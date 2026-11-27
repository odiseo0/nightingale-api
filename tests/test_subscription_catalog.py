import asyncio
import runpy
import unittest
from decimal import Decimal
from pathlib import Path
from uuid import uuid7

import asyncpg
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.subscriptions.application.catalog_cases import (
    PlanNotFound,
    PlanRetired,
    VersionConflict,
    create_plan_version,
    list_plans,
    retire_plan,
)
from src.api.subscriptions.domain.plans import PlanRetirementRequest, PlanVersionCreateRequest
from src.core import Err, Ok
from src.core.services.device_tokens import issue_token

ROOT = Path(__file__).resolve().parents[1]
support = runpy.run_path(str(ROOT / "test-support/persistence/check.py"))

SEED = """
    INSERT INTO nightingale.subscription_plans (id,code,name,description) VALUES
        ('019c1000-0000-7000-8000-000000000001','independent','Médico independiente','Fixture'),
        ('019c1000-0000-7000-8000-000000000002','small_practice','Consultorio pequeño','Fixture'),
        ('019c1000-0000-7000-8000-000000000003','medical_center','Centro médico','Fixture');
    INSERT INTO nightingale.subscription_plan_versions
        (id,plan_id,version,seat_limit,price_30d_usd,price_year_usd) VALUES
        ('019c1000-0000-7000-8000-000000000011','019c1000-0000-7000-8000-000000000001',1,2,18.00,100.00),
        ('019c1000-0000-7000-8000-000000000012','019c1000-0000-7000-8000-000000000002',1,5,24.00,240.00),
        ('019c1000-0000-7000-8000-000000000013','019c1000-0000-7000-8000-000000000003',1,20,75.00,500.00);
"""


class SubscriptionCatalogTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        asyncio.run(cls._prepare())

    @classmethod
    async def _prepare(cls):
        await support["prepare_database"]()
        result = support["migrate"]("upgrade", "head")
        assert result.returncode == 0, result.stderr or result.stdout

    @classmethod
    def tearDownClass(cls):
        async def drop():
            admin = await support["connect_admin"]()
            try:
                await admin.execute(
                    f'DROP DATABASE IF EXISTS "{support["DATABASE"]}" WITH (FORCE)'
                )
            finally:
                await admin.close()

        asyncio.run(drop())

    async def asyncSetUp(self):
        url = support["database_url"]("nightingale_app", support["APP_PASSWORD"])
        self.engine = create_async_engine(url)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        self.admin = await asyncpg.connect(
            host="127.0.0.1", port=55433, user="nightingale_fixture",
            password="Fixture-postgres-only-2026!", database=support["DATABASE"], timeout=10,
        )
        await self.admin.execute(f"""
            TRUNCATE nightingale.subscription_periods, nightingale.subscription_reviews,
                     nightingale.payment_report_evidence, nightingale.payment_reports,
                     nightingale.bcv_exchange_rates, nightingale.platform_operator_credentials,
                     nightingale.platform_operators, nightingale.account_subscriptions,
                     nightingale.subscription_plan_versions, nightingale.subscription_plans
                     CASCADE;
            {SEED}
        """)

        # One operator with the catalog action and one without it.
        self.catalog_token, self.review_token = await self._operators()

    async def _operators(self):
        tokens = {}
        for subject, actions in (("catalog-op", ["catalog"]), ("review-op", ["review"])):
            token_id, secret, digest = issue_token()
            await self.admin.execute(f"""
                INSERT INTO nightingale.platform_operators
                    (id,oidc_issuer,oidc_subject,display_name,actions)
                VALUES ('{uuid7()}','fixture','{subject}','{subject}',ARRAY{actions});
                INSERT INTO nightingale.platform_operator_credentials (id,operator_id,token_hash)
                SELECT '{uuid7()}', id, '{digest.hex()}'
                FROM nightingale.platform_operators WHERE oidc_subject='{subject}';
            """)
            tokens[subject] = secret

        return tokens["catalog-op"], tokens["review-op"]

    async def asyncTearDown(self):
        await self.admin.close()
        await self.engine.dispose()

    def version_payload(self, expected=1, seats=3, p30="20.00", pyear="200.00"):
        return PlanVersionCreateRequest(
            operation_id=uuid7(),
            expected_version=expected,
            seat_limit=seats,
            price_30d_usd=Decimal(p30),
            price_year_usd=Decimal(pyear),
        )

    async def test_authentication_and_action_are_required(self):
        async with self.sessions() as db:
            for token, error in ((None, "InvalidCredential"), ("ngt_bad", "InvalidCredential")):
                result = await list_plans(db, token)
                self.assertIsInstance(result, Err)
                self.assertEqual(type(result.error).__name__, error)

            denied = await list_plans(db, self.review_token)
            self.assertIsInstance(denied, Err)
            self.assertEqual(type(denied.error).__name__, "AccessDenied")

    async def test_catalog_lists_the_seeded_plans_with_history(self):
        async with self.sessions() as db:
            result = await list_plans(db, self.catalog_token)
            self.assertIsInstance(result, Ok)
            page = result.value
            self.assertEqual(page.total, 3)
            by_code = {plan.code: plan for plan in page.items}
            self.assertEqual(by_code["independent"].versions[0].seat_limit, 2)
            self.assertEqual(by_code["small_practice"].versions[0].price_30d_usd, Decimal("24.00"))
            self.assertEqual(by_code["medical_center"].versions[0].price_year_usd, Decimal("500.00"))

    async def test_new_version_preserves_history(self):
        async with self.sessions() as db:
            result = await create_plan_version(
                db, self.catalog_token, "independent", self.version_payload()
            )
            self.assertIsInstance(result, Ok)
            plan = result.value.plan
            self.assertEqual(plan.version, 2)
            self.assertEqual([v.version for v in plan.versions], [1, 2])
            # The historical version 1 keeps its D21 values.
            self.assertEqual(plan.versions[0].price_30d_usd, Decimal("18.00"))
            self.assertEqual(plan.versions[1].price_30d_usd, Decimal("20.00"))

            stale = await create_plan_version(
                db, self.catalog_token, "independent", self.version_payload(expected=1)
            )
            self.assertIsInstance(stale, Err)
            self.assertIsInstance(stale.error, VersionConflict)

            missing = await create_plan_version(
                db, self.catalog_token, "unknown", self.version_payload()
            )
            self.assertIsInstance(missing.error, PlanNotFound)

    async def test_retirement_keeps_history_and_blocks_new_versions(self):
        async with self.sessions() as db:
            result = await retire_plan(
                db,
                self.catalog_token,
                "medical_center",
                PlanRetirementRequest(operation_id=uuid7(), expected_version=1),
            )
            self.assertIsInstance(result, Ok)
            self.assertEqual(result.value.plan.status, "retired")
            self.assertEqual(len(result.value.plan.versions), 1)

            blocked = await create_plan_version(
                db, self.catalog_token, "medical_center", self.version_payload()
            )
            self.assertIsInstance(blocked.error, PlanRetired)

            listed = await list_plans(db, self.catalog_token)
            retired = {p.code: p for p in listed.value.items}["medical_center"]
            self.assertEqual(retired.status, "retired")
            self.assertEqual(retired.versions[0].price_year_usd, Decimal("500.00"))


if __name__ == "__main__":
    unittest.main()
