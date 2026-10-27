import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import runpy
from unittest.mock import patch
from uuid import UUID, uuid7

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]


async def check_appointments(runtime, administrative, client, tokens):
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.authorization.application.authorization_cases import identified_users
    from src.api.appointments.repository.dao import dao_histories
    from src.core import Ok

    owner, assistant, outsider = [await access.issue(client, token["access_token"]) for token in tokens]

    async def practice(actor):
        async with administrative() as db:
            identity = (await identified_users(db,[UUID(actor["userId"])]))[UUID(actor["userId"])]
        async with administrative() as db:
            result = await bootstrap_practice(db,BootstrapPracticeInput(
                owner_issuer=identity.oidc_issuer,owner_subject=identity.oidc_subject,
                owner_name="Fixture Owner",professional_name="Fixture Professional",display_name="Fixture Practice",
                time_zone="America/Caracas",location_name="Fixture Office",location_address="Fictional address",
                location_country="VE",location_state="Fixture State",location_city="Fixture City",
            ))
        assert isinstance(result,Ok)
        return f"/v1/accounts/{result.value.account_id}",result.value.professional_id

    base, professional = await practice(owner)
    other_base, other_professional = await practice(outsider)
    account_id = UUID(base.rsplit("/",1)[1])
    def envelope(action,key,payload,version=0):
        return {"operationId":str(uuid7()),"contractVersion":1,"action":action,"entityKey":str(key),"expectedVersion":version,"payload":payload}
    async def submit(operation,actor=owner,account=base,status=200):
        response = await client.post(account+"/sync/operations",headers=access.authorization(actor),json={"operations":[operation]})
        access.expect(response,status)
        return response.json()["results"][0] if status == 200 else response.json()
    async def get(path,actor=owner,account=base,status=200):
        response = await client.get(account+path,headers=access.authorization(actor))
        access.expect(response,status)
        return response.json()
    async def counts():
        async with administrative() as db:
            return tuple((await db.execute(text("""
                SELECT (SELECT count(*) FROM nightingale.appointments),
                    (SELECT count(*) FROM nightingale.appointment_histories),
                    (SELECT count(*) FROM nightingale.operation_receipts),
                    (SELECT count(*) FROM nightingale.audit_events WHERE operation_id IS NOT NULL),
                    (SELECT count(*) FROM nightingale.change_log),sum(last_sequence),sum(permission_epoch)
                FROM nightingale.account_sync_heads
            """))).one())

    for actor,account in ((owner,base),(outsider,other_base)):
        await submit(envelope("RegisterAccountDevice",actor["deviceId"],{}),actor,account)
    invitation = uuid7()
    await submit(envelope("CreateInvitation",invitation,{"inviteeUserId":assistant["userId"]}))
    access.expect(await client.post(f"/v1/me/invitations/{invitation}/accept",headers=access.authorization(assistant),json={"operationId":str(uuid7())}),200)
    await submit(envelope("RegisterAccountDevice",assistant["deviceId"],{}),assistant)
    patient, service, rule = uuid7(),uuid7(),uuid7()
    assert (await submit(envelope("RegisterPatient",patient,{
        "fullName":"Fixture Patient","phoneCode":"+58","phone":"4125550101","identificationBasis":"own_document",
        "identifiers":[{"id":str(uuid7()),"issuingCountry":"VE","documentType":"national_id","documentNumber":"FIXTURE-001"}],
    })))["status"] == "accepted"
    assert (await submit(envelope("SetPatientCompletion",patient,{"completionStatus":"complete"},1)))["status"] == "accepted"
    assert (await submit(envelope("CreateService",service,{"professionalId":str(professional),"name":"Fixture Service","defaultDurationMinutes":30})))["status"] == "accepted"
    offer = {**envelope("OfferService",service,{}),"entityKey":{"professionalId":str(professional),"serviceId":str(service)}}
    assert (await submit(offer))["status"] == "accepted"
    assert (await submit(envelope("CreateScheduleRule",rule,{"professionalId":str(professional),"isoWeekday":1,"localStartMinute":480,"localEndMinute":1020,"validFrom":"2026-10-26"})))["status"] == "accepted"

    appointment = uuid7()
    payload = {"patientId":str(patient),"professionalId":str(professional),"serviceId":str(service),"startsAt":"2026-11-02T13:00:00Z","endsAt":"2026-11-02T13:45:00Z"}
    first = envelope("CreateAppointment",appointment,payload)
    before = await counts()
    results = await asyncio.gather(submit(first),submit(first))
    assert sorted(item["status"] for item in results) == ["accepted","duplicate"]
    assert tuple(a-b for a,b in zip(await counts(),before)) == (1,1,1,1,1,1,0)
    state = next(item["state"] for item in results if item["status"] == "accepted")
    assert state["offeredDurationMinutesSnapshot"] == 30 and state["status"] == "scheduled"
    assert state["confirmedAt"] is None and state["version"] == 1
    assert state["timeZoneSnapshot"] == "America/Caracas"
    history = (await get(f"/appointments/{appointment}/history"))["items"]
    assert len(history) == 1 and history[0]["action"] == "created" and history[0]["actorUserId"] == owner["userId"]
    assert history[0]["changedAt"] == state["createdAt"] == state["updatedAt"]
    assert (await get("/appointments?from=2026-11-02T13:10:00Z&until=2026-11-02T13:20:00Z"))["total"] == 1
    assert (await get("/appointments?from=2026-11-02T12:00:00Z&until=2026-11-02T16:00:00Z&page=2&shows=1"))["items"] == []
    await get(f"/appointments/{appointment}",outsider,other_base,status=404)
    await submit(envelope("CreateAppointment",uuid7(),payload),outsider,other_base,status=404)
    conflict = await submit(envelope("CreateAppointment",uuid7(),payload),assistant)
    assert conflict["status"] == "conflict" and conflict["error"]["code"] == "SLOT_UNAVAILABLE"
    adjacent = envelope("CreateAppointment",uuid7(),{**payload,"startsAt":"2026-11-02T13:45:00Z","endsAt":"2026-11-02T14:15:00Z"})
    assert (await submit(adjacent,assistant))["status"] == "accepted"
    free = await get(f"/availability?professionalId={professional}&serviceId={service}&from=2026-11-02T12:00:00Z&until=2026-11-02T16:00:00Z",assistant)
    assert free["availableIntervals"] == [{"startsAt":"2026-11-02T12:00:00Z","endsAt":"2026-11-02T13:00:00Z"},{"startsAt":"2026-11-02T14:15:00Z","endsAt":"2026-11-02T16:00:00Z"}]
    assert set(free) == {"accountId","professionalId","serviceId","referenceDurationMinutes","requestedDurationMinutes","availableIntervals"}
    offer_key = offer["entityKey"]
    inactive_offer = {**envelope("SetServiceOfferStatus",service,{"status":"inactive"},1),"entityKey":offer_key}
    assert (await submit(inactive_offer))["status"] == "accepted"
    unavailable_offer = await submit(envelope("CreateAppointment",uuid7(),{**payload,"startsAt":"2026-11-02T20:00:00Z","endsAt":"2026-11-02T20:30:00Z"}))
    assert unavailable_offer["error"]["code"] == "INVALID_STATE_TRANSITION"
    assert (await submit({**envelope("SetServiceOfferStatus",service,{"status":"active"},2),"entityKey":offer_key}))["status"] == "accepted"

    # A missing first history must roll back even when the failure occurs at commit.
    retry = envelope("CreateAppointment",uuid7(),{**payload,"startsAt":"2026-11-02T16:00:00Z","endsAt":"2026-11-02T16:30:00Z"})
    before = await counts()
    with patch.object(dao_histories,"append",return_value=None):
        assert (await submit(retry))["status"] == "retryable_failure"
    assert await counts() == before
    assert (await submit(retry))["status"] == "accepted"

    # The savepoint reverts an incompatible proposal but preserves its rejection receipt.
    for operation in (
        envelope("UpdateScheduleRule",rule,{"localEndMinute":540},1),
        envelope("CreateScheduleException",uuid7(),{"professionalId":str(professional),"localDate":"2026-11-02","kind":"closed"}),
        envelope("CreateScheduleBlock",uuid7(),{"professionalId":str(professional),"accountId":None,"startsAt":"2026-11-02T13:00:00Z","endsAt":"2026-11-02T14:00:00Z","reasonCode":"vacation"}),
        envelope("UpdateAccountDetails",account_id,{"timeZone":"Asia/Tokyo"},1),
    ):
        before = await counts()
        result = await submit(operation)
        assert result["status"] == "conflict" and result["error"]["code"] == "SLOT_UNAVAILABLE", result
        assert tuple(a-b for a,b in zip(await counts(),before)) == (0,0,1,1,0,0,0)
        assert (await submit(operation))["status"] == "duplicate"
    assert (await get(f"/schedule/rules/{rule}"))["localEndMinute"] == 1020
    assert (await get(""))["timeZone"] == "America/Caracas"
    async with administrative() as db:
        assert await db.scalar(text("SELECT count(*) FROM nightingale.schedule_exceptions")) == 0
        assert await db.scalar(text("SELECT count(*) FROM nightingale.schedule_blocks")) == 0

    competing = {**payload,"startsAt":"2026-11-02T15:00:00Z","endsAt":"2026-11-02T15:30:00Z"}
    results = await asyncio.gather(submit(envelope("CreateAppointment",uuid7(),competing)),submit(envelope("CreateAppointment",uuid7(),competing),assistant))
    assert sorted(item["status"] for item in results) == ["accepted","conflict"]

    # Both requests wait on the same actual professional row before they compete.
    from src.api.accounts.repository.dao import dao_professionals
    entered = asyncio.Event()
    waiting_pids = []
    original_lock = dao_professionals.lock_for_account
    async def observed_lock(db,account):
        waiting_pids.append(await db.scalar(text("SELECT pg_backend_pid()")))
        if len(waiting_pids) == 2:
            entered.set()
        return await original_lock(db,account)
    race_payload = {**payload,"startsAt":"2026-11-02T17:00:00Z","endsAt":"2026-11-02T17:30:00Z"}
    block = {"professionalId":str(professional),"accountId":str(account_id),"startsAt":race_payload["startsAt"],"endsAt":race_payload["endsAt"],"reasonCode":"administrative"}
    async with administrative() as blocker:
        async with blocker.begin():
            blocker_pid = await blocker.scalar(text("SELECT pg_backend_pid()"))
            await blocker.execute(text("SELECT id FROM nightingale.professionals WHERE id=:id FOR UPDATE"),{"id":professional})
            with patch.object(dao_professionals,"lock_for_account",side_effect=observed_lock):
                booking = asyncio.create_task(submit(envelope("CreateAppointment",uuid7(),race_payload)))
                blocking = asyncio.create_task(submit(envelope("CreateScheduleBlock",uuid7(),block),assistant))
                try:
                    async with asyncio.timeout(5):
                        await entered.wait()
                        async with administrative() as observer:
                            # PostgreSQL can queue one waiter behind the other.
                            while not all([await observer.scalar(text("SELECT cardinality(pg_blocking_pids(:waiting))>0"),{"waiting":pid}) for pid in waiting_pids]):
                                await asyncio.sleep(0.01)
                            assert any([await observer.scalar(text("SELECT :holder = ANY(pg_blocking_pids(:waiting))"),{"holder":blocker_pid,"waiting":pid}) for pid in waiting_pids])
                except BaseException:
                    booking.cancel()
                    blocking.cancel()
                    await asyncio.gather(booking,blocking,return_exceptions=True)
                    raise
        results = await asyncio.gather(booking,blocking)
    assert sorted(item["status"] for item in results) == ["accepted","conflict"]

    # A second account is a SQL fixture only. Its real reservation must occupy
    # the same professional globally without enabling clinic HTTP management.
    second = uuid7()
    async with administrative() as db, db.begin():
        await db.execute(text("""
            INSERT INTO nightingale.accounts
                (id,kind,owner_user_id,display_name,time_zone,location_name,location_address,location_country,location_state,location_city,created_at,updated_at)
            SELECT :second,'clinic',:owner,'Fixture second account',time_zone,location_name,location_address,location_country,location_state,location_city,created_at,updated_at
            FROM nightingale.accounts WHERE id=:source
        """),{"second":second,"owner":UUID(outsider["userId"]),"source":account_id})
        for actor in (owner,outsider):
            await db.execute(text("INSERT INTO nightingale.account_memberships(account_id,user_id,created_at,updated_at) VALUES (:account,:user,clock_timestamp(),clock_timestamp())"),{"account":second,"user":UUID(actor["userId"])})
        await db.execute(text("INSERT INTO nightingale.account_professionals(account_id,professional_id,user_id,created_at,updated_at) VALUES (:account,:professional,:user,clock_timestamp(),clock_timestamp())"),{"account":second,"professional":professional,"user":UUID(owner["userId"])})
        await db.execute(text("INSERT INTO nightingale.account_sync_heads(account_id,created_at,updated_at) VALUES (:account,clock_timestamp(),clock_timestamp())"),{"account":second})
        await db.execute(text("""
            INSERT INTO nightingale.account_patients
                (account_id,patient_id,full_name,birth_date,phone_code,phone,identification_basis,completion_status,status,created_at,updated_at,version)
            SELECT :second,patient_id,'Other account fixture',birth_date,phone_code,phone,identification_basis,completion_status,status,created_at,updated_at,version
            FROM nightingale.account_patients WHERE account_id=:source AND patient_id=:patient
        """),{"second":second,"source":account_id,"patient":patient})
        await db.execute(text("""
            INSERT INTO nightingale.professional_services(account_id,professional_id,service_id,duration_minutes_override,status,created_at,updated_at,version)
            SELECT :second,professional_id,service_id,duration_minutes_override,status,created_at,updated_at,version
            FROM nightingale.professional_services WHERE account_id=:source AND service_id=:service
        """),{"second":second,"source":account_id,"service":service})

    from src.api.appointments.domain.appointments import AppointmentHistoryQuery, AppointmentHistoryResponse
    from src.api.appointments.repository.dao import dao_appointments
    from src.api.appointments.application.appointments_cases import appointment_response
    from src.core.db import DAOIntegrityError, transaction
    foreign_id = uuid7()
    async with administrative() as db:
        row = await dao_appointments.get(db,appointment)
        template = appointment_response(row)
        first_history = (await dao_histories.page(db,account_id,appointment,AppointmentHistoryQuery()))[0][0]
        history_template = AppointmentHistoryResponse.model_validate(first_history).model_dump()
    values = {**template,"id":foreign_id,"account_id":second,"starts_at":datetime.fromisoformat("2026-11-02T18:00:00Z"),"ends_at":datetime.fromisoformat("2026-11-02T18:30:00Z")}
    history_values = {**history_template,"appointment_id":foreign_id,"account_id":second,"starts_at":values["starts_at"],"ends_at":values["ends_at"]}
    entered = asyncio.Event()
    second_pid = {}
    async def conflicting_writer():
        try:
            async with runtime() as db, transaction(db):
                second_pid["pid"] = await db.scalar(text("SELECT pg_backend_pid()"))
                entered.set()
                await dao_appointments.create(db,obj_in={**values,"id":uuid7(),"account_id":account_id},commit=False)
        except DAOIntegrityError as error:
            assert error.__cause__.orig.sqlstate == "23P01"
            return "excluded"
        raise AssertionError("Global exclusion accepted a concurrent overlap")
    async with runtime() as first_db, transaction(first_db):
        first_pid = await first_db.scalar(text("SELECT pg_backend_pid()"))
        await dao_appointments.create(first_db,obj_in=values,commit=False)
        waiting = asyncio.create_task(conflicting_writer())
        try:
            async with asyncio.timeout(5):
                await entered.wait()
                async with administrative() as observer:
                    while not await observer.scalar(text("SELECT :holder = ANY(pg_blocking_pids(:waiting))"),{"holder":first_pid,"waiting":second_pid["pid"]}):
                        await asyncio.sleep(0.01)
            await dao_histories.append(first_db,history_values)
        except BaseException:
            waiting.cancel()
            await asyncio.gather(waiting,return_exceptions=True)
            raise
    assert await waiting == "excluded"
    global_free = await get(f"/availability?professionalId={professional}&serviceId={service}&from=2026-11-02T18:00:00Z&until=2026-11-02T19:00:00Z")
    assert global_free["availableIntervals"] == [{"startsAt":"2026-11-02T18:30:00Z","endsAt":"2026-11-02T19:00:00Z"}]
    await get(f"/appointments/{foreign_id}",status=404)
    # Eligibility is checked at the proposed date, not only at completion time.
    assert (await submit(envelope("SetPatientCompletion",patient,{"completionStatus":"draft"},2)))["status"] == "accepted"
    ineligible = await submit(envelope("CreateAppointment",uuid7(),{**payload,"startsAt":"2026-11-02T20:00:00Z","endsAt":"2026-11-02T20:30:00Z"}))
    assert ineligible["error"]["code"] == "COMPLETENESS_CONFLICT"
    assert (await submit(envelope("SetPatientCompletion",patient,{"completionStatus":"complete"},3)))["status"] == "accepted"
    minor, contact = uuid7(),uuid7()
    assert (await submit(envelope("RegisterPatient",minor,{"fullName":"Fixture Minor","birthDate":"2015-01-01","identificationBasis":"minor_without_document"})))["status"] == "accepted"
    assert (await submit(envelope("CreateContactPerson",contact,{"fullName":"Fixture Responsible","phoneCode":"+58","phone":"4125550102"})))["status"] == "accepted"
    relationship = {**envelope("CreatePatientContactRelationship",contact,{"relationshipKind":"guardian","isResponsibleContact":True,"validFrom":"2026-01-01T00:00:00Z","validUntil":"2027-01-01T00:00:00Z"}),"entityKey":{"patientId":str(minor),"contactPersonId":str(contact)}}
    assert (await submit(relationship))["status"] == "accepted"
    assert (await submit(envelope("SetPatientCompletion",minor,{"completionStatus":"complete"},1)))["status"] == "accepted"
    minor_payload = {**payload,"patientId":str(minor),"startsAt":"2026-11-02T20:00:00Z","endsAt":"2026-11-02T20:30:00Z"}
    assert (await submit(envelope("CreateAppointment",uuid7(),minor_payload)))["error"]["code"] == "COMPLETENESS_CONFLICT"
    await submit(envelope("CreateAppointment",uuid7(),{**minor_payload,"responsibleContactId":str(uuid7())}),status=404)
    minor_appointment = await submit(envelope("CreateAppointment",uuid7(),{**minor_payload,"responsibleContactId":str(contact)}))
    assert minor_appointment["status"] == "accepted" and minor_appointment["state"]["responsibleContactId"] == str(contact)
    special = uuid7()
    assert (await submit(envelope("CreateScheduleException",special,{"professionalId":str(professional),"localDate":"2026-11-09","kind":"replacement","localStartMinute":1080,"localEndMinute":1140})))["status"] == "accepted"
    assert (await submit(envelope("CreateAppointment",uuid7(),{**payload,"startsAt":"2026-11-09T22:00:00Z","endsAt":"2026-11-09T22:30:00Z"})))["status"] == "accepted"
    for action,change in (("SetScheduleExceptionStatus",{"status":"inactive"}),("UpdateScheduleException",{"localDate":"2026-11-10"})):
        assert (await submit(envelope(action,special,change,1)))["error"]["code"] == "SLOT_UNAVAILABLE"
    assert (await get(f"/schedule/exceptions/{special}"))["status"] == "active"
    confirmation = envelope("ConfirmAppointment",appointment,{},1)
    before = await counts()
    results = await asyncio.gather(submit(confirmation),submit(confirmation))
    assert sorted(item["status"] for item in results) == ["accepted","duplicate"]
    assert tuple(a-b for a,b in zip(await counts(),before)) == (0,1,1,1,1,1,0)
    confirmed = next(item["state"] for item in results if item["status"] == "accepted")
    assert confirmed["startsAt"] == state["startsAt"] and confirmed["endsAt"] == state["endsAt"]
    assert confirmed["status"] == "confirmed" and confirmed["version"] == 2
    assert confirmed["confirmedAt"] == confirmed["updatedAt"] and confirmed["createdAt"] == state["createdAt"]
    assert (await submit(envelope("ConfirmAppointment",appointment,{},1)))["error"]["code"] == "VERSION_CONFLICT"
    assert (await submit(envelope("ConfirmAppointment",appointment,{},2)))["error"]["code"] == "INVALID_STATE_TRANSITION"
    assert (await submit(envelope("ConfirmAppointment",appointment,{"confirmedAt":"2026-10-27T00:00:00Z"},2)))["error"]["code"] == "VALIDATION_ERROR"
    await submit(envelope("ConfirmAppointment",appointment,{},2),outsider,other_base,status=404)
    assert (await get(f"/appointments/{appointment}/history"))["total"] == 2
    assert (await get(f"/appointments/{appointment}/history?afterVersion=1"))["items"][0]["action"] == "confirmed"
    assert (await submit(first))["state"]["status"] == "scheduled"
    assert (await submit(envelope("UpdateService",service,{"name":"Renamed Fixture Service","defaultDurationMinutes":20},1)))["status"] == "accepted"
    wrong_duration = await submit(envelope("RescheduleAppointment",appointment,{"startsAt":"2026-11-02T12:00:00Z","endsAt":"2026-11-02T12:30:00Z"},2))
    assert wrong_duration["error"]["code"] == "VALIDATION_ERROR"
    overlap = await submit(envelope("RescheduleAppointment",appointment,{"startsAt":"2026-11-02T13:30:00Z","endsAt":"2026-11-02T14:15:00Z"},2))
    assert overlap["error"]["code"] == "SLOT_UNAVAILABLE"
    assert (await get(f"/appointments/{appointment}"))["confirmedAt"] == confirmed["confirmedAt"]
    move = envelope("RescheduleAppointment",appointment,{"startsAt":"2026-11-02T12:45:00Z","endsAt":"2026-11-02T13:30:00Z"},2)
    before = await counts()
    with patch.object(dao_histories,"append",return_value=None):
        assert (await submit(move))["status"] == "retryable_failure"
    assert await counts() == before
    assert (await get(f"/appointments/{appointment}"))["version"] == 2
    moved = await submit(move,assistant)
    assert moved["status"] == "accepted" and moved["state"]["version"] == 3
    assert moved["state"]["status"] == "scheduled" and moved["state"]["confirmedAt"] is None
    assert moved["state"]["id"] == str(appointment)
    for name in state:
        if name.endswith("Snapshot"):
            assert moved["state"][name] == state[name]
    assert (await submit(move,assistant))["status"] == "duplicate"
    assert (await submit(envelope("RescheduleAppointment",appointment,move["payload"],3)))["error"]["code"] == "NO_CHANGES"
    histories = (await get(f"/appointments/{appointment}/history"))["items"]
    assert [item["version"] for item in histories] == [1,2,3]
    assert histories[-1]["action"] == "rescheduled" and histories[-1]["confirmedAt"] is None
    reconfirmed = await submit(envelope("ConfirmAppointment",appointment,{},3))
    assert reconfirmed["status"] == "accepted" and reconfirmed["state"]["version"] == 4
    cancel = envelope("CancelAppointment",appointment,{"changeReason":"Fixture administrative cancellation"},4)
    before = await counts()
    cancelled = await submit(cancel,assistant)
    assert cancelled["status"] == "accepted" and cancelled["state"]["version"] == 5
    assert cancelled["state"]["status"] == "cancelled"
    assert cancelled["state"]["confirmedAt"] == reconfirmed["state"]["confirmedAt"]
    assert cancelled["state"]["startsAt"] == moved["state"]["startsAt"]
    assert tuple(a-b for a,b in zip(await counts(),before)) == (0,1,1,1,1,1,0)
    assert (await submit(cancel,assistant))["status"] == "duplicate"
    assert (await submit(envelope("CancelAppointment",appointment,{},5)))["error"]["code"] == "INVALID_STATE_TRANSITION"
    assert (await submit(envelope("ConfirmAppointment",appointment,{},5)))["error"]["code"] == "INVALID_STATE_TRANSITION"
    released = await get(f"/availability?professionalId={professional}&serviceId={service}&from=2026-11-02T12:45:00Z&until=2026-11-02T13:30:00Z")
    assert released["availableIntervals"] == [{"startsAt":"2026-11-02T12:45:00Z","endsAt":"2026-11-02T13:30:00Z"}]
    replacement = await submit(envelope("CreateAppointment",uuid7(),{**payload,**move["payload"]}))
    assert replacement["status"] == "accepted"
    assert replacement["state"]["offeredDurationMinutesSnapshot"] == 20
    assert (await get(f"/appointments/{appointment}/history"))["total"] == 5
    replacement_id = UUID(replacement["state"]["id"])
    assert (await submit(envelope("CompleteAppointment",replacement_id,{},1)))["error"]["code"] == "INVALID_STATE_TRANSITION"
    with patch.object(dao_appointments,"server_time",return_value=datetime.fromisoformat(move["payload"]["startsAt"])):
        completed = await submit(envelope("CompleteAppointment",replacement_id,{"changeReason":"Fixture attendance"},1),assistant)
    assert completed["status"] == "accepted" and completed["state"]["status"] == "completed"
    assert completed["state"]["startsAt"] == replacement["state"]["startsAt"]
    assert (await submit(envelope("CreateAppointment",uuid7(),{**payload,**move["payload"]})))["error"]["code"] == "SLOT_UNAVAILABLE"
    assert (await submit(envelope("ConfirmAppointment",replacement_id,{},2)))["error"]["code"] == "INVALID_STATE_TRANSITION"
    adjacent_id = UUID(adjacent["entityKey"])
    with patch.object(dao_appointments,"server_time",return_value=datetime.fromisoformat("2026-11-02T13:59:59.999999Z")):
        assert (await submit(envelope("MarkAppointmentNoShow",adjacent_id,{},1)))["error"]["code"] == "INVALID_STATE_TRANSITION"
    assert (await submit(envelope("UpdateAccountPolicy",account_id,{"noShowGraceMinutes":30},1)))["status"] == "accepted"
    with patch.object(dao_appointments,"server_time",return_value=datetime.fromisoformat("2026-11-02T14:00:00Z")):
        assert (await submit(envelope("MarkAppointmentNoShow",adjacent_id,{},1)))["error"]["code"] == "INVALID_STATE_TRANSITION"
    absence = envelope("MarkAppointmentNoShow",adjacent_id,{"changeReason":"Fixture absence"},1)
    with patch.object(dao_appointments,"server_time",return_value=datetime.fromisoformat("2026-11-02T14:15:00Z")):
        absent = await submit(absence,assistant)
    assert absent["status"] == "accepted" and absent["state"]["status"] == "no_show"
    assert (await submit(absence,assistant))["status"] == "duplicate"
    assert (await submit(envelope("CancelAppointment",adjacent_id,{},2)))["error"]["code"] == "INVALID_STATE_TRANSITION"
    assert (await submit(envelope("CreateAppointment",uuid7(),{**payload,"startsAt":"2026-11-02T13:45:00Z","endsAt":"2026-11-02T14:15:00Z"})))["error"]["code"] == "SLOT_UNAVAILABLE"
    # History constraints must reject invalid SQL, not only API payloads.
    from src.core.db import DAOError
    probe_id = UUID(retry["entityKey"])
    async with administrative() as db:
        row = await dao_appointments.get(db,probe_id)
        probe_state = appointment_response(row)
        probe_history = (await dao_histories.page(db,account_id,probe_id,AppointmentHistoryQuery()))[0][0]
        probe_history_values = AppointmentHistoryResponse.model_validate(probe_history).model_dump()
    async def invalid_sql(kind,session_factory=runtime):
        before = await counts()
        try:
            async with session_factory() as db, transaction(db):
                if kind in ("update","delete"):
                    statement = "UPDATE nightingale.appointment_histories SET change_reason='Forbidden' WHERE appointment_id=:id" if kind == "update" else "DELETE FROM nightingale.appointment_histories WHERE appointment_id=:id"
                    await db.execute(text(statement),{"id":probe_id})
                elif kind == "skip_parent":
                    await db.execute(text("UPDATE nightingale.appointments SET version=version+2 WHERE id=:id"),{"id":probe_id})
                elif kind == "future":
                    await dao_histories.append(db,{**probe_history_values,"version":3})
                else:
                    now = await dao_appointments.server_time(db)
                    changes = {"status":"confirmed","confirmed_at":now}
                    if kind == "change_both_snapshots":
                        changes["service_name_snapshot"] = "Changed agreed value"
                    current = await dao_appointments.get(db,probe_id)
                    await dao_appointments.revise(db,current,changes,now)
                    values = {**probe_history_values,"version":2,"action":"confirmed","status":"confirmed","confirmed_at":now,"changed_at":now}
                    if kind in ("mismatch","change_both_snapshots"):
                        values["service_name_snapshot"] = "Changed agreed value"
                    if kind == "gap":
                        values["version"] = 3
                    if kind == "bad_action":
                        values["action"] = "created"
                    await dao_histories.append(db,values)
        except (DAOError,DBAPIError) as error:
            db_error = error if isinstance(error,DBAPIError) else error.__cause__
            assert db_error.orig.sqlstate in ("23503","23514","42501"),kind
        else:
            raise AssertionError(f"Invalid history SQL committed: {kind}")
        assert await counts() == before
        assert (await get(f"/appointments/{probe_id}"))["version"] == 1
    for kind in ("update","delete","skip_parent","future","mismatch","change_both_snapshots","gap","bad_action"):
        await invalid_sql(kind)
    await invalid_sql("update",administrative)
    await invalid_sql("delete",administrative)
    async with administrative() as db:
        rows = (await db.execute(text("SELECT appointment_id,version FROM nightingale.appointment_histories ORDER BY appointment_id,version"))).all()
        for history_row in rows:
            await db.execute(text("SELECT nightingale.validate_appointment_history(:id,:version)"),{"id":history_row.appointment_id,"version":history_row.version})
    await submit(envelope("RevokeAccountDevice",assistant["deviceId"],{},1))
    await get(f"/appointments/{appointment}",assistant,status=403)
    await submit(first,assistant,status=403)


if __name__ == "__main__":
    asyncio.run(support["main"](check_appointments))
    print("Appointments: creation, confirmation, rescheduling, terminal states, global races, immutable history and atomic rollback passed.")
