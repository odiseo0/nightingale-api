import asyncio
import runpy
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid7

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]


async def check_services(runtime, administrative, client, tokens):
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.authorization.application.authorization_cases import identified_users
    from src.api.services.repository.dao import dao_offers, dao_services
    from src.api.services.application.offers_cases import booking_service
    from src.api.accounts.application.accounts_cases import get_account_context
    from src.core.db import transaction
    from src.api.sync.repository.dao import dao_changes
    from src.core import Ok

    owner, assistant, outsider = [await access.issue(client, token["access_token"]) for token in tokens]

    async def practice(actor):
        async with administrative() as db:
            identity = (await identified_users(db, [UUID(actor["userId"])]))[UUID(actor["userId"])]
        async with administrative() as db:
            result = await bootstrap_practice(db, BootstrapPracticeInput(
                owner_issuer=identity.oidc_issuer, owner_subject=identity.oidc_subject,
                owner_name="Fixture Owner", professional_name="Fixture Professional",
                display_name="Fixture Practice", time_zone="America/Caracas", location_name="Fixture Office",
                location_address="Fictional address", location_country="VE", location_state="Fixture State", location_city="Fixture City",
            ))
        assert isinstance(result, Ok)
        return f"/v1/accounts/{result.value.account_id}", str(result.value.professional_id)

    base, professional = await practice(owner)
    other_base, other_professional = await practice(outsider)

    def envelope(action, key, payload, version=0):
        return {"operationId": str(uuid7()), "contractVersion": 1, "action": action,
                "entityKey": key if isinstance(key, dict) else str(key), "expectedVersion": version, "payload": payload}

    async def submit(operation, actor=owner, account=base, status=200):
        response = await client.post(account + "/sync/operations", headers=access.authorization(actor), json={"operations": [operation]})
        access.expect(response, status)
        return response.json()["results"][0] if status == 200 else response.json()

    async def get(path="/v1/me/services", actor=owner, status=200):
        response = await client.get(path, headers=access.authorization(actor))
        access.expect(response, status)
        assert response.headers["Cache-Control"] == "no-store"
        return response.json()

    async def counts():
        async with administrative() as db:
            return tuple((await db.execute(text("""
                SELECT (SELECT count(*) FROM nightingale.services),
                    (SELECT count(*) FROM nightingale.operation_receipts),
                    (SELECT count(*) FROM nightingale.audit_events WHERE operation_id IS NOT NULL),
                    (SELECT count(*) FROM nightingale.change_log),sum(last_sequence),sum(permission_epoch)
                FROM nightingale.account_sync_heads
            """))).one())

    for actor, account in ((owner, base), (outsider, other_base)):
        assert (await submit(envelope("RegisterAccountDevice", actor["deviceId"], {}), actor, account))["status"] == "accepted"
    invitation = uuid7()
    await submit(envelope("CreateInvitation", invitation, {"inviteeUserId": assistant["userId"]}))
    access.expect(await client.post(f"/v1/me/invitations/{invitation}/accept", headers=access.authorization(assistant), json={"operationId": str(uuid7())}), 200)
    await submit(envelope("RegisterAccountDevice", assistant["deviceId"], {}), assistant)

    service = uuid7()
    create = envelope("CreateService", service, {"professionalId": professional, "name": " Fixture % ", "defaultDurationMinutes": 30})
    before = await counts()
    results = await asyncio.gather(submit(create), submit(create))
    assert sorted(item["status"] for item in results) == ["accepted", "duplicate"]
    assert tuple(a-b for a,b in zip(await counts(), before)) == (1,1,1,1,1,0)
    state = next(item["state"] for item in results if item["status"] == "accepted")
    assert state["name"] == "Fixture %" and state["version"] == 1 and state["status"] == "active"
    assert state["createdAt"].endswith("Z")
    assert (await submit(dict(create, payload={**create["payload"], "name": "Fixture %"})))["status"] == "duplicate"
    assert (await submit(dict(create, payload={**create["payload"], "name": "Other"})))["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    assert (await get("/v1/me/services?q=%25&shows=1"))["total"] == 1
    assert (await get("/v1/me/services?page=2&shows=1"))["items"] == []
    assert (await get(actor=outsider))["total"] == 0
    await get(actor=assistant, status=404)
    await get("/v1/me/services?other=1", status=422)
    await submit(create, assistant, status=403)
    await submit(envelope("CreateService", uuid7(), {**create["payload"], "professionalId": other_professional}), status=404)
    await submit(envelope("UpdateService", service, {"name": "Forbidden"}, 1), outsider, other_base, status=404)

    results = await asyncio.gather(*[submit(envelope("UpdateService", service, {"defaultDurationMinutes": value}, 1)) for value in (1,1440)])
    assert sorted(item["status"] for item in results) == ["accepted", "conflict"]
    assert (await submit(envelope("UpdateService", service, {"name": "Updated"}, 1)))["error"]["code"] == "VERSION_CONFLICT"
    assert (await submit(envelope("SetServiceStatus", service, {"status": "inactive"}, 2)))["entityVersion"] == 3
    assert (await get("/v1/me/services?status=active"))["total"] == 0
    assert (await get())["total"] == 1
    assert (await submit(envelope("SetServiceStatus", service, {"status": "inactive"}, 3)))["error"]["code"] == "NO_CHANGES"
    for value in (0,1441,True,1.5,"30"):
        assert (await submit(envelope("CreateService", uuid7(), {**create["payload"], "defaultDurationMinutes": value})))["error"]["code"] == "VALIDATION_ERROR"

    rollback = envelope("CreateService", uuid7(), create["payload"])
    before = await counts()
    original_append = dao_changes.append

    async def incomplete_group(db, values, **kwargs):
        return await original_append(db, {**values, "group_size": values["group_size"]+1}, **kwargs)

    with patch.object(dao_changes, "append", side_effect=incomplete_group):
        assert (await submit(rollback))["status"] == "retryable_failure"
    assert await counts() == before
    assert (await submit(rollback))["status"] == "accepted"
    async with administrative() as db:
        assert await db.scalar(text("SELECT count(*) FROM nightingale.change_log WHERE entity_type='service' AND audience<>'owner'")) == 0
    for statement in (
        "UPDATE nightingale.services SET professional_id=:professional,version=version+1 WHERE id=:id",
        "UPDATE nightingale.services SET version=version WHERE id=:id",
        "UPDATE nightingale.services SET default_duration_minutes=0,version=version+1 WHERE id=:id",
    ):
        try:
            async with administrative() as db, db.begin():
                await db.execute(text(statement), {"id": service, "professional": UUID(other_professional)})
        except DBAPIError:
            pass
        else:
            raise AssertionError("Invalid service record was committed")

    offered = uuid7()
    assert (await submit(envelope("CreateService", offered, {**create["payload"], "name": "Offered"})))["status"] == "accepted"
    key = {"professionalId": professional, "serviceId": str(offered)}
    offer = envelope("OfferService", key, {})
    results = await asyncio.gather(submit(offer), submit(offer))
    assert sorted(item["status"] for item in results) == ["accepted", "duplicate"]
    assert (await submit(dict(offer, payload={"durationMinutesOverride": None})))["status"] == "duplicate"
    listed = await get(base + "/services?shows=1", assistant)
    assert listed["total"] == 1 and listed["items"][0]["serviceId"] == str(offered)
    assert listed["items"][0]["effectiveDurationMinutes"] == 30
    assert listed["items"][0]["durationMinutesOverride"] is None
    assert (await get(base + "/services?page=2&shows=1"))["items"] == []
    assert (await get(base + f"/services?professionalId={other_professional}"))["total"] == 0
    await get(base + "/services?other=1", status=422)
    await get(base + "/services", outsider, status=404)
    await submit(envelope("UpdateServiceOffer", key, {"durationMinutesOverride": 40}, 1), assistant, status=403)
    await submit(envelope("OfferService", {**key, "professionalId": other_professional}, {}), status=404)
    foreign = uuid7()
    await submit(envelope("CreateService", foreign, {**create["payload"], "professionalId": other_professional}), outsider, other_base)
    await submit(envelope("OfferService", {**key, "serviceId": str(foreign)}, {}), status=404)
    assert (await submit(envelope("UpdateServiceOffer", key, {"durationMinutesOverride": 45}, 1)))["state"]["effectiveDurationMinutes"] == 45
    assert (await submit(envelope("UpdateServiceOffer", key, {"durationMinutesOverride": None}, 2)))["state"]["effectiveDurationMinutes"] == 30

    # The stage exposes one independent practice per owner. A second account is
    # a schema fixture only; it does not enable HTTP clinic management.
    second = uuid7()
    async with administrative() as db, db.begin():
        await db.execute(text("""
            INSERT INTO nightingale.accounts
                (id,kind,owner_user_id,display_name,time_zone,location_name,location_address,location_country,location_state,location_city,created_at,updated_at)
            SELECT :second,'clinic',:owner,'Fixture second account',time_zone,location_name,location_address,location_country,location_state,location_city,clock_timestamp(),clock_timestamp()
            FROM nightingale.accounts WHERE id=:source
        """), {"second": second, "owner": UUID(outsider["userId"]), "source": UUID(base.rsplit("/",1)[1])})
        for member in (owner, outsider):
            await db.execute(text("INSERT INTO nightingale.account_memberships(account_id,user_id,created_at,updated_at) VALUES (:account,:user,clock_timestamp(),clock_timestamp())"), {"account": second, "user": UUID(member["userId"])})
        await db.execute(text("INSERT INTO nightingale.account_professionals(account_id,professional_id,user_id,created_at,updated_at) VALUES (:account,:professional,:user,clock_timestamp(),clock_timestamp())"), {"account": second, "professional": UUID(professional), "user": UUID(owner["userId"])})
        await db.execute(text("INSERT INTO nightingale.account_sync_heads(account_id,created_at,updated_at) VALUES (:account,clock_timestamp(),clock_timestamp())"), {"account": second})
    async with runtime() as db, transaction(db):
        now = await dao_services.server_time(db)
        await dao_offers.create_offer(db, {"account_id": second, "professional_id": UUID(professional), "service_id": offered, "duration_minutes_override": 45, "created_at": now, "updated_at": now}, commit=False)

    assert (await submit(envelope("UpdateService", offered, {"defaultDurationMinutes": 20}, 1)))["status"] == "accepted"
    assert (await get(base + "/services", assistant))["items"][0]["effectiveDurationMinutes"] == 20
    async with administrative() as db:
        row = (await db.execute(text("SELECT projection_json,audience FROM nightingale.change_log WHERE account_id=:account ORDER BY sequence DESC LIMIT 1"), {"account": second})).one()
        assert row.projection_json["effectiveDurationMinutes"] == 45 and row.audience == "members"
        assert row.projection_json["serviceVersion"] == 2 and row.projection_json["version"] == 1
        assert await db.scalar(text("SELECT count(*) FROM nightingale.change_log WHERE account_id=:account AND entity_type='service'"), {"account": second}) == 0

    # A failure in a second account rolls back catalog, both journals and receipt.
    failed_update = envelope("UpdateService", offered, {"name": "Retry after rollback"}, 2)
    before = await counts()
    async def fail_second_account(db, values, **kwargs):
        if values["account_id"] == second:
            values = {**values, "group_size": values["group_size"]+1}
        return await original_append(db, values, **kwargs)
    with patch.object(dao_changes, "append", side_effect=fail_second_account):
        assert (await submit(failed_update))["status"] == "retryable_failure"
    assert await counts() == before
    assert (await get(base + "/services"))["items"][0]["name"] == "Offered"

    # An invalid dict in the second journal must also roll back the first one.
    from src.api.services.application import services_cases
    original_projection = services_cases.offer_response
    def invalid_second_projection(row, service_row):
        value = original_projection(row, service_row)
        if row.account_id == second:
            del value["service_version"]
        return value
    with patch.object(services_cases, "offer_response", side_effect=invalid_second_projection):
        assert (await submit(failed_update))["status"] == "retryable_failure"
    assert await counts() == before
    assert (await get(base + "/services"))["items"][0]["name"] == "Offered"
    assert (await submit(failed_update))["status"] == "accepted"

    async with runtime() as db, transaction(db):
        context = await get_account_context(db, owner["accessToken"], UUID(base.rsplit("/",1)[1]), True)
        assert isinstance(context, Ok)
        reference = await booking_service(db, context.value, UUID(professional), offered)
        assert isinstance(reference, Ok) and reference.value.effective_duration_minutes == 20
    assert (await submit(envelope("SetServiceOfferStatus", key, {"status": "inactive"}, 3)))["status"] == "accepted"
    async with administrative() as db:
        assert await db.scalar(text("SELECT status FROM nightingale.professional_services WHERE account_id=:account"), {"account": second}) == "active"
    assert (await get(base + "/services?status=active"))["total"] == 0
    assert (await get(base + "/services"))["total"] == 1
    async with runtime() as db, transaction(db):
        context = await get_account_context(db, owner["accessToken"], UUID(base.rsplit("/",1)[1]), True)
        assert not isinstance(await booking_service(db, context.value, UUID(professional), offered), Ok)

    assert (await submit(envelope("SetServiceOfferStatus", key, {"status": "active"}, 4)))["status"] == "accepted"
    assert (await submit(envelope("SetServiceStatus", offered, {"status": "inactive"}, 3)))["status"] == "accepted"
    async with runtime() as db, transaction(db):
        context = await get_account_context(db, owner["accessToken"], UUID(base.rsplit("/",1)[1]), True)
        assert not isinstance(await booking_service(db, context.value, UUID(professional), offered), Ok)
    assert (await get(base + "/services"))["items"][0]["status"] == "active"
    assert (await get(base + "/services"))["items"][0]["serviceStatus"] == "inactive"

    # The composite FK must reject a service owned by another professional.
    try:
        async with runtime() as db, transaction(db):
            now = await dao_services.server_time(db)
            await dao_offers.create_offer(db, {"account_id": UUID(base.rsplit("/",1)[1]), "professional_id": UUID(professional), "service_id": foreign, "duration_minutes_override": None, "created_at": now, "updated_at": now}, commit=False)
    except Exception as error:
        from src.core.db import DAOError
        assert isinstance(error, DAOError)
    else:
        raise AssertionError("A foreign service bypassed the composite FK")

    # Even a saved result requires the professional's current account link.
    async with administrative() as db, db.begin():
        await db.execute(text("UPDATE nightingale.account_professionals SET status='inactive',version=version+1,updated_at=clock_timestamp() WHERE account_id=:account"), {"account":UUID(base.rsplit("/",1)[1])})
    await submit(create,status=403)
    await get(base + "/sync/operations/" + create["operationId"],status=403)
    async with administrative() as db, db.begin():
        await db.execute(text("UPDATE nightingale.account_professionals SET status='active',version=version+1,updated_at=clock_timestamp() WHERE account_id=:account"), {"account":UUID(base.rsplit("/",1)[1])})

    # Reauthorization occurs before returning the original catalog result.
    await submit(envelope("SetAccountStatus", base.rsplit("/",1)[1], {"status": "inactive"}, 1))
    await submit(create, status=403)


if __name__ == "__main__":
    asyncio.run(support["main"](check_services))
    print("Services: ownership, duration, versions, private projection, duplicates and atomic rollback passed.")
