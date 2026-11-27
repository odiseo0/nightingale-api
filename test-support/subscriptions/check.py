import asyncio
import os
import runpy
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from uuid import uuid7

import httpx

ROOT = Path(__file__).resolve().parents[2]
postgres = SimpleNamespace(**runpy.run_path(str(ROOT / "test-support/persistence/check.py")))
access = SimpleNamespace(**runpy.run_path(str(ROOT / "test-support/access/check.py")))
oidc = access.oidc
CERTIFICATE = access.CERTIFICATE

PNG = b"\x89PNG\r\n\x1a\n" + b"fixture-capture" * 8


def payload(operation_id, **overrides):
    body = {
        "operationId": str(operation_id),
        "planCode": "independent",
        "periodicity": "days_30",
        "declaredPaidOn": "2026-11-20",
        "declaredAmount": {"amount": "18.00", "currency": "USD"},
        "declaredMethod": "transferencia ficticia",
        "declaredReferenceLast4": "0071",
    }
    body.update(overrides)
    return body


async def check_submissions(client, factory, administrative, tokens):
    owner, assistant, outsider = tokens
    owner_device = await access.issue(client, owner["access_token"])
    assistant_device = await access.issue(client, assistant["access_token"])
    outsider_device = await access.issue(client, outsider["access_token"])
    owner_headers = access.authorization(owner_device)

    # The owner's account is created through the real bootstrap case.
    from src.api.accounts.application.accounts_cases import bootstrap_practice
    from src.api.accounts.domain.accounts import BootstrapPracticeInput
    from src.api.authorization.application.authorization_cases import identified_users
    from src.core import Ok
    from uuid import UUID

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
    account_id = str(result.value.account_id)

    base = f"/v1/accounts/{account_id}/subscription/reports"
    account_base = f"/v1/accounts/{account_id}"

    async def register_device(actor):
        response = await client.post(
            account_base + "/sync/operations",
            headers=access.authorization(actor),
            json={"operations": [{
                "operationId": str(uuid7()), "contractVersion": 1,
                "action": "RegisterAccountDevice", "entityKey": actor["deviceId"],
                "expectedVersion": 0, "payload": {},
            }]},
        )
        access.expect(response, 200)
        assert response.json()["results"][0]["status"] == "accepted"

    await register_device(owner_device)

    # The assistant joins through the real invitation flow.
    key = uuid7()
    invited = await client.post(
        f"/v1/accounts/{account_id}/sync/operations",
        headers=access.authorization(owner_device),
        json={"operations": [{
            "operationId": str(uuid7()), "contractVersion": 1, "action": "CreateInvitation",
            "entityKey": str(key), "expectedVersion": 0,
            "payload": {"inviteeUserId": assistant_device["userId"]},
        }]},
    )
    access.expect(invited, 200)
    assert invited.json()["results"][0]["status"] == "accepted"

    accepted = await client.post(
        f"/v1/me/invitations/{key}/accept",
        headers=access.authorization(assistant_device),
        json={"operationId": str(uuid7())},
    )
    access.expect(accepted, 200)
    await register_device(assistant_device)

    # The assistant has a registered device but no subscription permission.
    expect = access.expect
    operation_id = uuid7()
    expect(await client.post(base, json=payload(operation_id),
                             headers=access.authorization(assistant_device)), 403)
    expect(await client.post(base, json=payload(uuid7()),
                             headers=access.authorization(outsider_device)), 404)

    # Submitting leaves the report pending and activates nothing.
    created = await client.post(base, json=payload(operation_id), headers=owner_headers)
    expect(created, 201)
    report = created.json()
    assert report["status"] == "pending" and report["reportId"] == str(operation_id)
    assert report["declared"]["referenceLast4"] == "0071"
    assert report["evidence"] is None

    # A lost response recovers the same report; different content conflicts.
    again = await client.post(base, json=payload(operation_id), headers=owner_headers)
    expect(again, 201)
    assert again.json()["reportId"] == report["reportId"]
    conflict = await client.post(
        base, json=payload(operation_id, declaredMethod="otro método ficticio"),
        headers=owner_headers,
    )
    expect(conflict, 409)

    async with factory() as db:
        from sqlalchemy import text

        counts = await db.execute(text(
            "SELECT (SELECT count(*) FROM nightingale.payment_reports),"
            " (SELECT count(*) FROM nightingale.subscription_periods),"
            " (SELECT status FROM nightingale.account_subscriptions "
            f" WHERE account_id='{account_id}')"
        ))
        reports, periods, status = counts.one()
        assert reports == 1 and periods == 0 and status == "pending_activation"

    # Owner lists and reads only their own reports.
    listed = await client.get(base, headers=owner_headers)
    expect(listed, 200)
    assert listed.json()["total"] == 1
    detail = await client.get(f"{base}/{operation_id}", headers=owner_headers)
    expect(detail, 200)
    assert detail.json()["review"] is None
    other_account = str(uuid7())
    expect(await client.get(
        f"/v1/accounts/{other_account}/subscription/reports/{operation_id}",
        headers=owner_headers,
    ), 404)

    # Evidence: real signature first, then one capture per report, private download.
    forged = await client.post(
        f"{base}/{operation_id}/evidence",
        files={"file": ("captura.png", b"GIF89a-forged", "image/png")},
        headers=owner_headers,
    )
    expect(forged, 422)
    uploaded = await client.post(
        f"{base}/{operation_id}/evidence",
        files={"file": ("captura.png", PNG, "image/png")},
        headers=owner_headers,
    )
    expect(uploaded, 201)
    duplicate = await client.post(
        f"{base}/{operation_id}/evidence",
        files={"file": ("captura.png", PNG, "image/png")},
        headers=owner_headers,
    )
    expect(duplicate, 409)

    download = await client.get(f"{base}/{operation_id}/evidence", headers=owner_headers)
    expect(download, 200)
    assert download.content == PNG and download.headers["content-type"] == "image/png"
    assert download.headers["cache-control"] == "no-store"
    expect(await client.get(f"{base}/{operation_id}/evidence",
                            headers=access.authorization(assistant_device)), 403)

    detail = await client.get(f"{base}/{operation_id}", headers=owner_headers)
    assert detail.json()["evidence"]["sizeBytes"] == len(PNG)
    assert "storageKey" not in detail.text and "storage_key" not in detail.text

    # Operator tray: review action required, evidence re-authorized per request.
    from sqlalchemy import text
    from src.core.services.device_tokens import issue_token

    async def make_operator(actions):
        token_id, secret, digest = issue_token()
        async with administrative() as db:
            operator_id = str(uuid7())
            await db.execute(text(
                "INSERT INTO nightingale.platform_operators "
                "(id,oidc_issuer,oidc_subject,display_name,actions) VALUES "
                f"('{operator_id}','fixture','op-{operator_id}','op',ARRAY{actions})"
            ))
            await db.execute(text(
                "INSERT INTO nightingale.platform_operator_credentials (id,operator_id,token_hash) "
                f"VALUES ('{uuid7()}','{operator_id}','{digest.hex()}')"
            ))
            await db.commit()
        return {"Authorization": f"Bearer {secret}"}, operator_id

    reviewer, reviewer_id = await make_operator(["review"])
    catalog_only, _ = await make_operator(["catalog"])

    expect(await client.get("/v1/operator/payment-reports"), 401)
    expect(await client.get("/v1/operator/payment-reports",
                            headers=catalog_only), 403)

    tray = await client.get("/v1/operator/payment-reports?status=pending", headers=reviewer)
    expect(tray, 200)
    assert tray.json()["total"] == 1
    assert tray.json()["items"][0]["reportId"] == str(operation_id)
    assert tray.json()["items"][0]["accountId"] == account_id

    filtered = await client.get(
        f"/v1/operator/payment-reports?accountId={uuid7()}", headers=reviewer
    )
    assert filtered.json()["total"] == 0

    operator_detail = await client.get(
        f"/v1/operator/payment-reports/{operation_id}", headers=reviewer
    )
    expect(operator_detail, 200)
    body = operator_detail.json()
    assert body["declared"]["method"] == "transferencia ficticia"
    assert body["evidence"]["sha256"] is not None
    assert "storageKey" not in operator_detail.text

    operator_download = await client.get(
        f"/v1/operator/payment-reports/{operation_id}/evidence", headers=reviewer
    )
    expect(operator_download, 200)
    assert operator_download.content == PNG
    assert operator_download.headers["cache-control"] == "no-store"

    # Approval: mismatch first, then one atomic approval with a unique period.
    approval_base = f"/v1/operator/payment-reports/{operation_id}/approval"

    def approval_body(operation, amount="18.00", currency="USD", expected=1):
        return {
            "operationId": str(operation), "expectedVersion": expected,
            "verifiedPaidOn": "2026-11-20", "verifiedAmount": amount,
            "verifiedCurrency": currency,
        }

    mismatch = await client.post(approval_base, json=approval_body(uuid7(), "17.99"),
                                 headers=reviewer)
    expect(mismatch, 422)

    approval_operation = uuid7()
    approved = await client.post(approval_base, json=approval_body(approval_operation),
                                 headers=reviewer)
    expect(approved, 200)
    result = approved.json()
    assert result["grantedPeriod"]["sequence"] == 1
    assert result["subscription"]["status"] == "active"
    assert result["duplicate"] is False

    # A lost approval response recovers the same decision without a second period.
    duplicate = await client.post(approval_base, json=approval_body(approval_operation),
                                  headers=reviewer)
    expect(duplicate, 200)
    assert duplicate.json()["duplicate"] is True
    assert duplicate.json()["grantedPeriod"]["sequence"] == 1

    second = await client.post(approval_base, json=approval_body(uuid7()), headers=reviewer)
    expect(second, 409)

    async with administrative() as db:
        row = (await db.execute(text(
            "SELECT (SELECT count(*) FROM nightingale.subscription_periods),"
            " (SELECT count(*) FROM nightingale.subscription_reviews),"
            " (SELECT count(*) FROM nightingale.audit_events "
            "  WHERE action='ApprovePaymentReport' AND outcome='accepted')"
        ))).one()
        assert tuple(row) == (1, 1, 1), row

    # Owner sees the granted period on their own report.
    owner_detail = await client.get(f"{base}/{operation_id}", headers=owner_headers)
    review = owner_detail.json()["review"]
    assert review["decision"] == "approved" and review["grantedPeriod"]["sequence"] == 1

    # Two operators racing on a new report: exactly one approval wins.
    race_operation = uuid7()
    race_report = await client.post(base, json=payload(race_operation, periodicity="year_1",
                                                       declaredAmount={"amount": "100.00", "currency": "USD"}),
                                    headers=owner_headers)
    expect(race_report, 201)
    race_base = f"/v1/operator/payment-reports/{race_operation}/approval"
    racer, _ = await make_operator(["review"])
    responses = await asyncio.gather(
        client.post(race_base, json=approval_body(uuid7(), "100.00"), headers=reviewer),
        client.post(race_base, json=approval_body(uuid7(), "100.00"), headers=racer),
    )
    assert sorted(response.status_code for response in responses) == [200, 409], [
        response.status_code for response in responses
    ]
    async with administrative() as db:
        periods = await db.scalar(text("SELECT count(*) FROM nightingale.subscription_periods"))
        assert periods == 2, periods

    # Rejection: keeps the previous state, records a safe reason, never a period.
    rejected_operation = uuid7()
    rejected_report = await client.post(base, json=payload(rejected_operation), headers=owner_headers)
    expect(rejected_report, 201)
    rejection_base = f"/v1/operator/payment-reports/{rejected_operation}/rejection"

    stale = await client.post(rejection_base, json={
        "operationId": str(uuid7()), "expectedVersion": 99, "reason": "fixture",
    }, headers=reviewer)
    expect(stale, 409)

    rejection_operation = uuid7()
    rejected = await client.post(rejection_base, json={
        "operationId": str(rejection_operation), "expectedVersion": 1,
        "reason": "referencia no verificable",
    }, headers=reviewer)
    expect(rejected, 200)
    assert rejected.json()["decision"] == "rejected"

    again = await client.post(rejection_base, json={
        "operationId": str(rejection_operation), "expectedVersion": 1,
        "reason": "referencia no verificable",
    }, headers=reviewer)
    expect(again, 200)
    assert again.json()["duplicate"] is True

    owner_rejected = await client.get(f"{base}/{rejected_operation}", headers=owner_headers)
    review = owner_rejected.json()["review"]
    assert review["decision"] == "rejected" and review["reason"] == "referencia no verificable"
    assert review["grantedPeriod"] is None

    # The resubmission links the rejected original and can be approved exactly once.
    resubmission_operation = uuid7()
    resubmitted = await client.post(base, json=payload(
        resubmission_operation, previousReportId=str(rejected_operation),
    ), headers=owner_headers)
    expect(resubmitted, 201)
    assert resubmitted.json()["previousReportId"] == str(rejected_operation)
    assert resubmitted.json()["status"] == "pending"

    original = await client.get(f"{base}/{rejected_operation}", headers=owner_headers)
    assert original.json()["status"] == "rejected"

    resubmission_approval = await client.post(
        f"/v1/operator/payment-reports/{resubmission_operation}/approval",
        json=approval_body(uuid7()), headers=reviewer,
    )
    expect(resubmission_approval, 200)
    assert resubmission_approval.json()["grantedPeriod"]["sequence"] == 3

    # Account subscription read, plan change and cancellation (D24, §16.3).
    subscription_url = f"{account_base}/subscription"
    state = await client.get(subscription_url, headers=owner_headers)
    expect(state, 200)
    body = state.json()
    assert body["plan"]["code"] == "independent" and body["status"] == "active"
    assert body["seats"] == {"used": 2, "limit": 2}
    expect(await client.get(subscription_url,
                            headers=access.authorization(assistant_device)), 403)

    stale_change = await client.post(subscription_url + "/plan-changes", json={
        "operationId": str(uuid7()), "expectedVersion": 99, "planCode": "small_practice",
    }, headers=owner_headers)
    expect(stale_change, 409)

    changed = await client.post(subscription_url + "/plan-changes", json={
        "operationId": str(uuid7()),
        "expectedVersion": body["subscriptionVersion"],
        "planCode": "small_practice",
    }, headers=owner_headers)
    expect(changed, 200)
    assert changed.json()["plan"]["code"] == "small_practice"
    assert changed.json()["seats"]["limit"] == 5

    cancelled = await client.post(subscription_url + "/cancellation", json={
        "operationId": str(uuid7()),
        "expectedVersion": changed.json()["subscriptionVersion"],
    }, headers=owner_headers)
    expect(cancelled, 200)
    # Paid time continues after cancellation (§16.3).
    assert cancelled.json()["status"] == "active"
    assert cancelled.json()["currentPeriod"] is not None

    # A revoked operator loses access even with the same credential.
    async with administrative() as db:
        await db.execute(text(
            "UPDATE nightingale.platform_operators SET status='revoked' "
            f"WHERE id='{reviewer_id}'"
        ))
        await db.commit()
    expect(await client.get("/v1/operator/payment-reports", headers=reviewer), 403)


async def main():
    realm = __import__("json").loads((ROOT / "test-support/oidc/realm.json").read_text())
    tokens = [access.provider_tokens(user) for user in realm["users"]]
    try:
        await postgres.prepare_database()
        result = postgres.migrate("upgrade", "head")
        assert result.returncode == 0, "Subscriptions migrations failed"
        with TemporaryDirectory(prefix="subscriptions-", dir=ROOT / ".tmp") as temporary:
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
            })
            sys.path.insert(0, str(ROOT))
            previous_directory = Path.cwd()
            os.chdir(directory)
            from src.application import app
            from src.core.db.session import async_session_factory, engine



            try:
                from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

                admin_engine = create_async_engine(
                    postgres.database_url("nightingale_migrator", postgres.MIGRATOR_PASSWORD)
                )
                administrative = async_sessionmaker(admin_engine, expire_on_commit=False)

                try:
                    async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://fixture") as client:
                        await check_submissions(client, async_session_factory, administrative, tokens)
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

    print("Subscriptions checks passed: submit stays pending, lost response recovers one report, "
          "assistant/outsider denied, evidence signature/size/single-capture rules and private "
          "download; operator tray requires the review action, filters by account, shows no "
          "storage keys and a revoked operator loses access.")


if __name__ == "__main__":
    asyncio.run(main())
