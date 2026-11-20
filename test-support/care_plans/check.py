import asyncio
import runpy
from pathlib import Path
from uuid import uuid7

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]


async def check_care_plans(runtime, administrative, client, tokens):
    from pydantic import SecretStr
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.authorization.application.authorization_cases import identified_users
    from src.core import Ok
    from src.settings.api_settings import api_settings

    api_settings.sync_signing_key = SecretStr("fixture-care-plan-signing-key-2026")
    from uuid import UUID
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

    plan = uuid7()
    created_plan = await operation("CreatePatientCarePlan", plan, {
        "patientId": str(patient), "title": "PRIV-E17-CONTROL-PESO",
        "purpose": "Plan preventivo", "startDate": "2026-11",
    }, actor=assistant)
    assert created_plan["state"]["planStatus"] == "active"
    assert created_plan["state"]["conditionId"] is None

    goal = uuid7()
    created_goal = await operation("AddCarePlanGoal", goal, {
        "planId": str(plan), "patientId": str(patient), "description": "Reducir peso",
        "goalKind": "measurable", "measurementKind": "weight",
        "targetValue": "70", "unit": "kg",
    }, actor=assistant)
    assert created_goal["state"]["evaluationStatus"] == "pending"

    action = uuid7()
    created_action = await operation("AddCarePlanAction", action, {
        "planId": str(plan), "patientId": str(patient), "goalId": str(goal),
        "description": "Caminar 30 minutos diarios",
    }, actor=assistant)
    assert created_action["state"]["completionStatus"] == "not_completed"
    wrong_goal = await operation("AddCarePlanAction", uuid7(), {
        "planId": str(plan), "patientId": str(patient), "goalId": str(uuid7()),
        "description": "Fixture",
    }, actor=assistant, status=404)
    assert wrong_goal["code"] == "NOT_FOUND"

    completed = await operation("CompleteCarePlanAction", action, {
        "completionNote": "Paciente reporta cumplimiento",
    }, 1, actor=assistant)
    assert completed["entityVersion"] == 2
    assert completed["state"]["completionStatus"] == "completed"

    still_pending = await get(f"/patients/{patient}/care-plans/{plan}/goals/{goal}")
    assert still_pending["evaluationStatus"] == "pending", "completar actividad no evalúa el objetivo"

    evaluated = await operation("EvaluateCarePlanGoal", goal, {
        "evaluationStatus": "achieved", "note": "Meta ficticia alcanzada",
    }, 1, actor=assistant)
    assert evaluated["entityVersion"] == 2
    assert evaluated["state"]["evaluatedByUserId"] == assistant["userId"]
    assert evaluated["state"]["evaluationNote"] == "Meta ficticia alcanzada"
    read_goal = await get(f"/patients/{patient}/care-plans/{plan}/goals/{goal}")
    assert read_goal["evaluationNote"] == "Meta ficticia alcanzada"

    narrative = uuid7()
    await operation("AddCarePlanGoal", narrative, {
        "planId": str(plan), "patientId": str(patient),
        "description": "Objetivo narrativo", "goalKind": "narrative",
    }, actor=assistant)
    pending_action = uuid7()
    await operation("AddCarePlanAction", pending_action, {
        "planId": str(plan), "patientId": str(patient),
        "description": "Acción pendiente",
    }, actor=assistant)
    goal_base = f"/patients/{patient}/care-plans/{plan}/goals"
    narrative_only = await get(goal_base + "?goalKind=narrative")
    assert narrative_only["total"] == 1 and narrative_only["items"][0]["goalId"] == str(narrative)
    pending_only = await get(goal_base + "?evaluationStatus=pending")
    assert pending_only["total"] == 1 and pending_only["items"][0]["goalId"] == str(narrative)
    combined = await get(goal_base + "?goalKind=narrative&evaluationStatus=pending")
    assert combined["total"] == 1 and combined["items"][0]["goalId"] == str(narrative)
    goal_pages = [await get(goal_base + f"?page={page}&shows=1") for page in (1, 2)]
    assert all(page["total"] == 2 and len(page["items"]) == 1 for page in goal_pages)
    assert goal_pages[0]["items"][0]["goalId"] != goal_pages[1]["items"][0]["goalId"]
    actions_pending = await get(
        f"/patients/{patient}/care-plans/{plan}/actions?completionStatus=not_completed"
    )
    assert actions_pending["total"] == 1
    assert actions_pending["items"][0]["actionId"] == str(pending_action)
    evaluated_without_note = await operation("EvaluateCarePlanGoal", narrative, {
        "evaluationStatus": "not_achieved",
    }, 1, actor=assistant)
    assert evaluated_without_note["state"]["evaluationNote"] is None
    goal_history = (await get(f"{goal_base}/{goal}/history"))["items"]
    assert [item["evaluationNote"] for item in goal_history] == [None, "Meta ficticia alcanzada"], goal_history
    recent_goal_history = await get(f"{goal_base}/{goal}/history?afterVersion=1")
    assert recent_goal_history["total"] == 1
    assert recent_goal_history["items"][0]["version"] == 2

    review = uuid7()
    created_review = await operation("AddCarePlanReview", review, {
        "planId": str(plan), "patientId": str(patient), "summary": "Primera revisión",
        "nextReviewDate": "2026-12",
    }, actor=assistant)
    assert created_review["state"]["nextReviewDate"] == "2026-12"

    closed = await operation("UpdatePatientCarePlan", plan, {
        "planStatus": "closed", "statusReason": "Objetivo logrado",
    }, 1, actor=assistant)
    assert closed["state"]["planStatus"] == "closed"
    no_reason = await operation("UpdatePatientCarePlan", plan, {"planStatus": "active"}, 2, actor=assistant)
    assert no_reason["status"] == "rejected"

    history = (await get(f"/patients/{patient}/care-plans/{plan}/history"))["items"]
    assert len(history) == 2 and history[0]["planStatus"] == "active"

    snapshot = await client.post(base + "/sync/snapshots", headers=access.authorization(assistant), json={"includeClinical": True})
    access.expect(snapshot, 201)
    items = (await get(f"/sync/snapshots/{snapshot.json()['snapshotId']}/items?shows=500", actor=assistant))["items"]
    entities = {item["entityType"] for item in items}
    assert {"care_plan", "care_plan_goal", "care_plan_action", "care_plan_review"} <= entities
    captured_goal = next(item for item in items
        if item["entityType"] == "care_plan_goal" and item["entityKey"] == str(goal))
    assert captured_goal["state"]["evaluationNote"] == "Meta ficticia alcanzada"
    async with administrative() as db:
        assert await db.scalar(text("SELECT count(*) FROM nightingale.audit_events WHERE object_key::text LIKE '%PRIV-%'")) == 0
        assert await db.scalar(text("SELECT count(*) FROM nightingale.care_plan_histories WHERE id=:id"), {"id": plan}) == 2
        assert await db.scalar(text("SELECT count(*) FROM nightingale.care_plan_goal_histories WHERE id=:id"), {"id": goal}) == 2
        assert await db.scalar(text("SELECT evaluation_note FROM nightingale.care_plan_goals WHERE id=:id"), {"id": goal}) == "Meta ficticia alcanzada"
        history_notes = (await db.execute(text("""
            SELECT evaluation_note FROM nightingale.care_plan_goal_histories
            WHERE id=:id ORDER BY version
        """), {"id": goal})).scalars().all()
        assert list(history_notes) == [None, "Meta ficticia alcanzada"]

    await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": {"carePlans": "none"}}, 1)
    await get(f"/patients/{patient}/care-plans", actor=assistant, status=403)
    await operation("CreatePatientCarePlan", plan, {"patientId": str(patient), "title": "X"}, actor=assistant, status=403)
    print("Care plan checks passed: E17 plan/objectives/actions/reviews, done != achieved, versions, sync, privacy and permissions.")


if __name__ == "__main__":
    asyncio.run(support["main"](check_care_plans))
