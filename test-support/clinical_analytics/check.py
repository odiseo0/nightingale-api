import asyncio
import runpy
from pathlib import Path
from uuid import UUID, uuid7

from sqlalchemy import select, text

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]


async def check_clinical_analytics(runtime, administrative, client, tokens):
    from pydantic import SecretStr
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.analytics.application.etl_cases import rebuild_analytics, run_etl
    from src.api.analytics.repository.dao import dao_analytic_points
    from src.api.analytics.repository.models import AnalyticMeasurementPoint
    from src.api.authorization.application.authorization_cases import identified_users
    from src.core import Ok
    from src.settings.api_settings import api_settings

    api_settings.sync_signing_key = SecretStr("fixture-analytics-signing-key-2026")
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
    base = f"/v1/accounts/{account_id}"

    async def operation(action, key, payload, version=0, actor=owner, operation_id=None, status=200):
        response = await client.post(base + "/sync/operations", headers=access.authorization(actor), json={"operations": [{
            "operationId": str(operation_id or uuid7()), "contractVersion": 1,
            "action": action, "entityKey": str(key), "expectedVersion": version, "payload": payload,
        }]})
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
    await operation("RegisterPatient", patient, {"fullName": "Fixture Patient"})

    old, wrong = uuid7(), uuid7()
    await operation("RecordPatientMeasurement", old, {
        "patientId": str(patient), "kind": "weight", "measuredAt": "2026-11-01T09:00:00Z",
        "value": "70", "unit": "kg",
    }, actor=assistant)
    await operation("RecordPatientMeasurement", wrong, {
        "patientId": str(patient), "kind": "weight", "measuredAt": "2026-11-01T09:05:00Z",
        "value": "700", "unit": "kg",
    }, actor=assistant)
    corrected_result = await operation("CorrectPatientMeasurement", wrong, {
        "value": "71", "correctionReason": "Transcripción",
    }, 1, actor=assistant)
    assert corrected_result["status"] == "accepted"

    series = await get(f"/patients/{patient}/analytics/series?kind=weight")
    assert [point["value"] for point in series["points"]] == ["70", "71"], "la serie usa solo válidos y correcciones"
    assert all(point["sourceVersion"] == 1 for point in series["points"] if point["sourceMeasurementId"] != str(wrong))
    corrected = [point for point in series["points"] if point["sourceMeasurementId"] == str(wrong)][0]
    assert corrected["sourceVersion"] == 2

    async with administrative() as db:
        await run_etl(db, account_id)
        points = await db.scalars(select(AnalyticMeasurementPoint).where(
            AnalyticMeasurementPoint.account_id == account_id,
            AnalyticMeasurementPoint.patient_id == patient,
        ))
        points = list(points)
        assert len(points) == 2, "ETL sin duplicados tras corrección"
        assert {point.value for point in points} == {70, 71}
        await run_etl(db, account_id)
        points_after = list((await db.scalars(select(AnalyticMeasurementPoint).where(
            AnalyticMeasurementPoint.account_id == account_id,
            AnalyticMeasurementPoint.patient_id == patient,
        ))).all())
        assert len(points_after) == 2, "reintento no duplica puntos"
        await rebuild_analytics(db)
        points_rebuilt = list((await db.scalars(select(AnalyticMeasurementPoint).where(
            AnalyticMeasurementPoint.account_id == account_id,
            AnalyticMeasurementPoint.patient_id == patient,
        ))).all())
        assert sorted((p.measured_at, float(p.value)) for p in points_rebuilt) == sorted(
            (p.measured_at, float(p.value)) for p in points_after
        ), "la reconstrucción produce la misma proyección"
        assert await db.scalar(text("SELECT count(*) FROM nightingale.audit_events WHERE object_key::text LIKE '%PRIV-%'")) == 0

    # E20/E21: growth with WHO reference limits and birth-change recalculation.
    grown = uuid7()
    await operation("RegisterPatient", grown, {"fullName": "Fixture Child"})
    await operation("UpdatePatientProfile", grown, {"birthDate": "2021-10-18"}, 1)
    sex_result = await operation("SetPatientSexAtBirth", grown, {"sexAtBirth": "male", "sourceType": "patient"}, 0)
    assert sex_result["status"] == "accepted", sex_result

    birth_weight = uuid7()
    await operation("RecordPatientMeasurement", birth_weight, {
        "patientId": str(grown), "kind": "weight",
        "measuredAt": "2021-11-17T09:00:00Z", "value": "3.3464", "unit": "kg",
    }, actor=assistant)
    current_weight = uuid7()
    await operation("RecordPatientMeasurement", current_weight, {
        "patientId": str(grown), "kind": "weight",
        "measuredAt": "2026-11-17T09:00:00Z", "value": "20", "unit": "kg",
    }, actor=assistant)

    growth = await get(f"/patients/{grown}/analytics/growth?indicator=weight_for_age")
    by_source = {point["sourceMeasurementId"]: point for point in growth["points"]}
    assert abs(float(by_source[str(birth_weight)]["zScore"])) < 0.01, "mediana oficial da z≈0"
    assert by_source[str(current_weight)]["limitExplanation"], "E20: fuera de cobertura explica el límite sin curva"
    assert "diagnos" not in growth and "diagnosis" not in growth

    await operation("UpdatePatientProfile", grown, {"birthDate": "2020-10-18"}, 2)
    regrown = await get(f"/patients/{grown}/analytics/growth?indicator=weight_for_age")
    rebirth = {point["sourceMeasurementId"]: point for point in regrown["points"]}[str(birth_weight)]
    assert rebirth["ageMonths"] == 12, "E21: cambio de nacimiento recalcula la edad en el hecho"
    assert rebirth["limitExplanation"], "E21: derivado recalculado sin punto persistido ni versión oculta"

    await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": {"measurements": "none"}}, 1)
    await get(f"/patients/{patient}/analytics/series?kind=weight", actor=assistant, status=403)
    print("Clinical analytics checks passed: E03/E09 series with corrections, ETL idempotent retry, rebuild convergence, privacy and permissions.")


if __name__ == "__main__":
    asyncio.run(support["main"](check_clinical_analytics))
