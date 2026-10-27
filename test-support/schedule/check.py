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

    # A daily exception replaces all weekly intervals and retains its row on reopening.
    from src.api.schedule.application.exceptions_cases import daily_day

    exception = uuid7()
    closed = envelope("CreateScheduleException", exception, {
        "professionalId": str(professional), "localDate": "2026-10-26", "kind": "closed",
    })
    results = await asyncio.gather(submit(closed), submit(closed))
    assert sorted(item["status"] for item in results) == ["accepted", "duplicate"]
    async def daily():
        async with runtime() as db, transaction(db):
            scope = await get_account_context(db, owner["accessToken"], account_id, True)
            result = await daily_day(db, scope.value, professional, date(2026,10,26))
            assert isinstance(result, Ok)
            return [(i.local_start_minute,i.local_end_minute) for i in result.value.intervals]

    async def exceptions(path="", actor=owner, account=base, status=200):
        response = await client.get(account + "/schedule/exceptions" + path, headers=access.authorization(actor))
        access.expect(response, status)
        return response.json()

    assert await daily() == []
    assert (await submit({**closed,"payload":{**closed["payload"],"localStartMinute":None,"localEndMinute":None}}))["status"] == "duplicate"
    assert (await submit(envelope("CreateScheduleException",uuid7(),closed["payload"])))["error"]["code"] == "INVALID_STATE_TRANSITION"
    assert (await submit(envelope("UpdateScheduleException",exception,{"kind":"replacement"},1)))["error"]["code"] == "VALIDATION_ERROR"
    assert (await submit(envelope("UpdateScheduleException",exception,{"kind":"replacement","localStartMinute":960,"localEndMinute":1440},1),assistant))["status"] == "accepted"
    assert await daily() == [(960,1440)]
    assert (await submit(envelope("UpdateScheduleException",exception,{"kind":"closed"},2)))["error"]["code"] == "VALIDATION_ERROR"
    assert (await submit(envelope("UpdateScheduleException",exception,{"localStartMinute":None},2)))["error"]["code"] == "VALIDATION_ERROR"
    assert (await submit(envelope("SetScheduleExceptionStatus",exception,{"status":"inactive"},1)))["error"]["code"] == "VERSION_CONFLICT"
    query = "?fromDate=2026-10-26&untilDate=2026-10-26"
    assert (await exceptions(query,assistant))["total"] == 1
    assert (await exceptions(query+"&page=2&shows=1"))["items"] == []
    await exceptions(status=422)
    await exceptions("?fromDate=2026-01-01&untilDate=2027-01-02",status=422)
    await exceptions(f"/{exception}",outsider,other_base,status=404)
    await submit(envelope("UpdateScheduleException",exception,{"kind":"closed","localStartMinute":None,"localEndMinute":None},2),outsider,other_base,status=404)

    before = await counts()
    reopening = envelope("SetScheduleExceptionStatus",exception,{"status":"inactive"},2)
    with patch.object(dao_changes,"append",side_effect=incomplete):
        assert (await submit(reopening))["status"] == "retryable_failure"
    assert await counts() == before
    assert await daily() == [(960,1440)]
    assert (await submit(reopening,assistant))["status"] == "accepted"
    assert await daily() == [(480,780)]
    assert (await exceptions(f"/{exception}"))["status"] == "inactive"
    assert (await exceptions(query))["total"] == 1
    assert (await submit(envelope("CreateScheduleException",uuid7(),closed["payload"])))["error"]["code"] == "INVALID_STATE_TRANSITION"
    assert (await submit(envelope("SetScheduleExceptionStatus",exception,{"status":"active"},3)))["status"] == "accepted"
    assert (await submit(envelope("UpdateScheduleException",exception,{"kind":"closed","localStartMinute":None,"localEndMinute":None},4)))["status"] == "accepted"
    assert await daily() == []

    # SQL must enforce the conditional shape too, including NULL handling.
    for start, end in ((None,None),(0,None),(None,60),(60,60)):
        try:
            async with administrative() as db, db.begin():
                await db.execute(text("""
                    INSERT INTO nightingale.schedule_exceptions
                        (id,account_id,professional_id,local_date,kind,local_start_minute,local_end_minute,created_at,updated_at)
                    VALUES (:id,:account,:professional,'2026-10-28','replacement',:start,:end,now(),now())
                """),{"id":uuid7(),"account":account_id,"professional":professional,"start":start,"end":end})
        except DBAPIError as error:
            assert error.orig.sqlstate == "23514"
        else:
            raise AssertionError("SQL accepted an invalid replacement")

    competitors = {**closed["payload"],"localDate":"2026-10-29"}
    results = await asyncio.gather(submit(envelope("CreateScheduleException",uuid7(),competitors)),submit(envelope("CreateScheduleException",uuid7(),competitors),assistant))
    assert sorted(item["status"] for item in results) == ["accepted","rejected"]
    # Second account is a SQL fixture, not a new clinic management feature.
    second = uuid7()
    async with administrative() as db, db.begin():
        await db.execute(text("""
            INSERT INTO nightingale.accounts
                (id,kind,owner_user_id,display_name,time_zone,location_name,location_address,location_country,location_state,location_city,created_at,updated_at)
            SELECT :second,'clinic',:owner,'Fixture second account',time_zone,location_name,location_address,location_country,location_state,location_city,clock_timestamp(),clock_timestamp()
            FROM nightingale.accounts WHERE id=:source
        """), {"second":second,"owner":UUID(outsider["userId"]),"source":account_id})
        for actor in (owner,outsider):
            await db.execute(text("INSERT INTO nightingale.account_memberships(account_id,user_id,created_at,updated_at) VALUES (:account,:user,clock_timestamp(),clock_timestamp())"),{"account":second,"user":UUID(actor["userId"])})
        await db.execute(text("INSERT INTO nightingale.account_professionals(account_id,professional_id,user_id,created_at,updated_at) VALUES (:account,:professional,:user,clock_timestamp(),clock_timestamp())"),{"account":second,"professional":professional,"user":UUID(owner["userId"])})
        await db.execute(text("INSERT INTO nightingale.account_sync_heads(account_id,created_at,updated_at) VALUES (:account,clock_timestamp(),clock_timestamp())"),{"account":second})
    second_base = f"/v1/accounts/{second}"

    global_id, limited_id = uuid7(), uuid7()
    block_payload = {"professionalId":str(professional),"accountId":None,"startsAt":"2026-10-27T08:00:00-04:00","endsAt":"2026-10-27T10:00:00-04:00","reasonCode":"vacation"}
    global_op = envelope("CreateScheduleBlock",global_id,block_payload)
    await submit(global_op,assistant,status=404)
    results = await asyncio.gather(submit(global_op),submit(global_op))
    assert sorted(item["status"] for item in results) == ["accepted","duplicate"]
    assert (await submit({**global_op,"payload":{**block_payload,"startsAt":"2026-10-27T12:00:00Z","endsAt":"2026-10-27T14:00:00Z"}}))["status"] == "duplicate"
    assert (await submit(envelope("CreateScheduleBlock",limited_id,{**block_payload,"accountId":str(account_id),"reasonCode":"administrative"}),assistant))["status"] == "accepted"
    block_query = "?from=2026-10-27T12:30:00Z&until=2026-10-27T13:00:00Z"
    async def blocks(path=block_query, actor=owner, account=base, status=200):
        response = await client.get(account+"/schedule/blocks"+path,headers=access.authorization(actor))
        access.expect(response,status)
        return response.json()
    assert (await blocks())["total"] == 2
    assert (await blocks(block_query+"&page=3&shows=1"))["items"] == []
    assert (await blocks(f"/{global_id}",assistant))["reasonCode"] is None
    assert (await blocks(f"/{global_id}"))["reasonCode"] == "vacation"
    assert (await blocks(f"/{limited_id}",assistant))["reasonCode"] == "administrative"
    from src.api.schedule.repository.dao import dao_blocks
    from src.api.schedule.domain.schedule import ScheduleBlockQuery
    async with runtime() as db:
        rows, total = await dao_blocks.page(db, second, ScheduleBlockQuery.model_validate({
            "from":"2026-10-27T12:30:00Z","until":"2026-10-27T13:00:00Z",
        }))
        assert total == 1 and rows[0].id == global_id
    await blocks(actor=outsider,account=second_base,status=404)
    await blocks(f"/{limited_id}",outsider,second_base,status=404)
    await blocks(f"/{global_id}",outsider,other_base,status=404)
    await blocks("",status=422)
    await blocks("?from=2026-10-27T14:00:00Z&until=2026-10-27T14:00:00Z",status=422)
    assert (await blocks("?from=2026-10-27T14:00:00Z&until=2026-10-27T15:00:00Z"))["total"] == 0
    await submit(envelope("UpdateScheduleBlock",global_id,{"reasonCode":"unavailable"},1),assistant,status=404)
    for invalid in ({"endsAt":"2026-10-27T12:00:00Z"},{"startsAt":None},{"accountId":str(account_id)}):
        assert (await submit(envelope("UpdateScheduleBlock",global_id,invalid,1)))["error"]["code"] == "VALIDATION_ERROR"
    async with administrative() as db:
        projections = (await db.execute(text("SELECT account_id,projection_json FROM nightingale.change_log WHERE entity_type='schedule_block' AND entity_key=to_jsonb(CAST(:id AS text))"),{"id":str(global_id)})).all()
        assert {row.account_id for row in projections} == {account_id,second}
        assert all(row.projection_json["reasonCode"] is None for row in projections)

    changing = envelope("UpdateScheduleBlock",global_id,{"endsAt":"2026-10-27T15:00:00Z"},1)
    async def fail_second(db,values,**kwargs):
        if values["account_id"] == second:
            values = {**values,"group_size":values["group_size"]+1}
        return await original_append(db,values,**kwargs)
    before = await counts()
    with patch.object(dao_changes,"append",side_effect=fail_second):
        assert (await submit(changing))["status"] == "retryable_failure"
    assert await counts() == before
    assert (await blocks(f"/{global_id}"))["version"] == 1
    assert (await submit(changing))["status"] == "accepted"
    assert (await submit(envelope("SetScheduleBlockStatus",global_id,{"status":"inactive"},2)))["status"] == "accepted"
    assert (await blocks(f"/{global_id}"))["status"] == "inactive"
    assert (await blocks(block_query+"&status=active"))["total"] == 1
    # Controlled intervals prove the local guard only; T22 supplies real bookings.
    from src.api.schedule.application.blocks_cases import apply_block_operation
    from src.api.schedule.domain.schedule import AbsoluteInterval, CreateScheduleBlockPayload
    before = await counts()
    async with runtime() as db, transaction(db):
        scope = await authorized_context(db,owner["accessToken"],account_id,blocks=True)
        effect = await apply_block_operation(
            db,scope.value[0],"CreateScheduleBlock",uuid7(),0,
            CreateScheduleBlockPayload.model_validate(block_payload),
            required_intervals=(AbsoluteInterval(startsAt="2026-10-27T13:00:00Z",endsAt="2026-10-27T13:30:00Z"),),
        )
        assert isinstance(effect,Err) and effect.error.code == "SLOT_UNAVAILABLE"
    assert await counts() == before
    service_id = uuid7()
    assert (await submit(envelope("CreateService",service_id,{"professionalId":str(professional),"name":"Fixture service","defaultDurationMinutes":30})))["status"] == "accepted"
    offer = {"professionalId":str(professional),"serviceId":str(service_id)}
    offer_op = {**envelope("OfferService",service_id,{}),"entityKey":offer}
    assert (await submit(offer_op))["status"] == "accepted"
    async def availability(start="2026-10-27T04:00:00Z",end="2026-10-28T04:00:00Z",duration=None,actor=owner,status=200):
        params = {"professionalId":str(professional),"serviceId":str(service_id),"from":start,"until":end}
        if duration is not None:
            params["durationMinutes"] = str(duration)
        response = await client.get(base+"/availability",params=params,headers=access.authorization(actor))
        access.expect(response,status)
        return response.json()
    before = await counts()
    value = await availability(actor=assistant)
    assert value["referenceDurationMinutes"] == value["requestedDurationMinutes"] == 30
    assert value["availableIntervals"] == [{"startsAt":"2026-10-27T14:00:00Z","endsAt":"2026-10-27T16:00:00Z"}]
    assert (await availability(duration=121))["availableIntervals"] == []
    assert (await availability(duration=45))["requestedDurationMinutes"] == 45
    assert await counts() == before
    assert (await submit(envelope("SetScheduleBlockStatus",global_id,{"status":"active"},3)))["status"] == "accepted"
    assert (await availability())["availableIntervals"] == [{"startsAt":"2026-10-27T15:00:00Z","endsAt":"2026-10-27T16:00:00Z"}]
    assert (await availability("2026-10-26T04:00:00Z","2026-10-27T04:00:00Z"))["availableIntervals"] == []
    await availability(duration=0,status=422)
    await availability("2026-10-01T00:00:00Z","2026-11-01T00:01:00Z",status=422)
    await availability(actor=outsider,status=404)

    assert (await submit(envelope("UpdateAccountDetails",account_id,{"timeZone":"America/New_York"},1)))["status"] == "accepted"
    assert (await submit(envelope("CreateScheduleRule",uuid7(),{**payload,"isoWeekday":7,"localStartMinute":60,"localEndMinute":120})))["status"] == "accepted"
    await availability("2026-11-01T04:00:00Z","2026-11-02T05:00:00Z",status=422)
    assert (await submit(envelope("CreateScheduleException",uuid7(),{"professionalId":str(professional),"localDate":"2026-11-01","kind":"replacement","localStartMinute":0,"localEndMinute":1440})))["status"] == "accepted"
    assert (await availability("2026-11-01T04:00:00Z","2026-11-02T05:00:00Z"))["availableIntervals"] == [{"startsAt":"2026-11-01T04:00:00Z","endsAt":"2026-11-02T05:00:00Z"}]
    assert (await submit(envelope("CreateScheduleException",uuid7(),{"professionalId":str(professional),"localDate":"2027-03-14","kind":"replacement","localStartMinute":150,"localEndMinute":240})))["status"] == "accepted"
    await availability("2027-03-14T05:00:00Z","2027-03-15T04:00:00Z",status=422)
    await submit(envelope("RevokeAccountDevice",assistant["deviceId"],{},1))
    await availability(actor=assistant,status=403)
    await blocks(actor=assistant,status=403)
    await exceptions(query,assistant,status=403)
    await submit(closed,assistant,status=403)
    await submit(first,assistant,status=403)
    await get(actor=assistant,status=403)


if __name__ == "__main__":
    asyncio.run(support["main"](check_schedule))
    print("Schedule: local split days, midnight end, open-rule uniqueness, versions, locking and rollback passed; no real appointments.")
