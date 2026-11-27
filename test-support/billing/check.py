import asyncio
import os
import runpy
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from uuid import UUID, uuid7

import httpx
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
postgres = SimpleNamespace(**runpy.run_path(str(ROOT / "test-support/persistence/check.py")))
access = SimpleNamespace(**runpy.run_path(str(ROOT / "test-support/access/check.py")))
oidc = access.oidc
CERTIFICATE = access.CERTIFICATE

PNG = b"\x89PNG\r\n\x1a\n" + b"fixture-capture" * 8


async def check_patient_billing(client, administrative, tokens):
    owner = tokens[0]
    owner_device = await access.issue(client, owner["access_token"])
    owner_headers = access.authorization(owner_device)

    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.authorization.application.authorization_cases import identified_users
    from src.core import Ok

    async with administrative() as db:
        users = await identified_users(db, [UUID(owner_device["userId"])])
    identity = users[UUID(owner_device["userId"])]
    data = BootstrapPracticeInput(
        owner_issuer=identity.oidc_issuer, owner_subject=identity.oidc_subject,
        owner_name="Fixture Owner", professional_name="Fixture Professional",
        display_name="Fixture Practice", time_zone="America/Caracas",
        location_name="Fixture Office", location_address="Fictional address",
        location_country="VE", location_state="Fixture State", location_city="Fixture City",
    )
    async with administrative() as db:
        result = await bootstrap_practice(db, data)
    assert isinstance(result, Ok)
    account_id = result.value.account_id

    response = await client.post(
        f"/v1/accounts/{account_id}/sync/operations",
        headers=owner_headers,
        json={"operations": [{
            "operationId": str(uuid7()), "contractVersion": 1,
            "action": "RegisterAccountDevice", "entityKey": owner_device["deviceId"],
            "expectedVersion": 0, "payload": {},
        }]},
    )
    access.expect(response, 200)
    assert response.json()["results"][0]["status"] == "accepted"

    professional_id = result.value.professional_id

    async def batch(operations):
        sent = await client.post(
            f"/v1/accounts/{account_id}/sync/operations",
            headers=owner_headers, json={"operations": operations},
        )
        access.expect(sent, 200)
        return sent.json()["results"]

    def op(action, key, expected, payload):
        return {"operationId": str(uuid7()), "contractVersion": 1, "action": action,
                "entityKey": str(key) if isinstance(key, UUID) else
                {name: str(value) for name, value in key.items()},
                "expectedVersion": expected, "payload": payload}

    # Fictitious patient with one issued and one draft charge (SQL fixtures only).
    patient_id, charge_id, draft_id = uuid7(), uuid7(), uuid7()
    async with administrative() as db, db.begin():
        await db.execute(text("""
            INSERT INTO nightingale.patients (id) VALUES (:patient)
        """), {"patient": patient_id})
        await db.execute(text("""
            INSERT INTO nightingale.account_patients (account_id,patient_id,full_name)
            VALUES (:account,:patient,'Paciente ficticio')
        """), {"account": account_id, "patient": patient_id})
        for key, status, issued in ((charge_id, "issued", "'2026-11-27T15:00:00Z'"),
                                    (draft_id, "draft", "NULL")):
            await db.execute(text(f"""
                INSERT INTO nightingale.patient_charges
                    (id,account_id,patient_id,description,amount,currency,price_source,
                     status,issued_at,created_by)
                VALUES (:id,:account,:patient,'Consulta ficticia',100.00,'USD','base',
                        '{status}',{issued},:actor)
            """), {"id": key, "account": account_id, "patient": patient_id,
                   "actor": UUID(owner_device["userId"])})

    grants = f"/v1/accounts/{account_id}/billing/grants"
    reports = "/v1/patient/billing/reports"

    # Offline drafts (D28): charge operations travel in the batch, are
    # revalidated at acceptance (current price) and are idempotent by receipt.
    service_id = uuid7()
    catalog = await batch([
        op("CreateService", service_id, 0, {
            "professionalId": str(professional_id), "name": "Consulta ficticia",
            "defaultDurationMinutes": 30}),
        op("OfferService", {"professionalId": professional_id,
                            "serviceId": service_id}, 0, {}),
        op("SetServicePrice", service_id, 0, {"amount": "18.00", "currency": "USD"}),
    ])
    assert all(item["status"] == "accepted" for item in catalog), catalog

    # Prepared while offline; the catalog price changes before it is sent.
    offline_charge = uuid7()
    draft_op = op("CreatePatientCharge", offline_charge, 0, {
        "patientId": str(patient_id), "serviceId": str(service_id)})
    reprice = await batch([op("SetServicePrice", service_id, 1,
                              {"amount": "20.00", "currency": "USD"})])
    assert reprice[0]["status"] == "accepted", reprice

    sent = await batch([draft_op])
    assert sent[0]["status"] == "accepted", sent
    # A lost response retried with the same operation id recovers the result.
    resent = await batch([draft_op])
    assert resent[0]["status"] == "duplicate", resent
    assert resent[0]["state"] == sent[0]["state"]

    stored = await client.get(
        f"/v1/accounts/{account_id}/billing/charges/{offline_charge}",
        headers=owner_headers,
    )
    access.expect(stored, 200)
    assert stored.json()["amount"] == "20.00", stored.json()
    assert stored.json()["status"] == "draft"
    charges_count = await client.get(
        f"/v1/accounts/{account_id}/billing/charges?patientId={patient_id}&status=draft",
        headers=owner_headers,
    )
    assert charges_count.json()["total"] == 2, charges_count.json()  # SQL draft + batch one

    # Grant issuance needs the review grant; the owner always passes.
    grant_operation = uuid7()
    issued_grant = await client.post(grants, headers=owner_headers, json={
        "operationId": str(grant_operation), "patientId": str(patient_id),
        "chargeId": str(charge_id),
        "actions": ["read_charge", "submit_report", "read_result"],
    })
    access.expect(issued_grant, 201)
    secret = issued_grant.json()["secret"]
    assert secret and issued_grant.json()["duplicate"] is False

    retry = await client.post(grants, headers=owner_headers, json={
        "operationId": str(grant_operation), "patientId": str(patient_id),
        "chargeId": str(charge_id),
        "actions": ["read_charge", "submit_report", "read_result"],
    })
    access.expect(retry, 201)
    assert retry.json()["duplicate"] is True and retry.json()["secret"] is None

    patient_headers = {"Authorization": f"Bearer {secret}"}

    # The valid link reads only its charge; drafts never appear.
    view = await client.get("/v1/patient/billing/charge", headers=patient_headers)
    access.expect(view, 200)
    items = view.json()["items"]
    assert len(items) == 1 and items[0]["chargeId"] == str(charge_id)
    assert items[0]["outstanding"] == "100.00"

    # Invalid links are a uniform 404 that never confirms existence (D28).
    outsider = {"Authorization": "Bearer " + "0" * 64}
    access.expect(await client.get("/v1/patient/billing/charge", headers=outsider), 404)
    access.expect(await client.get("/v1/patient/billing/charge"), 404)

    def report_form(operation_id, **overrides):
        form = {
            "operationId": str(operation_id), "chargeId": str(charge_id),
            "paidOn": "2026-11-26", "amount": "40.00", "currency": "USD",
            "method": "transferencia ficticia", "referenceLast4": "0071",
        }
        form.update(overrides)
        return form

    # The capture is mandatory and validated by its real signature.
    rejected = await client.post(
        reports, headers=patient_headers, data=report_form(uuid7()),
        files={"capture": ("capture.gif", b"GIF89a-no", "image/gif")},
    )
    access.expect(rejected, 422)

    # Submission stays pending, stores one capture and never changes the balance.
    operation_id = uuid7()
    created = await client.post(
        reports, headers=patient_headers, data=report_form(operation_id),
        files={"capture": ("capture.png", PNG, "image/png")},
    )
    assert created.status_code == 201, created.text
    assert created.json()["status"] == "pending"
    assert created.json()["duplicate"] is False

    after = await client.get("/v1/patient/billing/charge", headers=patient_headers)
    assert after.json()["items"][0]["outstanding"] == "100.00"

    # A lost response recovers the same report without duplicating capture.
    again = await client.post(
        reports, headers=patient_headers, data=report_form(operation_id),
        files={"capture": ("capture.png", PNG, "image/png")},
    )
    access.expect(again, 201)
    assert again.json()["duplicate"] is True
    listed = await client.get(reports, headers=patient_headers)
    access.expect(listed, 200)
    assert listed.json()["total"] == 1

    detail = await client.get(f"{reports}/{operation_id}", headers=patient_headers)
    access.expect(detail, 200)
    assert detail.json()["result"] is None
    access.expect(
        await client.get(f"{reports}/{uuid7()}", headers=patient_headers), 404
    )

    # A charge outside the grant scope is a uniform absence.
    foreign = await client.post(
        reports, headers=patient_headers, data=report_form(uuid7(), chargeId=str(draft_id)),
        files={"capture": ("capture.png", PNG, "image/png")},
    )
    access.expect(foreign, 404)

    # The review tray requires the explicit billing_review grant (D27): the
    # owner passes, an assistant without it gets 403 and no clinical access is
    # derived from reviewing.
    tray = f"/v1/accounts/{account_id}/billing/reports"
    pending = await client.get(tray, headers=owner_headers)
    access.expect(pending, 200)
    assert pending.json()["total"] == 1
    assert pending.json()["items"][0]["reportId"] == str(operation_id)

    detail = await client.get(f"{tray}/{operation_id}", headers=owner_headers)
    access.expect(detail, 200)
    assert detail.json()["evidence"]["contentType"] == "image/png"
    assert "storageKey" not in detail.text

    download = await client.get(f"{tray}/{operation_id}/evidence", headers=owner_headers)
    access.expect(download, 200)
    assert download.content == PNG
    assert "storage" not in download.headers.get("content-disposition", "")

    assistant_device = await access.issue(client, tokens[1]["access_token"])
    key = uuid7()
    invited = await client.post(
        f"/v1/accounts/{account_id}/sync/operations",
        headers=owner_headers,
        json={"operations": [{
            "operationId": str(uuid7()), "contractVersion": 1, "action": "CreateInvitation",
            "entityKey": str(key), "expectedVersion": 0,
            "payload": {"inviteeUserId": assistant_device["userId"]},
        }]},
    )
    access.expect(invited, 200)
    accepted = await client.post(
        f"/v1/me/invitations/{key}/accept",
        headers=access.authorization(assistant_device),
        json={"operationId": str(uuid7())},
    )
    access.expect(accepted, 200)
    registered = await client.post(
        f"/v1/accounts/{account_id}/sync/operations",
        headers=access.authorization(assistant_device),
        json={"operations": [{
            "operationId": str(uuid7()), "contractVersion": 1,
            "action": "RegisterAccountDevice", "entityKey": assistant_device["deviceId"],
            "expectedVersion": 0, "payload": {},
        }]},
    )
    access.expect(registered, 200)
    assistant_headers = access.authorization(assistant_device)
    access.expect(await client.get(tray, headers=assistant_headers), 403)
    access.expect(await client.get(f"{tray}/{operation_id}", headers=assistant_headers), 403)
    access.expect(
        await client.get(f"{tray}/{operation_id}/evidence", headers=assistant_headers), 403
    )

    # Atomic approval: one payment, balance updated once, retry loses with 409.
    approval_body = {
        "operationId": str(uuid7()), "expectedVersion": 1,
        "verifiedPaidOn": "2026-11-26", "verifiedAmount": "40.00",
        "verifiedCurrency": "USD", "method": "transferencia ficticia",
    }
    approved = await client.post(
        f"{tray}/{operation_id}/approval", headers=owner_headers, json=approval_body
    )
    access.expect(approved, 200)
    assert approved.json()["balance"]["paid"] == "40.00"
    assert approved.json()["balance"]["state"] == "partially_paid"
    duplicate = await client.post(
        f"{tray}/{operation_id}/approval", headers=owner_headers, json=approval_body
    )
    access.expect(duplicate, 409)
    access.expect(await client.get(tray, headers=assistant_headers), 403)

    # The patient sees the visible result, never the internal review data.
    result = await client.get(f"{reports}/{operation_id}", headers=patient_headers)
    access.expect(result, 200)
    assert result.json()["status"] == "approved"
    assert result.json()["result"]["paymentAmount"] == "40.00"

    # An excess over the remaining balance is rejected with 422 (D26).
    excess_id = uuid7()
    excess = await client.post(
        reports, headers=patient_headers, data=report_form(excess_id, amount="70.00"),
        files={"capture": ("capture.png", PNG, "image/png")},
    )
    access.expect(excess, 201)
    exceeded = await client.post(
        f"{tray}/{excess_id}/approval", headers=owner_headers,
        json={**approval_body, "operationId": str(uuid7()), "verifiedAmount": "70.00"},
    )
    access.expect(exceeded, 422)
    still = await client.get("/v1/patient/billing/charge", headers=patient_headers)
    assert still.json()["items"][0]["outstanding"] == "60.00"

    # Rejection keeps balance and evidence, and allows a chained resubmission.
    rejected = await client.post(
        f"{tray}/{excess_id}/rejection", headers=owner_headers,
        json={"operationId": str(uuid7()), "expectedVersion": 1,
              "reason": "importe excedente ficticio"},
    )
    access.expect(rejected, 200)
    assert rejected.json()["status"] == "rejected"
    access.expect(await client.post(
        f"{tray}/{excess_id}/rejection", headers=owner_headers,
        json={"operationId": str(uuid7()), "expectedVersion": 2, "reason": "otra"},
    ), 409)
    corrected = await client.post(
        reports, headers=patient_headers,
        data=report_form(uuid7(), amount="60.00", previousReportId=str(excess_id)),
        files={"capture": ("capture.png", PNG, "image/png")},
    )
    access.expect(corrected, 201)
    assert corrected.json()["previousReportId"] == str(excess_id)

    # Direct staff payment (staff_entry) with its own origin, same balance rules.
    direct = await client.post(
        f"/v1/accounts/{account_id}/billing/charges/{charge_id}/payments",
        headers=owner_headers,
        json={"operationId": str(uuid7()), "expectedVersion": 1,
              "paidOn": "2026-11-27", "amount": "60.00", "currency": "USD",
              "method": "efectivo ficticio",
              "evidenceNote": "recibo interno ficticio 7"},
    )
    access.expect(direct, 201)
    assert direct.json()["origin"] == "staff_entry"
    assert direct.json()["balance"]["state"] == "paid"
    access.expect(await client.post(
        f"/v1/accounts/{account_id}/billing/charges/{charge_id}/payments",
        headers=owner_headers,
        json={"operationId": str(uuid7()), "expectedVersion": 1,
              "paidOn": "2026-11-27", "amount": "1.00", "currency": "USD",
              "method": "efectivo ficticio", "evidenceNote": "excedente ficticio"},
    ), 422)

    # Annulment excludes the payment from the active balance without deleting
    # history and never affirms a refund (D27).
    annulled = await client.post(
        f"/v1/accounts/{account_id}/billing/payments/{direct.json()['paymentId']}/annulment",
        headers=owner_headers,
        json={"operationId": str(uuid7()), "expectedVersion": 1,
              "reason": "registro duplicado ficticio"},
    )
    access.expect(annulled, 200)
    assert annulled.json()["status"] == "annulled"
    assert annulled.json()["balance"]["outstanding"] == "60.00"
    access.expect(await client.post(
        f"/v1/accounts/{account_id}/billing/payments/{direct.json()['paymentId']}/annulment",
        headers=owner_headers,
        json={"operationId": str(uuid7()), "expectedVersion": 2, "reason": "otra"},
    ), 409)

    # Non-fiscal receipt: private PDF for authorized staff; the patient link
    # lacks read_receipt, so it is a uniform 404 (D28).
    receipt = await client.get(
        f"/v1/accounts/{account_id}/billing/payments/{direct.json()['paymentId']}/receipt",
        headers=owner_headers,
    )
    access.expect(receipt, 200)
    assert receipt.headers["content-type"].startswith("application/pdf")
    assert receipt.content.startswith(b"%PDF-1.4")
    assert "storage" not in receipt.headers.get("content-disposition", "")
    access.expect(await client.get(
        f"/v1/patient/billing/payments/{direct.json()['paymentId']}/receipt",
        headers=patient_headers,
    ), 404)

    # Revocation cuts access immediately; the report keeps its history.
    revoked = await client.post(
        f"{grants}/{grant_operation}/revocation", headers=owner_headers
    )
    access.expect(revoked, 200)
    assert revoked.json()["status"] == "revoked"
    access.expect(await client.get(reports, headers=patient_headers), 404)

    async with administrative() as db:
        kept = await db.scalar(text(
            "SELECT count(*) FROM nightingale.patient_payment_reports "
            "WHERE account_id=:account"
        ), {"account": account_id})
    assert kept == 3


async def main():
    realm = __import__("json").loads((ROOT / "test-support/oidc/realm.json").read_text())
    tokens = [access.provider_tokens(user) for user in realm["users"]]
    try:
        await postgres.prepare_database()
        result = postgres.migrate("upgrade", "head")
        assert result.returncode == 0, "Billing migrations failed"
        with TemporaryDirectory(prefix="billing-", dir=ROOT / ".tmp") as temporary:
            directory = Path(temporary).resolve()
            assert directory.is_relative_to(ROOT / ".tmp")
            for name in list(os.environ):
                if name.upper().startswith(("API_", "OIDC_", "DB_", "POOL_")) or name.upper() == "SQLALCHEMY_DATABASE_URI":
                    del os.environ[name]
            os.environ.update({
                "API_ENVIRONMENT": "test",
                "SQLALCHEMY_DATABASE_URI": postgres.database_url("nightingale_app", postgres.APP_PASSWORD),
                "OIDC_ISSUER": oidc.ISSUER,
                "OIDC_JWKS_URI": f"{oidc.ISSUER}/protocol/openid-connect/certs",
                "OIDC_TLS_CA_FILE": str(CERTIFICATE),
                "STORAGE_ROOT": str(directory / "storage"),
            })
            sys.path.insert(0, str(ROOT))
            previous_directory = Path.cwd()
            os.chdir(directory)
            from src.application import app
            from src.core.db.session import engine

            try:
                from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

                admin_engine = create_async_engine(
                    postgres.database_url("nightingale_migrator", postgres.MIGRATOR_PASSWORD)
                )
                administrative = async_sessionmaker(admin_engine, expire_on_commit=False)

                try:
                    async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://fixture") as client:
                        await check_patient_billing(client, administrative, tokens)
                finally:
                    await admin_engine.dispose()
            finally:
                await engine.dispose()
                os.chdir(previous_directory)
    finally:
        admin = await postgres.connect_admin()
        try:
            assert postgres.DATABASE.startswith("nightingale_test_")
            exists = await admin.fetchval(
                "SELECT EXISTS(SELECT FROM pg_database WHERE datname=$1)", postgres.DATABASE
            )
            if exists:
                await admin.execute(f'DROP DATABASE "{postgres.DATABASE}" WITH (FORCE)')
        finally:
            await admin.close()

    print("Billing checks passed: grant secret delivered once with idempotent retry, valid link "
          "reads only its issued charge, invalid links are a uniform 404, capture validated by "
          "real signature, submission stays pending without balance effect, lost response "
          "recovers one report, approval creates a single payment under the balance lock with 409 on "
          "retry and 422 on excess, the review tray and evidence need the explicit review grant "
          "with no storage keys exposed, and revocation cuts access while keeping history.")


if __name__ == "__main__":
    asyncio.run(main())
