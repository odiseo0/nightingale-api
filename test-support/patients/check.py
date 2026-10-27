import asyncio
import json
from datetime import datetime
import runpy
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid7

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]


async def check_patients(runtime, administrative, client, tokens):
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.authorization.application.authorization_cases import identified_users
    from src.api.patients.repository.dao import dao_identifiers
    from src.api.sync.repository.dao import dao_changes
    from src.api.sync.infrastructure import operations_api
    from src.core import Ok

    owner, assistant, outsider = [await access.issue(client, token["access_token"]) for token in tokens]

    async def practice(actor):
        async with administrative() as db:
            users = await identified_users(db, [UUID(actor["userId"])])
            identity = users[UUID(actor["userId"])]
        async with administrative() as db:
            result = await bootstrap_practice(db, BootstrapPracticeInput(
                owner_issuer=identity.oidc_issuer, owner_subject=identity.oidc_subject,
                owner_name="Fixture Owner", professional_name="Fixture Professional",
                display_name="Fixture Practice", time_zone="America/Caracas", location_name="Fixture Office",
                location_address="Fictional address", location_country="VE", location_state="Fixture State", location_city="Fixture City",
            ))
        assert isinstance(result, Ok)
        return f"/v1/accounts/{result.value.account_id}"

    base = await practice(owner)
    other_base = await practice(outsider)

    def envelope(action, key, payload, version=0):
        return {"operationId": str(uuid7()), "contractVersion": 1, "action": action,
                "entityKey": key if isinstance(key, dict) else str(key), "expectedVersion": version, "payload": payload}

    async def submit(operation, actor=owner, account=base, status=200):
        response = await client.post(account + "/sync/operations", headers=access.authorization(actor), json={"operations": [operation]})
        access.expect(response, status)
        return response.json()["results"][0] if status == 200 else response.json()

    async def get(path, actor=owner, account=base, status=200):
        response = await client.get(account + path, headers=access.authorization(actor))
        access.expect(response, status)
        assert response.headers["Cache-Control"] == "no-store"
        return response.json()

    async def counts():
        async with administrative() as db:
            return tuple((await db.execute(text("""
                SELECT (SELECT count(*) FROM nightingale.patients),
                    (SELECT count(*) FROM nightingale.account_patients),
                    (SELECT count(*) FROM nightingale.patient_identifiers),
                    (SELECT count(*) FROM nightingale.operation_receipts),
                    (SELECT count(*) FROM nightingale.audit_events WHERE operation_id IS NOT NULL),
                    (SELECT count(*) FROM nightingale.change_log),
                    sum(last_sequence),sum(permission_epoch) FROM nightingale.account_sync_heads
            """))).one())

    for actor, account in ((owner, base), (outsider, other_base)):
        assert (await submit(envelope("RegisterAccountDevice", actor["deviceId"], {}), actor, account))["status"] == "accepted"
    invitation = uuid7()
    assert (await submit(envelope("CreateInvitation", invitation, {"inviteeUserId": assistant["userId"]})))["status"] == "accepted"
    access.expect(await client.post(f"/v1/me/invitations/{invitation}/accept", headers=access.authorization(assistant), json={"operationId": str(uuid7())}), 200)
    assert (await submit(envelope("RegisterAccountDevice", assistant["deviceId"], {}), assistant))["status"] == "accepted"

    patient = uuid7()
    document = {"id": str(uuid7()), "documentType": "national_id", "documentNumber": "FICT-000001"}
    register = envelope("RegisterPatient", patient, {"fullName": " Fixture Patient % ", "identifiers": [document]})
    before = await counts()
    concurrent = await asyncio.gather(submit(register), submit(register))
    assert sorted(item["status"] for item in concurrent) == ["accepted", "duplicate"]
    assert tuple(a-b for a,b in zip(await counts(), before)) == (1, 1, 1, 1, 1, 2, 1, 0)
    state = next(item["state"] for item in concurrent if item["status"] == "accepted")
    assert state["completionStatus"] == "draft" and state["fullName"] == "Fixture Patient %"
    assert state["createdAt"].endswith("Z") and "identifiers" not in state
    normalized = dict(register, payload={"fullName": "Fixture Patient %", "birthDate": None, "phoneCode": None, "phone": None, "identificationBasis": None, "identifiers": [{**document, "issuingCountry": "VE"}]})
    assert (await submit(normalized))["status"] == "duplicate"
    assert (await submit(dict(register, payload={"fullName": "Other"})))["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    listed = await get("/patients?shows=1&completionStatus=draft", assistant)
    assert listed["total"] == 1 and listed["items"][0]["patientId"] == str(patient)
    identifiers = await get(f"/patients/{patient}/identifiers?shows=1", assistant)
    assert identifiers["total"] == 1 and identifiers["items"][0]["verificationStatus"] == "declared"
    assert identifiers["items"][0]["documentNumber"] == document["documentNumber"]
    assert "verifiedByUserId" not in identifiers["items"][0]
    assert (await get("/patients?q=%25"))["total"] == 1
    assert (await get("/patients?q=FICT-000001"))["total"] == 1
    assert (await get("/patients?page=2&shows=1"))["items"] == []
    await get("/patients?unlisted=x", status=422)
    await get(f"/patients/{patient}?status=active", status=422)
    await get(f"/patients/{patient}", outsider, status=404)
    await get(f"/patients/{patient}/identifiers", outsider, other_base, status=404)
    assert (await get("/patients?q=FICT-000001", outsider, other_base))["total"] == 0
    before = await counts()
    collision = await submit(envelope("RegisterPatient", patient, {}), outsider, other_base)
    assert collision["error"]["code"] == "INVALID_STATE_TRANSITION" and collision["state"] is None
    assert collision["entityVersion"] is None
    assert (await counts())[0:3] == before[0:3]
    await submit(envelope("UpdatePatientProfile", patient, {"fullName": "Forbidden"}, 1), outsider, other_base, status=404)

    updates = await asyncio.gather(*[
        submit(envelope("UpdatePatientProfile", patient, {"fullName": name}, 1), actor)
        for name,actor in (("Fixture A", owner), ("Fixture B", assistant))
    ])
    assert sorted(item["status"] for item in updates) == ["accepted", "conflict"]
    assert next(item for item in updates if item["status"] == "conflict")["error"]["code"] == "VERSION_CONFLICT"
    assert (await get(f"/patients/{patient}"))["version"] == 2
    assert (await submit(envelope("UpdatePatientProfile", patient, {"fullName": None}, 2)))["entityVersion"] == 3
    assert (await submit(envelope("SetPatientProfileStatus", patient, {"status": "inactive"}, 3)))["entityVersion"] == 4
    assert (await get("/patients?status=active"))["total"] == 0
    assert (await get("/patients?status=inactive"))["total"] == 1
    assert (await get("/patients"))["total"] == 1

    for payload in ({"birthDate": "2999-01-01"}, {"phoneCode": "+58"}, {"fullName": " "}, {"identifiers": [{**document, "id": str(uuid7()), "verificationStatus": "verified"}]}):
        failed = await submit(envelope("RegisterPatient", uuid7(), payload))
        assert failed["error"]["code"] == "VALIDATION_ERROR"

    # The second document fails a real CHECK after identity, profile and the first
    # document exist in the transaction. None may survive the rollback.
    rollback = envelope("RegisterPatient", uuid7(), {"identifiers": [
        {**document, "id": str(uuid7())}, {**document, "id": str(uuid7())},
    ]})
    original_create = dao_identifiers.create
    attempts = 0

    async def fail_second(db, obj_in, **kwargs):
        nonlocal attempts
        attempts += 1
        return await original_create(db, obj_in={**obj_in, "document_number": ""} if attempts == 2 else obj_in, **kwargs)

    before = await counts()
    with patch.object(dao_identifiers, "create", side_effect=fail_second):
        assert (await submit(rollback))["status"] == "retryable_failure"
    assert await counts() == before
    assert (await submit(rollback))["status"] == "accepted"

    deferred = envelope("RegisterPatient", uuid7(), {})
    original_append = dao_changes.append

    async def incomplete_group(db, values, **kwargs):
        return await original_append(db, {**values, "group_size": values["group_size"]+1}, **kwargs)

    before = await counts()
    with patch.object(dao_changes, "append", side_effect=incomplete_group):
        assert (await submit(deferred))["status"] == "retryable_failure"
    assert await counts() == before
    assert (await submit(deferred))["status"] == "accepted"

    lost = envelope("RegisterPatient", uuid7(), {})
    original_submit = operations_api.submit_batch

    async def lose_response(*args, **kwargs):
        await original_submit(*args, **kwargs)
        raise ConnectionResetError("Fixture response dropped after commit")

    with patch.object(operations_api, "submit_batch", side_effect=lose_response):
        try:
            await submit(lost)
        except ConnectionResetError:
            pass
        else:
            raise AssertionError("Response was not lost")
    assert (await submit(lost))["status"] == "duplicate"

    # The same document text in two declared identities does not link them.
    assert (await submit(envelope("RegisterPatient", uuid7(), {"identifiers": [{**document, "id": str(uuid7())}]}), outsider, other_base))["status"] == "accepted"
    assert (await get("/patients?q=FICT-000001", outsider, other_base))["total"] == 1
    for factory, statement in (
        (runtime, "DELETE FROM nightingale.account_patients"),
        (administrative, "UPDATE nightingale.account_patients SET version=version+1,patient_id=uuidv7()"),
        (administrative, "UPDATE nightingale.patient_identifiers SET version=version+1,verification_status='invalidated',verified_at=clock_timestamp()"),
    ):
        try:
            async with factory() as db:
                async with db.begin():
                    await db.execute(text(statement))
        except DBAPIError:
            pass
        else:
            raise AssertionError("Patient integrity or privileges were bypassed")
    contact_id = uuid7()
    contact_op = envelope("CreateContactPerson", contact_id, {"fullName": "Fixture Parent", "phoneCode": "+58", "phone": "4120000000"})
    contact_result = await submit(contact_op, assistant)
    assert contact_result["status"] == "accepted", contact_result
    assert (await submit(contact_op, assistant))["status"] == "duplicate"
    sibling = uuid7()
    assert (await submit(envelope("RegisterPatient", sibling, {"fullName": "Fixture Sibling"})))["status"] == "accepted"
    assert (await submit(envelope("SetPatientProfileStatus", patient, {"status": "active"}, 4)))["status"] == "accepted"
    keys = [{"patientId": str(key), "contactPersonId": str(contact_id)} for key in (patient, sibling)]
    for key in keys:
        result = await submit(envelope("CreatePatientContactRelationship", key, {
            "relationshipKind": "mother", "isResponsibleContact": True, "validFrom": "2026-01-01T00:00:00Z",
        }), assistant)
        assert result["status"] == "accepted" and result["state"]["representationStatus"] == "unverified"
        assert result["state"]["verifiedAt"] is None and result["state"]["validFrom"].endswith("Z")
    assert (await get(f"/contacts/{contact_id}/patients?shows=1"))["total"] == 2
    assert len((await get(f"/contacts/{contact_id}/patients?shows=1&page=2"))["items"]) == 1
    assert (await get(f"/patients/{sibling}/contacts"))["items"][0]["contactFullName"] == "Fixture Parent"
    assert (await get("/contacts?q=Parent"))["total"] == 1
    await get(f"/contacts/{contact_id}", outsider, other_base, status=404)
    foreign_contact = uuid7()
    assert (await submit(envelope("CreateContactPerson", foreign_contact, {"fullName": "Other Fixture"}), outsider, other_base))["status"] == "accepted"
    await submit(envelope("CreatePatientContactRelationship", {"patientId": str(patient), "contactPersonId": str(foreign_contact)}, {
        "relationshipKind": "other", "validFrom": "2026-01-01T00:00:00Z",
    }), status=404)
    assert (await submit(envelope("UpdateContactPerson", contact_id, {"documentNumber": "INCOMPLETE"}, 1)))["error"]["code"] == "VALIDATION_ERROR"
    updated = await submit(envelope("UpdateContactPerson", contact_id, {"fullName": "Fixture Shared Parent"}, 1))
    assert updated["entityVersion"] == 2
    assert (await get(f"/patients/{sibling}/contacts"))["items"][0]["contactFullName"] == "Fixture Shared Parent"
    assert (await submit(envelope("SetContactPersonStatus", contact_id, {"status": "inactive"}, 2)))["entityVersion"] == 3
    assert (await get("/contacts?status=active"))["total"] == 0
    assert (await get(f"/contacts/{contact_id}/patients"))["total"] == 2
    assert (await submit(envelope("SetContactPersonStatus", contact_id, {"status": "active"}, 3)))["entityVersion"] == 4
    assert (await submit(envelope("UpdatePatientContactRelationship", keys[0], {"validUntil": "2026-02-01T00:00:00Z"}, 1)))["entityVersion"] == 2
    assert (await submit(envelope("SetPatientContactRelationshipStatus", keys[0], {"status": "inactive"}, 2)))["entityVersion"] == 3
    assert (await submit(envelope("SetPatientContactRelationshipStatus", keys[0], {"status": "active"}, 3)))["error"]["code"] == "INVALID_STATE_TRANSITION"
    assert (await submit(envelope("UpdatePatientContactRelationship", keys[0], {"validUntil": None}, 3)))["entityVersion"] == 4
    assert (await submit(envelope("SetPatientContactRelationshipStatus", keys[0], {"status": "active"}, 4)))["entityVersion"] == 5
    for statement, params in (
        ("""INSERT INTO nightingale.patient_contact_relationships
            (account_id,patient_id,contact_person_id,relationship_kind,valid_from,created_at,updated_at)
            SELECT account_id,patient_id,:foreign,'other',clock_timestamp(),clock_timestamp(),clock_timestamp()
            FROM nightingale.account_patients WHERE patient_id=:patient""", {"foreign": foreign_contact, "patient": patient}),
        ("""UPDATE nightingale.patient_contact_relationships SET representation_status='verified',
            verified_at=clock_timestamp(),verified_by_user_id=:foreign,updated_at=clock_timestamp(),version=version+1
            WHERE patient_id=:patient""", {"foreign": UUID(outsider["userId"]), "patient": patient}),
    ):
        try:
            async with administrative() as db:
                async with db.begin():
                    await db.execute(text(statement), params)
        except DBAPIError as error:
            assert error.orig.sqlstate == "23503"
        else:
            raise AssertionError("Cross-account contact or verifier bypassed the composite FK")
    async with administrative() as db:
        async with db.begin():
            await db.execute(text("""UPDATE nightingale.patient_contact_relationships SET representation_status='verified',
                verified_at=clock_timestamp(),verified_by_user_id=:owner,updated_at=clock_timestamp(),version=version+1
                WHERE patient_id=:patient"""), {"owner": UUID(owner["userId"]), "patient": patient})
    before_evidence = (await get(f"/patients/{patient}/contacts"))["items"][0]
    result = await submit(envelope("SetPatientContactRelationshipStatus", keys[0], {"status": "inactive"}, 6))
    assert result["status"] == "accepted" and result["state"]["verifiedAt"] == before_evidence["verifiedAt"]
    assert result["state"]["representationStatus"] == "verified"
    assert (await get(f"/patients/{patient}/contacts?status=active"))["total"] == 0
    adult = uuid7()
    assert (await submit(envelope("RegisterPatient", adult, {
        "fullName": "Fixture Adult", "phoneCode": "+58", "phone": "4120000000", "identificationBasis": "own_document",
    })))["status"] == "accepted"
    assert (await submit(envelope("SetPatientCompletion", adult, {"completionStatus": "complete"}, 1)))["error"]["code"] == "COMPLETENESS_CONFLICT"
    add = envelope("AddPatientIdentifier", uuid7(), {"patientId": str(adult), "documentType": "passport", "documentNumber": "FICT-000002"})
    concurrent = await asyncio.gather(submit(add), submit(add))
    assert sorted(item["status"] for item in concurrent) == ["accepted", "duplicate"]
    assert all(item["state"]["verificationStatus"] == "declared" for item in concurrent)
    completed = await submit(envelope("SetPatientCompletion", adult, {"completionStatus": "complete"}, 1))
    assert completed["status"] == "accepted" and completed["entityVersion"] == 2
    rejected = await submit(envelope("UpdatePatientProfile", adult, {"phoneCode": None, "phone": None}, 2))
    assert rejected["error"]["code"] == "COMPLETENESS_CONFLICT"
    assert (await get(f"/patients/{adult}"))["version"] == 2
    assert (await submit(envelope("UpdatePatientProfile", adult, {"fullName": "Fixture Adult Renamed"}, 2)))["entityVersion"] == 3
    await submit(envelope("AddPatientIdentifier", uuid7(), {"patientId": str(adult), "documentType": "passport", "documentNumber": "FOREIGN"}), outsider, other_base, status=404)

    child = uuid7()
    assert (await submit(envelope("RegisterPatient", child, {"fullName": "Fixture Minor", "birthDate": "2010-01-01", "identificationBasis": "minor_without_document"})))["status"] == "accepted"
    child_key = {"patientId": str(child), "contactPersonId": str(contact_id)}
    assert (await submit(envelope("CreatePatientContactRelationship", child_key, {
        "relationshipKind": "guardian", "isResponsibleContact": True, "validFrom": "2026-01-01T00:00:00Z",
    })))["status"] == "accepted"
    assert (await submit(envelope("SetPatientCompletion", child, {"completionStatus": "complete"}, 1)))["entityVersion"] == 2

    from src.api.patients.application.patients_cases import booking_patient
    from src.api.sync.application.operations_cases import authorized_context
    from src.core import Err

    async def eligible(patient_id, instant):
        async with runtime() as db:
            async with db.begin():
                scope = await authorized_context(db, owner["accessToken"], UUID(base.rsplit("/", 1)[1]))
                assert isinstance(scope, Ok)
                return await booking_patient(db, scope.value[0], patient_id, datetime.fromisoformat(instant))

    assert isinstance(await eligible(adult, "2028-01-01T13:00:00Z"), Ok)
    assert isinstance(await eligible(child, "2027-12-31T13:00:00Z"), Ok)
    assert isinstance(await eligible(child, "2028-01-01T03:59:00Z"), Ok)  # still December 31 in Caracas
    assert isinstance(await eligible(child, "2028-01-01T04:00:00Z"), Err)
    for action, key, payload, version in (
        ("SetContactPersonStatus", contact_id, {"status": "inactive"}, 4),
        ("UpdateContactPerson", contact_id, {"phoneCode": None, "phone": None}, 4),
        ("SetPatientContactRelationshipStatus", child_key, {"status": "inactive"}, 1),
        ("UpdatePatientContactRelationship", child_key, {"isResponsibleContact": False}, 1),
    ):
        assert (await submit(envelope(action, key, payload, version)))["error"]["code"] == "COMPLETENESS_CONFLICT"
    assert (await submit(envelope("UpdatePatientContactRelationship", child_key, {"validUntil": "2027-01-01T00:00:00Z"}, 1)))["status"] == "accepted"
    assert isinstance(await eligible(child, "2027-07-01T13:00:00Z"), Err)
    assert (await submit(envelope("UpdatePatientContactRelationship", child_key, {"validUntil": None}, 2)))["status"] == "accepted"

    # Real constraint at deferred commit, bypassing the application's precheck.
    try:
        async with administrative() as db:
            async with db.begin():
                await db.execute(text("UPDATE nightingale.contact_people SET phone_code=NULL,phone=NULL,version=version+1,updated_at=clock_timestamp() WHERE id=:id"), {"id": contact_id})
    except DBAPIError as error:
        assert error.orig.sqlstate == "23514"
    else:
        raise AssertionError("Removing the last required phone committed")
    assert (await get(f"/contacts/{contact_id}"))["version"] == 4

    second_contact = uuid7()
    assert (await submit(envelope("CreateContactPerson", second_contact, {"fullName": "Fixture Second Parent", "phoneCode": "+58", "phone": "4120000000"})))["status"] == "accepted"
    assert (await submit(envelope("CreatePatientContactRelationship", {"patientId": str(child), "contactPersonId": str(second_contact)}, {
        "relationshipKind": "father", "isResponsibleContact": True, "validFrom": "2026-01-01T00:00:00Z",
    })))["status"] == "accepted"
    gate = asyncio.Event()
    ready = 0
    pids = set()

    async def remove_phone(contact):
        nonlocal ready
        try:
            async with administrative() as db:
                async with db.begin():
                    pids.add(await db.scalar(text("SELECT pg_backend_pid()")))
                    await db.execute(text("UPDATE nightingale.contact_people SET phone_code=NULL,phone=NULL,version=version+1,updated_at=clock_timestamp() WHERE id=:id"), {"id": contact})
                    ready += 1
                    if ready == 2:
                        gate.set()
                    await asyncio.wait_for(gate.wait(), 5)
            return "committed"
        except DBAPIError as error:
            assert error.orig.sqlstate == "23514"
            return "rejected"

    race = await asyncio.gather(remove_phone(contact_id), remove_phone(second_contact))
    assert len(pids) == 2 and sorted(race) == ["committed", "rejected"]
    assert isinstance(await eligible(child, "2027-06-01T13:00:00Z"), Ok)

    # Add a declaration and change the identification basis without changing id.
    assert (await submit(envelope("AddPatientIdentifier", uuid7(), {"patientId": str(child), "documentType": "national_id", "documentNumber": "FICT-000003"})))["status"] == "accepted"
    changed = await submit(envelope("UpdatePatientProfile", child, {"identificationBasis": "own_document"}, 2))
    assert changed["status"] == "accepted" and changed["state"]["patientId"] == str(child)
    assert isinstance(await eligible(child, "2028-06-01T13:00:00Z"), Ok)
    assert (await submit(envelope("SetPatientCompletion", child, {"completionStatus": "draft"}, 3)))["entityVersion"] == 4
    for contact in (contact_id, second_contact):
        state = await get(f"/contacts/{contact}")
        assert (await submit(envelope("SetContactPersonStatus", contact, {"status": "inactive"}, state["version"])))["status"] == "accepted"
    assert (await get(f"/patients/{child}"))["completionStatus"] == "draft"
    try:
        async with administrative() as db:
            async with db.begin():
                await db.execute(text("UPDATE nightingale.patient_identifiers SET verification_status='invalidated',version=version+1,updated_at=clock_timestamp() WHERE id=:id"), {"id": UUID(add["entityKey"])})
    except DBAPIError as error:
        assert error.orig.sqlstate == "23514"
    else:
        raise AssertionError("Invalidating the only document left a complete profile")
    assert (await get(f"/patients/{adult}/identifiers"))["items"][0]["verificationStatus"] == "declared"

    # A committed receipt must still match the hash captured before T52.
    from src.api.patients.domain.patients import RegisterPatientPayload

    fixture = json.loads((ROOT / "tests/fixtures/operation_hashes.json").read_text(encoding="utf-8"))
    vector = next(item for item in fixture["cases"] if item["action"] == "RegisterPatient" and "birthDate" in item["payload"])
    previous_request = {**fixture["envelope"], **{name: value for name, value in vector.items() if name != "sha256"}}
    with patch.object(RegisterPatientPayload, "model_validate", wraps=RegisterPatientPayload.model_validate) as validate:
        previous = await submit(previous_request)
        assert previous["status"] == "accepted" and validate.call_count == 1
        async with administrative() as db:
            stored = (await db.execute(text("SELECT request_hash, result_json ? 'payload' AS input_saved FROM nightingale.operation_receipts WHERE account_id=:account AND actor_user_id=:actor AND operation_id=:operation"), {"account": UUID(base.rsplit("/", 1)[1]), "actor": UUID(owner["userId"]), "operation": UUID(previous_request["operationId"])})).one()
        assert bytes(stored.request_hash).hex() == vector["sha256"] and not stored.input_saved
        before = await counts()
        repeated = await submit({**previous_request, "payload": {**previous_request["payload"], "fullName": "Fixture", "identifiers": []}})
        assert repeated["status"] == "duplicate" and repeated["originalResult"] == previous
        assert validate.call_count == 2 and await counts() == before
        changed = await submit({**previous_request, "payload": {**previous_request["payload"], "fullName": "Different fixture"}})
        assert changed["error"]["code"] == "IDEMPOTENCY_CONFLICT" and await counts() == before

    missing = await client.get(base + "/patients")
    access.expect(missing, 401)
    unregistered = await access.issue(client, tokens[0]["access_token"])
    await get("/patients", unregistered, status=403)
    assert (await submit(envelope("SetAccountStatus", base.rsplit("/", 1)[1], {"status": "inactive"}, 1)))["status"] == "accepted"
    await get("/patients", status=403)
    await submit(add, status=403)
    assert (await submit(envelope("SetAccountStatus", base.rsplit("/", 1)[1], {"status": "active"}, 2)))["status"] == "accepted"
    assert (await submit(add))["status"] == "duplicate"
    assert (await get("/patients?q=%25"))["total"] == 0
    assert (await get("/patients?q=_"))["total"] == 0
    print("Patient checks passed: drafts, contacts, declared identification, dated minor eligibility, deferred completeness and concurrent dependency loss.")


if __name__ == "__main__":
    asyncio.run(support["main"](check_patients))
