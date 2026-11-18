import asyncio
import runpy
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid7

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]

ADDED_SECTION_DEFAULTS = {
    "encounters": "read_write",
    "notes": "read_write",
    "measurements": "read_write",
    "immunizations": "read_write",
    "antecedents": "read_write",
    "declaredMedications": "read_write",
    "carePlans": "read_write",
    "diagnosticReports": "read_write",
    "specialtyTemplates": "read_write",
}


async def check_clinical_permissions(runtime, administrative, client, tokens):
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.authorization.application.authorization_cases import identified_users
    from src.api.sync.repository.dao import dao_changes
    from src.core import Ok
    from src.core.db import DAOError

    owner, assistant, outsider = [await access.issue(client, token["access_token"]) for token in tokens]
    async with administrative() as db:
        users = await identified_users(db, [UUID(owner["userId"])])
    identity = users[UUID(owner["userId"])]
    data = BootstrapPracticeInput(
        owner_issuer=identity.oidc_issuer,
        owner_subject=identity.oidc_subject,
        owner_name="Fixture Owner",
        professional_name="Fixture Professional",
        display_name="Fixture Practice",
        time_zone="America/Caracas",
        location_name="Fixture Office",
        location_address="Fictional address",
        location_country="VE",
        location_state="Fixture State",
        location_city="Fixture City",
    )
    async with administrative() as db:
        created = await bootstrap_practice(db, data)
    assert isinstance(created, Ok)
    account_id = created.value.account_id
    base = f"/v1/accounts/{account_id}"

    async def operation(action, key, payload, version=0, actor=owner, operation_id=None, status=200):
        response = await client.post(base + "/sync/operations", headers=access.authorization(actor), json={"operations": [{
            "operationId": str(operation_id or uuid7()), "contractVersion": 1, "action": action,
            "entityKey": str(key), "expectedVersion": version, "payload": payload,
        }]})
        access.expect(response, status)
        return response.json()["results"][0] if status == 200 else response.json()

    async def accept(invitation_id):
        response = await client.post(
            f"/v1/me/invitations/{invitation_id}/accept",
            headers=access.authorization(assistant),
            json={"operationId": str(uuid7())},
        )
        access.expect(response, 200)

    async def state():
        async with administrative() as db:
            return (await db.execute(text("""
                SELECT m.version,m.clinical_profile_access,m.conditions_access,m.allergies_access,
                    m.encounters_access,m.notes_access,m.measurements_access,
                    m.immunizations_access,m.antecedents_access,h.permission_epoch,
                    (SELECT count(*) FROM nightingale.operation_receipts WHERE account_id=m.account_id),
                    (SELECT count(*) FROM nightingale.audit_events WHERE account_id=m.account_id),
                    (SELECT count(*) FROM nightingale.change_log WHERE account_id=m.account_id)
                FROM nightingale.account_memberships m
                JOIN nightingale.account_sync_heads h ON h.account_id=m.account_id
                WHERE m.account_id=:account_id AND m.user_id=:user_id
            """), {"account_id": account_id, "user_id": UUID(assistant["userId"])})).one()

    assert (await operation("RegisterAccountDevice", owner["deviceId"], {}))["status"] == "accepted"
    invitation = uuid7()
    assert (await operation("CreateInvitation", invitation, {"inviteeUserId": assistant["userId"]}))["status"] == "accepted"
    await accept(invitation)
    assert (await operation("RegisterAccountDevice", assistant["deviceId"], {}, actor=assistant))["status"] == "accepted"

    async def get_result(result_id, actor=assistant, status=200):
        response = await client.get(
            base + f"/sync/operations/{result_id}", headers=access.authorization(actor)
        )
        access.expect(response, status)
        return response.json()

    async def result_audits():
        async with administrative() as db:
            return (await db.execute(text("""
                SELECT object_key FROM nightingale.audit_events
                WHERE account_id=:account_id AND action='ReadOperationResult'
            """), {"account_id": account_id})).scalars().all()

    initial = await state()
    assert initial[1:9] == ("read_write",) * 8

    response = await client.get(base + "/access", headers=access.authorization(assistant))
    access.expect(response, 200)
    assert response.json()["clinicalPermissions"] == {
        "clinicalProfile": "read_write",
        "conditions": "read_write",
        "allergies": "read_write",
        **ADDED_SECTION_DEFAULTS,
    }
    assert "SetMemberClinicalPermissions" not in response.json()["allowedActions"]

    permissions = {"clinicalProfile": "none", "conditions": "read", "allergies": "read_write"}
    operation_id = uuid7()
    changed = await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": permissions}, 1, operation_id=operation_id)
    assert changed["status"] == "accepted" and changed["entityVersion"] == 2, changed
    assert changed["state"]["clinicalPermissions"] == {**permissions, **ADDED_SECTION_DEFAULTS}
    effective = await state()
    assert effective[0] == initial[0] + 1 and effective[9] == initial[9] + 1
    duplicate = await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": permissions}, 1, operation_id=operation_id)
    assert duplicate["status"] == "duplicate" and duplicate["originalResult"]["status"] == "accepted"
    conflict = await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": {**permissions, "conditions": "read_write"}}, 1, operation_id=operation_id)
    assert conflict["status"] == "conflict" and conflict["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    assert (await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": permissions}, 2))["error"]["code"] == "NO_CHANGES"
    unchanged = await state()
    assert unchanged[0:10] == effective[0:10]
    assert (await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": permissions}, 1))["error"]["code"] == "VERSION_CONFLICT"
    await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": permissions}, 2, actor=assistant, status=403)
    await operation("SetMemberClinicalPermissions", owner["userId"], {"clinicalPermissions": permissions}, 1, status=403)

    response = await client.get(base + f"/members/{assistant['userId']}/clinical-permissions", headers=access.authorization(owner))
    access.expect(response, 200)
    assert response.json()["clinicalPermissions"] == {**permissions, **ADDED_SECTION_DEFAULTS} and response.json()["membershipVersion"] == 2
    response = await client.get(base + f"/members/{assistant['userId']}/clinical-permissions", headers=access.authorization(assistant))
    access.expect(response, 403)
    response = await client.get(base + "/access", headers=access.authorization(assistant))
    assert response.json()["clinicalPermissions"] == {**permissions, **ADDED_SECTION_DEFAULTS}

    assert (await operation("SetMembershipStatus", assistant["userId"], {"status": "inactive"}, 2))["entityVersion"] == 3
    assert (await state())[1:9] == ("none", "read", "read_write", "read_write", "read_write", "read_write", "read_write", "read_write")
    assert (await operation("SetMembershipStatus", assistant["userId"], {"status": "active"}, 3))["entityVersion"] == 4
    assert (await state())[1:9] == ("none", "read", "read_write", "read_write", "read_write", "read_write", "read_write", "read_write")

    before = await state()
    original_append = dao_changes.append
    retry_id = uuid7()
    updated = {"clinicalProfile": "read", "conditions": "none", "allergies": "read"}
    async def fail_group(db, values, **kwargs):
        return await original_append(db, {**values, "ordinal": 0}, **kwargs)
    with patch.object(dao_changes, "append", side_effect=fail_group):
        failed = await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": updated}, 4, operation_id=retry_id)
    assert failed["status"] == "retryable_failure" and failed["error"]["code"] == "TEMPORARY_FAILURE"
    assert await state() == before
    recovered = await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": updated}, 4, operation_id=retry_id)
    assert recovered["status"] == "accepted" and recovered["entityVersion"] == 5
    after = await state()
    assert after[0] == 5 and after[1:9] == ("read", "none", "read", "read_write", "read_write", "read_write", "read_write", "read_write")
    assert after[9] == before[9] + 1 and after[10:] == tuple(value + 1 for value in before[10:])

    first_id = uuid7()
    second_id = uuid7()
    first_permissions = {"clinicalProfile": "none", "conditions": "read", "allergies": "read_write"}
    second_permissions = {"clinicalProfile": "read_write", "conditions": "none", "allergies": "read"}
    first, second = await asyncio.gather(
        operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": first_permissions}, 5, operation_id=first_id),
        operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": second_permissions}, 5, operation_id=second_id),
    )
    assert sorted(item["status"] for item in (first, second)) == ["accepted", "conflict"]
    winner = first if first["status"] == "accepted" else second
    assert winner["state"]["clinicalPermissions"] in (
        {**first_permissions, **ADDED_SECTION_DEFAULTS},
        {**second_permissions, **ADDED_SECTION_DEFAULTS},
    )
    response = await client.get(base + f"/members/{assistant['userId']}/clinical-permissions", headers=access.authorization(owner))
    assert response.json()["clinicalPermissions"] == winner["state"]["clinicalPermissions"]
    assert set(response.json()["clinicalPermissions"]) == {
        "clinicalProfile", "conditions", "allergies", *ADDED_SECTION_DEFAULTS
    }
    assert response.json()["membershipVersion"] == 6

    read_write = {"clinicalProfile": "none", "conditions": "read_write", "allergies": "read_write"}
    assert (await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": read_write}, 6))["status"] == "accepted"
    patient_id = uuid7()
    assert (await operation("RegisterPatient", patient_id, {"fullName": "Fixture Patient"}))["status"] == "accepted"
    condition_id = uuid7()
    condition_payload = {"patientId": str(patient_id), "name": "Fixture condition"}
    assert (await operation("CreatePatientCondition", condition_id, condition_payload, actor=assistant, operation_id=condition_id))["status"] == "accepted"
    allergy_review_id = uuid7()
    allergy_payload = {"section": "allergies", "informationStatus": "unknown"}
    assert (await operation("SetPatientClinicalSectionReview", patient_id, allergy_payload, actor=assistant, operation_id=allergy_review_id))["status"] == "accepted"

    conditions_none = {"clinicalProfile": "none", "conditions": "none", "allergies": "read_write"}
    assert (await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": conditions_none}, 7))["status"] == "accepted"
    await operation("CreatePatientCondition", condition_id, condition_payload, actor=assistant, operation_id=condition_id, status=403)
    await operation("CreatePatientCondition", condition_id, {**condition_payload, "name": "Changed"}, actor=assistant, operation_id=condition_id, status=403)
    await get_result(condition_id, status=403)
    duplicate = await operation("SetPatientClinicalSectionReview", patient_id, allergy_payload, actor=assistant, operation_id=allergy_review_id)
    assert duplicate["status"] == "duplicate"
    assert (await get_result(allergy_review_id))["state"]["section"] == "allergies"

    allergies_none = {"clinicalProfile": "none", "conditions": "read_write", "allergies": "none"}
    assert (await operation("SetMemberClinicalPermissions", assistant["userId"], {"clinicalPermissions": allergies_none}, 8))["status"] == "accepted"
    assert (await operation("CreatePatientCondition", condition_id, condition_payload, actor=assistant, operation_id=condition_id))["status"] == "duplicate"
    assert (await get_result(condition_id))["state"]["name"] == "Fixture condition"
    await operation("SetPatientClinicalSectionReview", patient_id, allergy_payload, actor=assistant, operation_id=allergy_review_id, status=403)
    await get_result(allergy_review_id, status=403)

    assistant_second = await access.issue(client, tokens[1]["access_token"])
    assert (await operation("RegisterAccountDevice", assistant_second["deviceId"], {}, actor=assistant_second))["status"] == "accepted"
    assert (await operation("CreatePatientCondition", condition_id, condition_payload, actor=assistant_second, operation_id=condition_id))["status"] == "duplicate"
    assert (await get_result(condition_id, actor=assistant_second))["status"] == "accepted"
    await operation("SetPatientClinicalSectionReview", patient_id, allergy_payload, actor=assistant_second, operation_id=allergy_review_id, status=403)
    await get_result(allergy_review_id, actor=assistant_second, status=403)

    audits = await result_audits()
    assert len(audits) == 6 and set(audits) == {str(condition_id), str(allergy_review_id)}
    before_audits = len(audits)
    async def fail_audit(db, event):
        raise DAOError("Fixture audit failure")
    with patch("src.api.sync.application.operations_cases.record_control", side_effect=fail_audit):
        await get_result(condition_id, status=503)
    assert len(await result_audits()) == before_audits

    race_read = client.get(
        base + f"/sync/operations/{condition_id}", headers=access.authorization(assistant_second)
    )
    race_revoke = operation(
        "SetMemberClinicalPermissions", assistant["userId"],
        {"clinicalPermissions": conditions_none}, 9,
    )
    race_response, race_permission = await asyncio.gather(race_read, race_revoke)
    access.expect(race_response, race_response.status_code)
    assert race_response.status_code in (200, 403)
    assert race_permission["status"] == "accepted"
    await get_result(condition_id, actor=assistant_second, status=403)
    assert (await operation(
        "SetMemberClinicalPermissions", assistant["userId"],
        {"clinicalPermissions": allergies_none}, 10,
    ))["status"] == "accepted"

    routine_actions = {
        "encounters": "CreatePatientEncounter",
        "notes": "CreatePatientNote",
        "measurements": "RecordPatientMeasurement",
        "immunizations": "RecordPatientImmunization",
        "antecedents": "CreatePatientAntecedent",
    }
    routine_results = []
    for action in routine_actions.values():
        result_id = uuid7()
        result = await operation(
            action, uuid7(), {}, actor=assistant, operation_id=result_id
        )
        assert result["status"] == "rejected"
        assert result["error"]["code"] == "VALIDATION_ERROR"
        routine_results.append(result_id)

    combined = {
        **allergies_none,
        "encounters": "none",
        "notes": "none",
        "measurements": "none",
        "immunizations": "none",
        "antecedents": "none",
    }
    assert (await operation(
        "SetMemberClinicalPermissions", assistant["userId"],
        {"clinicalPermissions": combined}, 11,
    ))["status"] == "accepted"
    for result_id in routine_results:
        await get_result(result_id, status=403)
    read_only = {**combined, **{section: "read" for section in routine_actions}}
    assert (await operation(
        "SetMemberClinicalPermissions", assistant["userId"],
        {"clinicalPermissions": read_only}, 12,
    ))["status"] == "accepted"
    for result_id in routine_results:
        await get_result(result_id, status=403)

    section_actions = {
        "clinicalProfile": ["SetPatientSexAtBirth"],
        "conditions": ["CreatePatientCondition", "UpdatePatientCondition", "InvalidatePatientCondition"],
        "allergies": ["CreatePatientAllergyIntolerance", "UpdatePatientAllergyIntolerance", "InvalidatePatientAllergyIntolerance"],
        "encounters": ["CreatePatientEncounter", "UpdatePatientEncounter", "InvalidatePatientEncounter"],
        "notes": ["CreatePatientNote", "UpdatePatientNote", "InvalidatePatientNote"],
        "measurements": ["RecordPatientMeasurement", "CorrectPatientMeasurement", "InvalidatePatientMeasurement"],
        "immunizations": ["RecordPatientImmunization", "UpdatePatientImmunization", "InvalidatePatientImmunization"],
        "antecedents": ["CreatePatientAntecedent", "UpdatePatientAntecedent", "InvalidatePatientAntecedent"],
    }
    for section, actions in section_actions.items():
        for level in ("read_write", "read", "none"):
            permissions = {name: "none" for name in section_actions}
            permissions[section] = level
            assert (await operation(
                "SetMemberClinicalPermissions", assistant["userId"],
                {"clinicalPermissions": permissions}, (await state())[0],
            ))["status"] == "accepted"
            for action in actions:
                # Routine updates resolve the scoped object before payload errors.
                write_status = 404 if section in routine_actions and action != actions[0] else 200
                await operation(action, uuid7(), {"fixtureUnknown": True}, actor=assistant,
                                status=write_status if level == "read_write" else 403)
            if section in ("conditions", "allergies"):
                await operation("SetPatientClinicalSectionReview", patient_id,
                                {"section": section, "informationStatus": "unknown"},
                                version=999, actor=assistant,
                                status=200 if level == "read_write" else 403)

    # AU-32: old ambiguous receipts must not expose a result or suggest a section.
    ambiguous_id = uuid7()
    async with administrative() as db:
        async with db.begin():
            await db.execute(text("""
                INSERT INTO nightingale.operation_receipts
                    (account_id,actor_user_id,operation_id,source_device_id,contract_version,
                     action,entity_type,entity_key,request_hash,clinical_section,status,
                     entity_version,result_json,completed_at,result_expires_at,purged_at)
                SELECT account_id,actor_user_id,:new_id,source_device_id,contract_version,
                    'SetPatientClinicalSectionReview','patient_clinical_section_review',entity_key,
                    request_hash,NULL,status,entity_version,
                    jsonb_set(result_json,'{operationId}',to_jsonb(CAST(:new_text AS text))),
                    completed_at,result_expires_at,purged_at
                FROM nightingale.operation_receipts
                WHERE account_id=:account_id AND actor_user_id=:user_id AND operation_id=:source_id
            """), {"new_id": ambiguous_id, "new_text": str(ambiguous_id),
                   "account_id": account_id, "user_id": UUID(assistant["userId"]),
                   "source_id": routine_results[0]})
            await db.execute(text("""
                INSERT INTO nightingale.audit_events
                    (id,account_id,actor_kind,actor_user_id,actor_device_id,operator_ref,
                     action,object_type,object_key,outcome,operation_id,correlation_id,occurred_at)
                SELECT :audit_id,account_id,actor_kind,actor_user_id,actor_device_id,operator_ref,
                    'SetPatientClinicalSectionReview','patient_clinical_section_review',object_key,
                    outcome,:new_id,correlation_id,occurred_at
                FROM nightingale.audit_events
                WHERE account_id=:account_id AND actor_user_id=:user_id AND operation_id=:source_id
            """), {"audit_id": uuid7(), "new_id": ambiguous_id, "account_id": account_id,
                   "user_id": UUID(assistant["userId"]), "source_id": routine_results[0]})
    await get_result(ambiguous_id, status=403)
    permissions = {name: "none" for name in section_actions}
    permissions["conditions"] = "read_write"
    assert (await operation(
        "SetMemberClinicalPermissions", assistant["userId"],
        {"clinicalPermissions": permissions}, (await state())[0],
    ))["status"] == "accepted"
    await operation("SetPatientClinicalSectionReview", patient_id,
                    {"section": "conditions", "informationStatus": "unknown"},
                    actor=assistant, operation_id=ambiguous_id, status=403)
    await get_result(ambiguous_id, status=403)

    owner_second = await access.issue(client, tokens[0]["access_token"])
    assert (await operation("RegisterAccountDevice", owner_second["deviceId"], {}, actor=owner_second))["status"] == "accepted"
    assert (await operation("RevokeAccountDevice", owner["deviceId"], {}, 1, actor=owner_second))["status"] == "accepted"
    response = await client.get(base + f"/sync/operations/{winner['operationId']}", headers=access.authorization(owner))
    access.expect(response, 403)
    response = await client.get(base + f"/sync/operations/{winner['operationId']}", headers=access.authorization(owner_second))
    access.expect(response, 200)
    assert response.json()["state"]["clinicalPermissions"] == winner["state"]["clinicalPermissions"]
    response = await client.get(base + f"/members/{outsider['userId']}/clinical-permissions", headers=access.authorization(owner_second))
    access.expect(response, 404)
    # Hold a real acceptance before commit; observe a PostgreSQL waiter, then release.
    from pydantic import SecretStr
    from src.settings.api_settings import api_settings
    api_settings.sync_signing_key = SecretStr("fixture-authorization-race-signing-key-2026")

    async def wait_for_blocker(pid):
        async with administrative() as observer:
            for _ in range(150):
                if await observer.scalar(text(
                    "SELECT EXISTS(SELECT FROM pg_stat_activity WHERE :pid=ANY(pg_blocking_pids(pid)))"
                ), {"pid": pid}):
                    return
                await asyncio.sleep(.02)
        raise AssertionError("No PostgreSQL lock waiter observed")

    for acceptance_first in (False, True):
        await operation("SetMemberClinicalPermissions", assistant["userId"],
                        {"clinicalPermissions": {"notes": "read_write"}}, (await state())[0], actor=owner_second)
        note_id, note_operation, permission_operation = uuid7(), uuid7(), uuid7()
        version = (await state())[0]
        held_id = note_operation if acceptance_first else permission_operation
        entered, release = asyncio.Event(), asyncio.Event()
        holder_pid = None
        original_append = dao_changes.append

        async def pause_acceptance(db, values, **kwargs):
            nonlocal holder_pid
            result = await original_append(db, values, **kwargs)
            if values["operation_id"] == held_id:
                holder_pid = await db.scalar(text("SELECT pg_backend_pid()"))
                entered.set()
                await asyncio.wait_for(release.wait(), 10)
            return result

        def write_note():
            return operation("CreatePatientNote", note_id,
                             {"patientId": str(patient_id), "body": "Fixture race note"},
                             actor=assistant, operation_id=note_operation,
                             status=200 if acceptance_first else 403)

        def withdraw_notes():
            return operation("SetMemberClinicalPermissions", assistant["userId"],
                             {"clinicalPermissions": {"notes": "none"}}, version,
                             actor=owner_second, operation_id=permission_operation)

        tasks = []
        with patch.object(dao_changes, "append", side_effect=pause_acceptance):
            try:
                tasks.append(asyncio.create_task(write_note() if acceptance_first else withdraw_notes()))
                await asyncio.wait_for(entered.wait(), 10)
                tasks.append(asyncio.create_task(withdraw_notes() if acceptance_first else write_note()))
                if not acceptance_first:
                    tasks.append(asyncio.create_task(client.post(
                        base + "/sync/snapshots", headers=access.authorization(assistant),
                        json={"includeClinical": True},
                    )))
                assert holder_pid is not None
                await wait_for_blocker(holder_pid)
            finally:
                release.set()
                await asyncio.gather(*tasks, return_exceptions=True)
        outcomes = [await task for task in tasks]
        if not acceptance_first:
            captured = outcomes[2]
            if captured.status_code == 503:
                access.expect(captured, 503)
                assert captured.json()["code"] == "DEPENDENCY_UNAVAILABLE"
                captured = await client.post(base + "/sync/snapshots",
                                            headers=access.authorization(assistant), json={"includeClinical": True})
            access.expect(captured, 201)
            assert "notes" not in captured.json()["clinicalSections"]
        await get_result(note_operation, status=403 if acceptance_first else 404)
        async with administrative() as db:
            count = await db.scalar(text("SELECT count(*) FROM nightingale.patient_notes WHERE id=:id"), {"id": note_id})
            receipt = await db.scalar(text("SELECT count(*) FROM nightingale.operation_receipts WHERE operation_id=:id"), {"id": note_operation})
            assert count == receipt == int(acceptance_first)
    for actor, expected in ((assistant, 403), (outsider, 404)):
        for note in (note_id, uuid7()):
            response = await client.get(base + f"/patients/{patient_id}/notes/{note}", headers=access.authorization(actor))
            access.expect(response, expected)
            assert "Fixture race note" not in response.text
            assert str(note) not in response.text
    response = await client.get(base + "/patients?page=1&shows=1", headers=access.authorization(outsider))
    access.expect(response, 404)
    legacy_permissions = {name: "read_write" for name in (
        "clinicalProfile", "conditions", "allergies", "encounters", "notes",
        "measurements", "immunizations", "antecedents",
    )}
    await operation("SetMemberClinicalPermissions", assistant["userId"],
                    {"clinicalPermissions": legacy_permissions}, (await state())[0], actor=owner_second)
    legacy_id = uuid7()
    legacy_version = (await state())[0]
    unchanged = await operation("SetMemberClinicalPermissions", assistant["userId"],
                                {"clinicalPermissions": legacy_permissions}, legacy_version,
                                actor=owner_second, operation_id=legacy_id)
    assert unchanged["error"]["code"] == "NO_CHANGES"
    duplicate = await operation("SetMemberClinicalPermissions", assistant["userId"],
                                {"clinicalPermissions": {**legacy_permissions, "declaredMedications": "read_write"}},
                                legacy_version, actor=owner_second, operation_id=legacy_id)
    assert duplicate["status"] == "duplicate" and duplicate["originalResult"]["error"]["code"] == "NO_CHANGES"
    for level in ("read", "none"):
        conflict = await operation("SetMemberClinicalPermissions", assistant["userId"],
                                   {"clinicalPermissions": {**legacy_permissions, "declaredMedications": level}},
                                   legacy_version, actor=owner_second, operation_id=legacy_id)
        assert conflict["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    assert (await state())[0] == legacy_version
    print("Authorization races passed: real PostgreSQL waiters, section-first blocks effect/result and filters capture; acceptance-first preserves its note and receipt.")
    print("Clinical permission checks passed: defaults, section levels, versions, idempotency, races, rollback and device revocation.")


if __name__ == "__main__":
    asyncio.run(support["main"](check_clinical_permissions))
