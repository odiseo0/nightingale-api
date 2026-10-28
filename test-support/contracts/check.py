import asyncio
import copy
import json
import runpy
import secrets
from pathlib import Path
from uuid import UUID, uuid7
from unittest.mock import AsyncMock, patch

from pydantic import SecretStr

ROOT = Path(__file__).resolve().parents[2]
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]


def check_refs(document):
    def visit(value):
        if isinstance(value, dict):
            reference = value.get("$ref")
            if isinstance(reference, str) and reference.startswith("#/"):
                target = document
                for key in reference[2:].split("/"):
                    target = target[key.replace("~1", "/").replace("~0", "~")]
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)
    visit(document)


async def check_contracts(runtime, administrative, client, tokens):
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.authorization.domain.authorization import DeviceTokenIssued
    from src.api.sync.domain.capabilities import CapabilitiesResponse
    from src.api.sync.domain.downloads import ChangePage, SnapshotResponse, SyncItem
    from src.api.sync.domain.events import StreamEvent
    from src.api.sync.application import events_cases
    from src.api.sync.domain.operations import OperationBatchResult, OperationEnvelope, SERVICE_SCHEMAS, OFFER_SCHEMAS
    from src.core import Ok
    from src.core.schema import PaginatedResponse
    from src.core.schema.http import LiveResponse, ReadyResponse
    from src.settings.api_settings import api_settings

    examples = json.loads((ROOT / "contracts/examples.json").read_text(encoding="utf-8"))
    api_settings.sync_signing_key = SecretStr(secrets.token_urlsafe(48))
    for name in ("openapi.json", "public-models.schema.json", "accepted-operations.schema.json", "sse.schema.json"):
        check_refs(json.loads((ROOT / "contracts/api-v1" / name).read_text(encoding="utf-8")))
    generated = json.loads((ROOT / "contracts/api-v1/openapi.json").read_text(encoding="utf-8"))
    generated.pop("x-generated")
    response = await client.get("/openapi.json")
    assert response.status_code == 200 and response.json() == generated
    live = await client.get("/health/live")
    assert live.status_code == 200
    LiveResponse.model_validate(live.json())
    ready = await client.get("/health/ready")
    assert ready.status_code == 503  # ASGITransport does not start the process listener.
    ReadyResponse.model_validate(ready.json())
    response = await client.get("/v1/capabilities")
    access.expect(response, 200)
    capabilities = CapabilitiesResponse.model_validate(response.json())
    assert len(capabilities.operation_catalog) == 42 and capabilities.max_page_size == 500
    assert "AcceptInvitation" not in capabilities.operation_catalog and "AcceptInvitation" in capabilities.online_only_actions
    access.expect(await client.get("/v1/capabilities?unknown=1"), 422)

    async def issue(token):
        response = await client.post("/v1/auth/device-tokens", headers={"Authorization": "Bearer " + token}, json=examples["deviceRegistration"])
        access.expect(response, 201)
        DeviceTokenIssued.model_validate(response.json())
        return response.json()

    owner = await issue(tokens[0]["access_token"])
    response = await client.get("/v1/me", headers=access.authorization(owner))
    access.expect(response, 200)
    identity = response.json()
    async with administrative() as db:
        created = await bootstrap_practice(db, BootstrapPracticeInput(
            owner_issuer=identity["oidcIssuer"], owner_subject=identity["oidcSubject"], owner_name="Persona de prueba",
            professional_name="Profesional de prueba", display_name="Consulta de prueba", time_zone="America/Caracas",
            location_name="Sede de prueba", location_address="Dirección ficticia", location_country="VE",
            location_state="Estado de prueba", location_city="Ciudad de prueba",
        ))
    assert isinstance(created, Ok)
    base = f"/v1/accounts/{created.value.account_id}"

    async def operation(value, actor=owner):
        OperationEnvelope.model_validate(value)
        response = await client.post(base + "/sync/operations", headers=access.authorization(actor), json={"operations": [value]})
        access.expect(response, 200)
        return OperationBatchResult.model_validate(response.json()).results[0]

    registration = copy.deepcopy(examples["registerAccountDevice"])
    registration["entityKey"] = owner["deviceId"]
    assert (await operation(registration)).status == "accepted"
    access_response = await client.get(base + "/access", headers=access.authorization(owner))
    access.expect(access_response, 200)
    assert set(access_response.json()["allowedActions"]) == set(capabilities.operation_catalog)
    assert (await operation(examples["registerPatient"])).status == "accepted"
    response = await client.post(base + "/sync/snapshots", headers=access.authorization(owner), json=examples["snapshotRequest"])
    access.expect(response, 201)
    capture = SnapshotResponse.model_validate(response.json())
    assert response.json()["expiresAt"].endswith("Z")
    with patch.object(events_cases, "authorized_context", AsyncMock(side_effect=AssertionError("Journal read before confirmed LISTEN"))) as authorization:
        access.expect(await client.get(base + "/sync/events", params={"cursor": capture.base_cursor}, headers=access.authorization(owner)), 503)
        authorization.assert_not_awaited()
    updated = await operation(examples["updatePatient"])
    assert updated.status == "accepted" and updated.entity_version == 2
    duplicate = await operation(examples["updatePatient"])
    assert duplicate.status == "duplicate" and duplicate.original_result is not None and duplicate.original_result.entity_version == 2
    stale = await operation(examples["staleUpdatePatient"])
    assert stale.status == "conflict" and stale.error is not None and stale.error.code == "VERSION_CONFLICT"
    invalid = await operation(examples["invalidPayload"])
    assert invalid.status == "rejected" and invalid.error is not None and invalid.error.code == "VALIDATION_ERROR"
    response = await client.get(base + "/sync/changes", headers=access.authorization(owner), params={"cursor": capture.base_cursor})
    access.expect(response, 200)
    delta = ChangePage.model_validate(response.json())
    assert all(group["acceptedAt"].endswith("Z") for group in response.json()["groups"])
    assert len(delta.groups) == 1 and delta.groups[0].operation_id == UUID(examples["updatePatient"]["operationId"])
    assert delta.groups[0].changes[0].entity_version == 2
    response = await client.get(base + f'/sync/operations/{examples["updatePatient"]["operationId"]}', headers=access.authorization(owner))
    access.expect(response, 200)
    assert response.json()["status"] == "accepted"
    response = await client.get(base + f"/sync/snapshots/{capture.snapshot_id}/items", params={"page": 1, "shows": 2}, headers=access.authorization(owner))
    access.expect(response, 200)
    page = PaginatedResponse[SyncItem].model_validate(response.json())
    assert len(page.items) == 2 and page.total == capture.item_count
    for name in ("heartbeat", "accessRevoked"):
        StreamEvent.model_validate(examples[name])
    expired = await client.get(base + "/sync/changes", headers=access.authorization(owner), params={"cursor": "invalid"})
    access.expect(expired, 410)
    assert expired.json()["code"] == "CURSOR_EXPIRED"
    access.expect(await client.delete(base + f"/sync/snapshots/{capture.snapshot_id}", headers=access.authorization(owner)), 204)
    access.expect(await client.get(base + f"/sync/snapshots/{capture.snapshot_id}", headers=access.authorization(owner)), 404)

    assistant = await issue(tokens[1]["access_token"])
    invitation = {**registration, "operationId": str(uuid7()), "action": "CreateInvitation", "entityKey": str(uuid7()),
                  "payload": {"inviteeUserId": assistant["userId"]}}
    assert (await operation(invitation)).status == "accepted"
    access.expect(await client.post(f'/v1/me/invitations/{invitation["entityKey"]}/accept', headers=access.authorization(assistant), json={"operationId": str(uuid7())}), 200)
    assert (await operation({**registration, "operationId": str(uuid7()), "entityKey": assistant["deviceId"]}, assistant)).status == "accepted"
    response = await client.get(base + "/access", headers=access.authorization(assistant))
    access.expect(response, 200)
    owner_only = (set(capabilities.online_only_actions) | set(SERVICE_SCHEMAS) | set(OFFER_SCHEMAS) | {"UpdateProfessionalProfile"}) - {"RegisterAccountDevice"}
    assert set(response.json()["allowedActions"]) == set(capabilities.operation_catalog) - owner_only
    access.expect(await client.get(base + "/members", headers=access.authorization(assistant)), 403)
    print("Contract checks passed: generated HTTP schemas and local references, 42 actions, owner/assistant access sets, fictional example requests, duplicate/conflict/rejection, snapshot/delta/release and SSE model examples.")


if __name__ == "__main__":
    asyncio.run(support["main"](check=check_contracts))
