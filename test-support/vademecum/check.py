import asyncio
import hashlib
import json
import runpy
from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import UUID

from sqlalchemy import text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "vademecum/vademecum_venezuela_2026-11-03.json"
SOURCE_BYTES = SOURCE_PATH.read_bytes()
SOURCE = json.loads(SOURCE_BYTES)
support = runpy.run_path(str(ROOT / "test-support/sync/check.py"))
access = support["access"]
accounts = support["accounts"]


async def check_vademecum(runtime, administrative, client, tokens):
    from src.application import app
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.vademecum.application.import_cases import import_vademecum
    from src.api.vademecum.infrastructure.monographs_api import router as monographs_router
    from src.api.vademecum.infrastructure.products_api import router as products_router
    from src.api.vademecum.repository.dao import dao_vademecum
    from src.core import Ok
    from src.core.services.oidc import verify_identity

    for router, endpoint in ((products_router, "products"), (monographs_router, "monographs")):
        path = f"/v1/accounts/{{account_id}}/vademecum/{endpoint}"
        if not any(getattr(route, "path", None) == path for route in app.routes):
            app.include_router(router)

    owner, assistant, outsider = [
        await access.issue(client, token["access_token"]) for token in tokens
    ]
    identity = await verify_identity(tokens[0]["access_token"])
    assert isinstance(identity, Ok)
    created = await accounts.call(administrative, bootstrap_practice, BootstrapPracticeInput(
        owner_issuer=identity.value["issuer"], owner_subject=identity.value["subject"],
        owner_name="Fixture Owner", professional_name="Fixture Professional",
        display_name="Fixture Practice", time_zone="America/Caracas",
        location_name="Fixture Office", location_address="Fictional address",
        location_country="VE", location_state="Fixture State", location_city="Fixture City",
    ))
    assert isinstance(created, Ok)
    account_id = created.value.account_id
    base = f"/v1/accounts/{account_id}/vademecum"
    async with administrative() as db:
        async with db.begin():
            await db.execute(text("""
                INSERT INTO nightingale.account_memberships(account_id,user_id)
                VALUES (:account,:user)
            """), {"account": account_id, "user": UUID(assistant["userId"])})
            for installation in (owner, assistant):
                await db.execute(text("""
                    INSERT INTO nightingale.account_device_accesses
                        (account_id,device_id,user_id,created_by_user_id,changed_by_user_id)
                    VALUES (:account,:device,:user,:user,:user)
                """), {
                    "account": account_id, "device": UUID(installation["deviceId"]),
                    "user": UUID(installation["userId"]),
                })

    access.expect(await client.get(base + "/products", headers=access.authorization(owner)), 503)
    access.expect(await client.get(base + "/products"), 401)
    access.expect(await client.get(base + "/products", headers=access.authorization(outsider)), 404)
    unregistered = await access.issue(client, tokens[0]["access_token"])
    access.expect(await client.get(base + "/products", headers=access.authorization(unregistered)), 403)

    async with administrative() as db:
        imported = await import_vademecum(db, SOURCE_BYTES)
        assert isinstance(imported, Ok) and imported.value.status == "imported"
    async with administrative() as db:
        repeated = await import_vademecum(db, SOURCE_BYTES)
        assert isinstance(repeated, Ok) and repeated.value.status == "existing"
        assert repeated.value.dataset_id == imported.value.dataset_id

    with patch.object(dao_vademecum, "activate", new=AsyncMock(side_effect=RuntimeError("Fixture rollback"))):
        async with administrative() as db:
            try:
                await import_vademecum(db, SOURCE_BYTES + b"\n")
            except RuntimeError:
                pass
            else:
                raise AssertionError("Forced import failure succeeded")
    async with administrative() as db:
        assert await db.scalar(text("SELECT count(*) FROM nightingale.vademecum_datasets")) == 1
        assert str(await db.scalar(text("SELECT id FROM nightingale.vademecum_datasets WHERE active"))) == str(imported.value.dataset_id)

    products = base + "/products"
    monographs = base + "/monographs"
    product_id = SOURCE["products"][0]["ef"]
    for installation in (owner, assistant):
        for path in (products, products + "/" + product_id, monographs, monographs + "/abacavir"):
            response = await client.get(path, headers=access.authorization(installation))
            access.expect(response, 200)
            body = response.json()
            assert body["catalog"]["registryCutoffDate"] == "2026-11-03"
            assert body["catalog"]["sourceSha256"] == hashlib.sha256(SOURCE_BYTES).hexdigest()
            assert body["catalog"]["medicalNotice"] == SOURCE["medicalNotice"]
            assert body["catalog"]["schemaVersion"] == "1.0.0"
            for forbidden in ("oficios", "rifRepresentante", "supplementaryIngredientIds", "historicalProducts"):
                assert forbidden not in response.text

    expected_product_searches = {
        "mucofar": product_id,
        "e.f.43.258": product_id,
        "carboximetilcisteina": product_id,
        "carbocisteina": product_id,
        "r05cb03": product_id,
    }
    for query, registration in expected_product_searches.items():
        response = await client.get(products, params={"q": query}, headers=access.authorization(owner))
        access.expect(response, 200)
        assert response.json()["total"] >= 1
        assert registration in {item["registrationNumber"] for item in response.json()["items"]}
    response = await client.get(products, params={"monographId": "carbocisteina"}, headers=access.authorization(owner))
    access.expect(response, 200)
    assert product_id in {item["registrationNumber"] for item in response.json()["items"]}
    response = await client.get(products, params={"q": "mucofar", "page": 2}, headers=access.authorization(owner))
    access.expect(response, 200)
    assert response.json()["items"] == [] and response.json()["total"] == 1

    for query in ("abacavir", "sulfato de abacavir", "j05af"):
        response = await client.get(monographs, params={"q": query}, headers=access.authorization(assistant))
        access.expect(response, 200)
        assert "abacavir" in {item["id"] for item in response.json()["items"]}

    detail = await client.get(products + "/" + product_id, headers=access.authorization(owner))
    assert detail.json()["product"]["canonicalIngredientIds"] == ["carbocisteina"]
    assert detail.json()["product"]["ingredientLinkStatus"] == "complete"
    slash_registration = next(
        product["ef"] for product in SOURCE["products"] if "/" in product["ef"]
    )
    for path_value in (slash_registration, slash_registration.replace("/", "%2F")):
        response = await client.get(
            products + "/" + path_value, headers=access.authorization(owner)
        )
        access.expect(response, 200)
        assert response.json()["product"]["registrationNumber"] == slash_registration
    empty = next(
        product for product in SOURCE["products"]
        if not product["principioActivo"] and not product["monographIds"]
    )
    response = await client.get(products + "/" + empty["ef"], headers=access.authorization(owner))
    access.expect(response, 200)
    assert response.json()["product"]["activeIngredientText"] == ""
    assert response.json()["product"]["monographIds"] == []

    combination = next(product for product in SOURCE["products"] if "productMonographReference" in product)
    response = await client.get(products + "/" + combination["ef"], headers=access.authorization(owner))
    access.expect(response, 200)
    product = response.json()["product"]
    assert product["combinationMonographIds"] == combination["combinationMonographIds"]
    assert product["productReference"]["sources"] == combination["productMonographReference"]["sources"]

    for document in (
        SOURCE["monographs"][0],
        next(item for item in SOURCE["monographs"] if item["id"] == "dutasterida-tamsulosina"),
        next(item for item in SOURCE["monographs"] if not item["atc"]["code"]),
    ):
        response = await client.get(monographs + "/" + document["id"], headers=access.authorization(owner))
        access.expect(response, 200)
        assert response.json()["monograph"] == document
        assert response.json()["monograph"]["review"]["status"] == document["review"]["status"]

    access.expect(await client.get(products + "/missing", headers=access.authorization(owner)), 404)
    access.expect(await client.get(monographs + "/missing", headers=access.authorization(owner)), 404)
    access.expect(await client.get(products + "?unknown=1", headers=access.authorization(owner)), 422)
    access.expect(await client.get(monographs + "?shows=501", headers=access.authorization(owner)), 422)

    async with administrative() as db:
        async with db.begin():
            await db.execute(text("UPDATE nightingale.accounts SET status='inactive' WHERE id=:id"), {"id": account_id})
    access.expect(await client.get(products, headers=access.authorization(owner)), 403)
    async with administrative() as db:
        async with db.begin():
            await db.execute(text("UPDATE nightingale.accounts SET status='active' WHERE id=:id"), {"id": account_id})
            await db.execute(text("UPDATE nightingale.account_memberships SET status='inactive' WHERE account_id=:account AND user_id=:user"), {"account": account_id, "user": UUID(assistant["userId"])})
    access.expect(await client.get(products, headers=access.authorization(assistant)), 404)
    async with administrative() as db:
        async with db.begin():
            await db.execute(text("UPDATE nightingale.account_memberships SET status='active' WHERE account_id=:account AND user_id=:user"), {"account": account_id, "user": UUID(assistant["userId"])})
            await db.execute(text("UPDATE nightingale.account_device_accesses SET status='revoked' WHERE account_id=:account AND device_id=:device"), {"account": account_id, "device": UUID(assistant["deviceId"])})
    access.expect(await client.get(products, headers=access.authorization(assistant)), 403)

    print("Vademecum checks passed: real PostgreSQL/Keycloak, import/idempotency/rollback, four routes for owner/assistant, access rejections, bounded search, links, warnings and complete monographs.")


if __name__ == "__main__":
    asyncio.run(support["main"](check=check_vademecum))
