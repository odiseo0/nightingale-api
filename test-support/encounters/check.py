import asyncio
import runpy
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid7

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]


async def check_encounters(runtime, administrative, client, tokens):
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.authorization.application.authorization_cases import identified_users
    from src.core import Ok
    from pydantic import SecretStr
    from src.settings.api_settings import api_settings

    api_settings.sync_signing_key = SecretStr("fixture-encounter-signing-key-2026")
    from src.core.db import DAOError

    owner, assistant, outsider = [await access.issue(client, token["access_token"]) for token in tokens]
    async with administrative() as db:
        identity = (await identified_users(db, [UUID(owner["userId"])]))[UUID(owner["userId"])]
    async with administrative() as db:
        created = await bootstrap_practice(db, BootstrapPracticeInput(
            owner_issuer=identity.oidc_issuer, owner_subject=identity.oidc_subject,
            owner_name="Fixture Owner", professional_name="Fixture Professional",
            display_name="Fixture Practice", time_zone="America/Caracas",
            location_name="Fixture Office", location_address="Fictional address",
            location_country="VE", location_state="Fixture State", location_city="Fixture City",
        ))
    assert isinstance(created, Ok)
    account_id = created.value.account_id
    professional_id = created.value.professional_id
    base = f"/v1/accounts/{account_id}"

    async def operation(action, key, payload, version=0, actor=owner, operation_id=None, local=None, status=200):
        envelope = {
            "operationId": str(operation_id or uuid7()), "contractVersion": 1,
            "action": action, "entityKey": str(key), "expectedVersion": version,
            "payload": payload,
        }
        if local is not None:
            envelope["occurredAtLocal"] = local
        response = await client.post(base + "/sync/operations", headers=access.authorization(actor), json={"operations": [envelope]})
        access.expect(response, status)
        return response.json()["results"][0] if status == 200 else response.json()

    async def get(path, actor=owner, status=200):
        response = await client.get(base + path, headers=access.authorization(actor))
        access.expect(response, status)
        return response.json()

    await operation("RegisterAccountDevice", owner["deviceId"], {})
    invitation = uuid7()
    await operation("CreateInvitation", invitation, {"inviteeUserId": assistant["userId"]})
    access.expect(await client.post(
        f"/v1/me/invitations/{invitation}/accept", headers=access.authorization(assistant),
        json={"operationId": str(uuid7())},
    ), 200)
    await operation("RegisterAccountDevice", assistant["deviceId"], {}, actor=assistant)
    patient = uuid7()
    await operation("RegisterPatient", patient, {
        "fullName": "Fixture Patient", "phoneCode": "+58", "phone": "4125550101",
        "identificationBasis": "own_document", "identifiers": [{
            "id": str(uuid7()), "issuingCountry": "VE", "documentType": "national_id",
            "documentNumber": "FIXTURE-E06",
        }],
    })
    await operation("SetPatientCompletion", patient, {"completionStatus": "complete"}, 1)
    service, rule, appointment = uuid7(), uuid7(), uuid7()
    await operation("CreateService", service, {"professionalId": str(professional_id), "name": "Fixture Service", "defaultDurationMinutes": 30})
    response = await client.post(base + "/sync/operations", headers=access.authorization(owner), json={"operations": [{
        "operationId": str(uuid7()), "contractVersion": 1, "action": "OfferService",
        "entityKey": {"professionalId": str(professional_id), "serviceId": str(service)},
        "expectedVersion": 0, "payload": {},
    }]})
    access.expect(response, 200)
    await operation("CreateScheduleRule", rule, {
        "professionalId": str(professional_id), "isoWeekday": 1,
        "localStartMinute": 480, "localEndMinute": 1020, "validFrom": "2026-10-26",
    })
    await operation("CreateAppointment", appointment, {
        "patientId": str(patient), "professionalId": str(professional_id),
        "serviceId": str(service), "startsAt": "2026-11-02T13:00:00Z",
        "endsAt": "2026-11-02T13:45:00Z",
    })

    assert (await get(f"/patients/{patient}/last-visit"))["encounterId"] is None
    first, second = uuid7(), uuid7()
    first_id = uuid7()
    created_first = await operation("CreatePatientEncounter", first, {
        "patientId": str(patient), "appointmentId": str(appointment),
        "attendingProfessionalId": str(professional_id), "reason": "PRIV-E06-MOTIVO",
        "occurredAt": "2026-11-02T13:05:00Z", "capturedAtLocal": "2026-11-02T13:06:00-04:00",
    }, actor=assistant, operation_id=first_id)
    assert created_first["status"] == "accepted" and created_first["entityVersion"] == 1, created_first
    duplicate = await operation("CreatePatientEncounter", first, {
        "patientId": str(patient), "appointmentId": str(appointment),
        "attendingProfessionalId": str(professional_id), "reason": "PRIV-E06-MOTIVO",
        "occurredAt": "2026-11-02T13:05:00Z", "capturedAtLocal": "2026-11-02T13:06:00-04:00",
    }, actor=assistant, operation_id=first_id)
    assert duplicate["status"] == "duplicate"
    await operation("CreatePatientEncounter", second, {
        "patientId": str(patient), "appointmentId": str(appointment),
        "attendingProfessionalId": str(professional_id),
        "occurredAt": "2026-11-02T14:00:00Z",
    }, actor=assistant)
    assert (await get(f"/patients/{patient}/encounters"))["total"] == 2
    assert (await get(f"/patients/{patient}/last-visit"))["encounterId"] == str(second)
    await operation("CompleteAppointment", appointment, {})
    assert (await get(f"/patients/{patient}/encounters"))["total"] == 2

    updates = await asyncio.gather(
        operation("UpdatePatientEncounter", second, {"assessment": "PRIV-E14-A"}, 1, actor=assistant),
        operation("UpdatePatientEncounter", second, {"assessment": "PRIV-E14-B"}, 1, actor=assistant),
    )
    assert sorted(item["status"] for item in updates) == ["accepted", "conflict"]
    history = (await get(f"/patients/{patient}/encounters/{second}/history"))["items"]
    assert len(history) == 2 and [row["version"] for row in history] == [1, 2]
    await operation("InvalidatePatientEncounter", second, {"correctionReason": "Fixture error"}, 2, actor=assistant)
    assert (await get(f"/patients/{patient}/last-visit"))["encounterId"] == str(first)
    assert (await get(f"/patients/{patient}/encounters"))["total"] == 1
    assert (await get(f"/patients/{patient}/encounters?recordStatus=entered-in-error"))["total"] == 1

    without_appointment = uuid7()
    offline = await operation("CreatePatientEncounter", without_appointment, {
        "patientId": str(patient), "attendingProfessionalId": str(professional_id),
        "reason": "PRIV-E11-OFFLINE",
    }, actor=assistant, local="2026-11-02T14:00:00-04:00")
    assert offline["state"]["occurredAt"] == "2026-11-02T18:00:00Z", offline
    assert offline["state"]["capturedAtLocal"] == "2026-11-02T18:00:00Z"
    future = await operation("CreatePatientEncounter", uuid7(), {
        "patientId": str(patient), "attendingProfessionalId": str(professional_id),
        "occurredAt": "2999-01-01T00:00:00Z",
    }, actor=assistant)
    assert future["status"] == "rejected" and future["error"]["code"] == "VALIDATION_ERROR"

    async with administrative() as db:
        timeline = (await db.execute(text("""
            SELECT entry_type,entity_version,record_status FROM nightingale.patient_clinical_timeline
            WHERE account_id=:account ORDER BY entry_id
        """), {"account": account_id})).all()
        assert len(timeline) == 3
        audit = await db.scalar(text("""
            SELECT count(*) FROM nightingale.audit_events
            WHERE account_id=:account AND (object_key::text LIKE '%PRIV-%' OR action LIKE '%PRIV-%')
        """), {"account": account_id})
        assert audit == 0

    snapshot = await client.post(base + "/sync/snapshots", headers=access.authorization(assistant), json={"includeClinical": True})
    access.expect(snapshot, 201)
    snapshot_body = snapshot.json()
    assert "encounters" in snapshot_body["clinicalSections"]
    items = (await get(f"/sync/snapshots/{snapshot_body['snapshotId']}/items?shows=500", actor=assistant))["items"]
    encounters = [item for item in items if item["entityType"] == "clinical_encounter"]
    assert {item["entityKey"] for item in encounters} == {str(first), str(without_appointment)}

    await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": {"encounters": "none"}}, 1)
    await get(f"/patients/{patient}/encounters", actor=assistant, status=403)
    await get(f"/patients/{patient}/last-visit", actor=assistant, status=403)
    await operation("CreatePatientEncounter", first, {
        "patientId": str(patient), "appointmentId": str(appointment),
        "attendingProfessionalId": str(professional_id), "reason": "PRIV-E06-MOTIVO",
        "occurredAt": "2026-11-02T13:05:00Z", "capturedAtLocal": "2026-11-02T13:06:00-04:00",
    }, actor=assistant, operation_id=first_id, status=403)

    retry = uuid7()
    retry_entity = uuid7()
    retry_payload = {
        "patientId": str(patient), "attendingProfessionalId": str(professional_id),
    }
    with patch("src.api.sync.application.operations_cases.apply_encounter_operation", side_effect=DAOError("Fixture rollback")):
        failed = await operation("CreatePatientEncounter", retry_entity, retry_payload, operation_id=retry)
    assert failed["status"] == "retryable_failure"
    recovered = await operation("CreatePatientEncounter", retry_entity, retry_payload, operation_id=retry)
    assert recovered["status"] == "accepted"

    print("Encounter checks passed: links, last visit, versions, invalidation, offline, permissions, sync and privacy.")


if __name__ == "__main__":
    asyncio.run(support["main"](check_encounters))
