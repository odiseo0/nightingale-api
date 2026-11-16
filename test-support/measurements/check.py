import asyncio
import runpy
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid7

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]


async def check_measurements(runtime, administrative, client, tokens):
    from pydantic import SecretStr
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.authorization.application.authorization_cases import identified_users
    from src.core import Ok
    from src.core.db import DAOError
    from src.settings.api_settings import api_settings

    api_settings.sync_signing_key = SecretStr("fixture-measurement-signing-key-2026")
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
        envelope = {"operationId": str(operation_id or uuid7()), "contractVersion": 1,
            "action": action, "entityKey": str(key), "expectedVersion": version, "payload": payload}
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
    access.expect(await client.post(f"/v1/me/invitations/{invitation}/accept", headers=access.authorization(assistant), json={"operationId": str(uuid7())}), 200)
    await operation("RegisterAccountDevice", assistant["deviceId"], {}, actor=assistant)
    patient = uuid7()
    await operation("RegisterPatient", patient, {"fullName": "Fixture Patient", "birthDate": "2000-02-29"})

    first, second, historical, pressure = uuid7(), uuid7(), uuid7(), uuid7()
    first_result = await operation("RecordPatientMeasurement", first, {
        "patientId": str(patient), "kind": "weight", "value": 700, "unit": "kg",
        "measuredAt": "2026-11-01T10:00:00Z",
    }, actor=assistant)
    assert first_result["status"] == "accepted" and first_result["state"]["value"] == 700, first_result
    corrected = await operation("CorrectPatientMeasurement", first, {
        "value": 70, "correctionReason": "PRIV-E09-CORRECCION",
    }, 1, actor=assistant)
    assert corrected["entityVersion"] == 2 and corrected["state"]["value"] == 70
    assert corrected["state"]["ageYears"] == 26 and corrected["state"]["ageAsOf"] == "2026-11-01"
    await operation("RecordPatientMeasurement", second, {
        "patientId": str(patient), "kind": "weight", "value": 69, "unit": "kg",
        "measuredAt": "2026-11-08T10:00:00Z",
    }, actor=assistant)
    await operation("RecordPatientMeasurement", historical, {
        "patientId": str(patient), "kind": "weight", "value": 68, "unit": "kg",
    }, actor=assistant, local="2026-11-03T06:00:00-04:00")
    page = await get(f"/patients/{patient}/measurements?kind=weight")
    assert page["total"] == 3
    assert [item["measurementId"] for item in page["items"]] == [str(first), str(historical), str(second)]
    summary = await get(f"/patients/{patient}/measurements/summary")
    assert next(item for item in summary["items"] if item["kind"] == "weight")["measurementId"] == str(second)
    history = (await get(f"/patients/{patient}/measurements/{first}/history"))["items"]
    assert len(history) == 2 and history[0]["value"] == 700 and history[1]["value"] == 70

    pressure_result = await operation("RecordPatientMeasurement", pressure, {
        "patientId": str(patient), "kind": "blood_pressure", "systolicValue": 120,
        "diastolicValue": None, "unit": "mm[Hg]",
    }, actor=assistant)
    assert pressure_result["status"] == "accepted" and pressure_result["state"]["diastolicValue"] is None
    for kind, value, unit in (("weight", 0, "kg"), ("temperature", 50, "Cel"), ("heart_rate", 0, "/min")):
        rejected = await operation("RecordPatientMeasurement", uuid7(), {
            "patientId": str(patient), "kind": kind, "value": value, "unit": unit,
        }, actor=assistant)
        assert rejected["status"] == "rejected"

    races = await asyncio.gather(
        operation("CorrectPatientMeasurement", second, {"value": 70}, 1, actor=assistant),
        operation("CorrectPatientMeasurement", second, {"value": 71}, 1, actor=assistant),
    )
    assert sorted(item["status"] for item in races) == ["accepted", "conflict"]
    await operation("InvalidatePatientMeasurement", second, {}, 2, actor=assistant)
    summary = await get(f"/patients/{patient}/measurements/summary")
    assert next(item for item in summary["items"] if item["kind"] == "weight")["measurementId"] == str(historical)

    snapshot = await client.post(base + "/sync/snapshots", headers=access.authorization(assistant), json={"includeClinical": True})
    access.expect(snapshot, 201)
    items = (await get(f"/sync/snapshots/{snapshot.json()['snapshotId']}/items?shows=500", actor=assistant))["items"]
    measurements = [item for item in items if item["entityType"] == "patient_measurement"]
    assert {item["entityKey"] for item in measurements} == {str(first), str(historical), str(pressure)}
    async with administrative() as db:
        assert await db.scalar(text("SELECT count(*) FROM nightingale.patient_clinical_timeline WHERE entry_type='measurement'")) == 4
        assert await db.scalar(text("SELECT count(*) FROM nightingale.audit_events WHERE object_key::text LIKE '%PRIV-%'")) == 0

    retry, retry_measurement = uuid7(), uuid7()
    payload = {"patientId": str(patient), "kind": "heart_rate", "value": 72, "unit": "/min"}
    with patch("src.api.sync.application.operations_cases.apply_measurement_operation", side_effect=DAOError("Fixture rollback")):
        failed = await operation("RecordPatientMeasurement", retry_measurement, payload, operation_id=retry)
    assert failed["status"] == "retryable_failure"
    assert (await operation("RecordPatientMeasurement", retry_measurement, payload, operation_id=retry))["status"] == "accepted"

    await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": {"measurements": "none"}}, 1)
    await get(f"/patients/{patient}/measurements", actor=assistant, status=403)
    await get(f"/patients/{patient}/measurements/summary", actor=assistant, status=403)
    print("Measurement checks passed: series, correction, history, offline, pressure, age, races, sync, rollback and permissions.")


if __name__ == "__main__":
    asyncio.run(support["main"](check_measurements))
