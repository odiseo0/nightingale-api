import asyncio
from datetime import date, datetime
import runpy
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid7

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]


async def check_schedule(runtime, administrative, client, tokens):
    from src.api.accounts.application.accounts_cases import bootstrap_practice, get_account_context
    from src.api.accounts.application.management_cases import dao_professionals
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.authorization.application.authorization_cases import identified_users
    from src.api.schedule.application.schedule_cases import apply_rule_operation, weekly_day
    from src.api.schedule.domain.schedule import RequiredScheduleInterval, ScheduleRuleStatusPayload
    from src.api.sync.application.operations_cases import authorized_context
    from src.api.sync.repository.dao import dao_changes
    from src.core import Err, Ok
    from src.core.db import transaction

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
        return f"/v1/accounts/{result.value.account_id}", result.value.professional_id

    base, professional = await practice(owner)
    other_base, other_professional = await practice(outsider)
    account_id = UUID(base.rsplit("/",1)[1])
    def envelope(action, key, payload, version=0):
        return {"operationId": str(uuid7()), "contractVersion": 1, "action": action,
                "entityKey": str(key), "expectedVersion": version, "payload": payload}
    async def submit(operation, actor=owner, account=base, status=200):
        response = await client.post(account + "/sync/operations", headers=access.authorization(actor), json={"operations": [operation]})
        access.expect(response, status)
        return response.json()["results"][0] if status == 200 else response.json()
    async def get(path="", actor=owner, account=base, status=200):
        response = await client.get(account + "/schedule/rules" + path, headers=access.authorization(actor))
        access.expect(response, status)
        return response.json()
    async def counts():
        async with administrative() as db:
            return tuple((await db.execute(text("""
                SELECT (SELECT count(*) FROM nightingale.schedule_rules),
                    (SELECT count(*) FROM nightingale.operation_receipts),
                    (SELECT count(*) FROM nightingale.audit_events WHERE operation_id IS NOT NULL),
                    (SELECT count(*) FROM nightingale.change_log),sum(last_sequence),sum(permission_epoch)
                FROM nightingale.account_sync_heads
            """))).one())

    for actor, account in ((owner,base),(outsider,other_base)):
        await submit(envelope("RegisterAccountDevice", actor["deviceId"], {}), actor, account)
    invitation = uuid7()
    await submit(envelope("CreateInvitation", invitation, {"inviteeUserId": assistant["userId"]}))
    access.expect(await client.post(f"/v1/me/invitations/{invitation}/accept", headers=access.authorization(assistant), json={"operationId": str(uuid7())}), 200)
    await submit(envelope("RegisterAccountDevice", assistant["deviceId"], {}), assistant)

    morning, afternoon, overlap = uuid7(), uuid7(), uuid7()
    payload = {"professionalId": str(professional), "isoWeekday": 1, "localStartMinute": 480, "localEndMinute": 720, "validFrom": "2026-10-26"}
    first = envelope("CreateScheduleRule", morning, payload)
    before = await counts()
    results = await asyncio.gather(submit(first), submit(first))
    assert sorted(item["status"] for item in results) == ["accepted","duplicate"]
    assert tuple(a-b for a,b in zip(await counts(),before)) == (1,1,1,1,1,0)
    assert (await submit(dict(first,payload={**payload,"validUntil":None})))["status"] == "duplicate"
    assert (await submit(envelope("CreateScheduleRule", afternoon, {**payload,"localStartMinute":840,"localEndMinute":1440}), assistant))["status"] == "accepted"
    assert (await submit(envelope("CreateScheduleRule", overlap, {**payload,"localStartMinute":540,"localEndMinute":780,"validUntil":"2026-10-26"})))["status"] == "accepted"
    assert (await get("?shows=1",assistant))["total"] == 3
    assert len((await get("?page=2&shows=1"))["items"]) == 1
    assert (await get("?page=4&shows=1"))["items"] == []
    assert (await get("?fromDate=2026-11-02&untilDate=2026-11-02"))["total"] == 2
    assert (await get(f"?professionalId={other_professional}"))["total"] == 0
    await get("?other=1", status=422)
    await get(f"/{morning}?status=active", status=422)
    await get(f"/{morning}", outsider, other_base, status=404)
    await submit(envelope("UpdateScheduleRule",morning,{"localEndMinute":780},1),outsider,other_base,status=404)
    await submit(envelope("CreateScheduleRule",uuid7(),{**payload,"professionalId":str(other_professional)}),status=404)
    assert (await submit(envelope("CreateScheduleRule",uuid7(),payload)))["error"]["code"] == "INVALID_STATE_TRANSITION"
    for invalid in ({"localEndMinute":480},{"isoWeekday":True},{"validUntil":"2026-10-25"},{"localStartMinute":None}):
        assert (await submit(envelope("UpdateScheduleRule",morning,invalid,1)))["error"]["code"] == "VALIDATION_ERROR"

    async with runtime() as db, transaction(db):
        scope = await get_account_context(db, owner["accessToken"],account_id,True)
        day = await weekly_day(db,scope.value,professional,date(2026,10,26))
        assert [(i.local_start_minute,i.local_end_minute) for i in day.value.intervals] == [(480,780),(840,1440)]
        assert day.value.time_zone == "America/Caracas"
        local = await weekly_day(db,scope.value,professional,datetime.fromisoformat("2026-10-27T03:59:00Z"))
        assert local.value.local_date == date(2026,10,26) and local.value.intervals[-1].local_end_minute == 1440
        next_day = await weekly_day(db,scope.value,professional,datetime.fromisoformat("2026-10-27T04:00:00Z"))
        assert next_day.value.local_date == date(2026,10,27) and next_day.value.intervals == []
        ended = await weekly_day(db,scope.value,professional,date(2026,11,2))
        assert ended.value.intervals[0].local_end_minute == 720

    # Controlled required intervals test the rejection case, not real bookings.
    before = await counts()
    async with runtime() as db, transaction(db):
        scope = await authorized_context(db,owner["accessToken"],account_id,professional=True)
        assert isinstance(scope,Ok)
        effect = await apply_rule_operation(db,scope.value[0],"SetScheduleRuleStatus",afternoon,1,ScheduleRuleStatusPayload(status="inactive"),required_intervals=(RequiredScheduleInterval(local_date="2026-10-26",local_start_minute=900,local_end_minute=930),))
        assert isinstance(effect,Err) and effect.error.code == "SLOT_UNAVAILABLE"
    assert await counts() == before

    # Observe an actual PostgreSQL wait on the professional before the API edits.
    entered, released = asyncio.Event(), asyncio.Event()
    pid = {}
    original_lock = dao_professionals.lock_for_account
    async def observed_lock(db, account):
        pid["waiting"] = await db.scalar(text("SELECT pg_backend_pid()"))
        entered.set()
        return await original_lock(db, account)
    async with administrative() as blocker:
        async with blocker.begin():
            blocker_pid = await blocker.scalar(text("SELECT pg_backend_pid()"))
            await blocker.execute(text("SELECT id FROM nightingale.professionals WHERE id=:id FOR UPDATE"),{"id":professional})
            with patch.object(dao_professionals,"lock_for_account",side_effect=observed_lock):
                waiting = asyncio.create_task(submit(envelope("UpdateScheduleRule",morning,{"localEndMinute":750},1),assistant))
                try:
                    async with asyncio.timeout(5):
                        await entered.wait()
                        async with administrative() as observer:
                            while not await observer.scalar(text("SELECT :blocker = ANY(pg_blocking_pids(:waiting))"),{"blocker":blocker_pid,"waiting":pid["waiting"]}):
                                await asyncio.sleep(0.01)
                except BaseException:
                    waiting.cancel()
                    await asyncio.gather(waiting,return_exceptions=True)
                    raise
        assert (await waiting)["status"] == "accepted"
    assert (await submit(envelope("UpdateScheduleRule",morning,{"localEndMinute":760},1)))["error"]["code"] == "VERSION_CONFLICT"

    rollback = envelope("SetScheduleRuleStatus",afternoon,{"status":"inactive"},1)
    original_append = dao_changes.append
    async def incomplete(db,values,**kwargs):
        return await original_append(db,{**values,"group_size":values["group_size"]+1},**kwargs)
    before = await counts()
    with patch.object(dao_changes,"append",side_effect=incomplete):
        assert (await submit(rollback))["status"] == "retryable_failure"
    assert await counts() == before
    assert (await submit(rollback))["status"] == "accepted"
    assert (await get("?status=inactive"))["total"] == 1
    assert (await get())["total"] == 3

    try:
        async with administrative() as db, db.begin():
            await db.execute(text("""
                INSERT INTO nightingale.schedule_rules
                    (id,account_id,professional_id,iso_weekday,local_start_minute,local_end_minute,valid_from,valid_until,created_at,updated_at)
                SELECT :id,account_id,professional_id,iso_weekday,local_start_minute,local_end_minute,valid_from,valid_until,created_at,updated_at
                FROM nightingale.schedule_rules WHERE id=:source
            """),{"id":uuid7(),"source":morning})
    except DBAPIError as error:
        assert error.orig.sqlstate == "23505"
    else:
        raise AssertionError("NULLS NOT DISTINCT did not protect the open rule")

    competing = {**payload,"isoWeekday":2}
    results = await asyncio.gather(submit(envelope("CreateScheduleRule",uuid7(),competing)),submit(envelope("CreateScheduleRule",uuid7(),competing),assistant))
    assert sorted(item["status"] for item in results) == ["accepted","rejected"]
    assert next(item for item in results if item["status"] == "rejected")["error"]["code"] == "INVALID_STATE_TRANSITION"

    await submit(envelope("RevokeAccountDevice",assistant["deviceId"],{},1))
    await submit(first,assistant,status=403)
    await get(actor=assistant,status=403)


if __name__ == "__main__":
    asyncio.run(support["main"](check_schedule))
    print("Schedule: local split days, midnight end, open-rule uniqueness, versions, locking and rollback passed; no real appointments.")
