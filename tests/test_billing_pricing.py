import asyncio
import runpy
import unittest
from decimal import Decimal
from pathlib import Path

import asyncpg
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.services.application.services_cases import resolve_service_price
from src.api.services.domain.offers import SetServiceOfferPricePayload
from src.api.services.domain.services import SetServicePricePayload
from src.api.services.repository.dao import dao_offer_prices, dao_service_prices

ROOT = Path(__file__).resolve().parents[1]
support = runpy.run_path(str(ROOT / "test-support/persistence/check.py"))

USER_ID = "019c0000-0000-7000-8000-0000000000a1"
ACCOUNT_ID = "019c0000-0000-7000-8000-0000000000a2"
PROFESSIONAL_ID = "019c0000-0000-7000-8000-0000000000b1"
SERVICE_ID = "019c0000-0000-7000-8000-0000000000d1"
OTHER_SERVICE_ID = "019c0000-0000-7000-8000-0000000000d2"


class PricePayloadTests(unittest.TestCase):
    def test_price_payloads_admit_zero_and_two_places(self):
        free = SetServicePricePayload(amount=Decimal("0.00"), currency="USD")
        self.assertEqual(free.amount, Decimal("0.00"))
        offer = SetServiceOfferPricePayload(amount=Decimal("15.00"), currency="VES")
        self.assertEqual(offer.currency, "VES")

    def test_price_payloads_reject_invalid_amounts_and_currencies(self):
        for amount in (Decimal("-0.01"), Decimal("1.001"), Decimal("NaN"), Decimal("Infinity")):
            with self.subTest(amount=amount), self.assertRaises(ValidationError):
                SetServicePricePayload(amount=amount, currency="USD")
        with self.assertRaises(ValidationError):
            SetServicePricePayload(amount=Decimal("1.00"), currency="EUR")
        with self.assertRaises(ValidationError):
            SetServicePricePayload.model_validate(
                {"amount": "1.00", "currency": "USD", "professionalId": str(SERVICE_ID)}
            )


class PriceResolutionTests(unittest.IsolatedAsyncioTestCase):
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
        self.admin = await asyncpg.connect(
            host="127.0.0.1", port=55433, user="nightingale_fixture",
            password="Fixture-postgres-only-2026!", database=support["DATABASE"], timeout=10,
        )
        await self.admin.execute("""
            TRUNCATE nightingale.service_offer_prices, nightingale.service_prices,
                     nightingale.professional_services, nightingale.services,
                     nightingale.account_professionals, nightingale.professionals,
                     nightingale.accounts, nightingale.app_users CASCADE;
        """)
        await self.admin.execute(f"""
            INSERT INTO nightingale.app_users (id,oidc_issuer,oidc_subject,display_name)
            VALUES ('{USER_ID}','fixture','pricing-owner','Fixture');
            INSERT INTO nightingale.accounts
                (id,kind,owner_user_id,display_name,time_zone,location_name,location_address,
                 location_country,location_state,location_city)
            VALUES ('{ACCOUNT_ID}','clinic','{USER_ID}','Fixture','America/Caracas',
                    'Fixture','Fixture','VE','Fixture','Fixture');
            INSERT INTO nightingale.account_memberships (account_id,user_id)
            VALUES ('{ACCOUNT_ID}','{USER_ID}');
            INSERT INTO nightingale.account_sync_heads (account_id,last_sequence)
            VALUES ('{ACCOUNT_ID}',0);
            INSERT INTO nightingale.professionals (id,user_id,public_name)
            VALUES ('{PROFESSIONAL_ID}','{USER_ID}','Profesional ficticio');
            INSERT INTO nightingale.account_professionals (account_id,professional_id,user_id)
            VALUES ('{ACCOUNT_ID}','{PROFESSIONAL_ID}','{USER_ID}');
            INSERT INTO nightingale.services (id,professional_id,name,default_duration_minutes)
            VALUES ('{SERVICE_ID}','{PROFESSIONAL_ID}','Consulta ficticia',30),
                   ('{OTHER_SERVICE_ID}','{PROFESSIONAL_ID}','Curso ficticio',45);
            INSERT INTO nightingale.professional_services (account_id,professional_id,service_id)
            VALUES ('{ACCOUNT_ID}','{PROFESSIONAL_ID}','{SERVICE_ID}'),
                   ('{ACCOUNT_ID}','{PROFESSIONAL_ID}','{OTHER_SERVICE_ID}');
        """)
        self.engine = create_async_engine(
            support["database_url"]("nightingale_app", support["APP_PASSWORD"])
        )
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.engine.dispose()
        await self.admin.close()

    async def test_base_offer_zero_and_null_resolution(self):
        async with self.sessions() as db, db.begin():
            # No rows: «sin precio definido», distinct from a valid zero (D25).
            self.assertIsNone(
                await resolve_service_price(db, ACCOUNT_ID, PROFESSIONAL_ID, SERVICE_ID)
            )

            await dao_service_prices.apply_price(
                db, PROFESSIONAL_ID, SERVICE_ID, Decimal("18.00"), "USD"
            )
            base = await resolve_service_price(db, ACCOUNT_ID, PROFESSIONAL_ID, SERVICE_ID)
            self.assertEqual((base.amount, base.source), (Decimal("18.00"), "base"))

            # The offer price replaces the base for this account.
            await dao_offer_prices.apply_price(
                db, ACCOUNT_ID, PROFESSIONAL_ID, SERVICE_ID, Decimal("15.00"), "USD"
            )
            offer = await resolve_service_price(db, ACCOUNT_ID, PROFESSIONAL_ID, SERVICE_ID)
            self.assertEqual((offer.amount, offer.source), (Decimal("15.00"), "offer"))

            # A free offer overrides a paid base with a valid zero.
            await dao_offer_prices.apply_price(
                db, ACCOUNT_ID, PROFESSIONAL_ID, OTHER_SERVICE_ID, Decimal("0.00"), "USD"
            )
            await dao_service_prices.apply_price(
                db, PROFESSIONAL_ID, OTHER_SERVICE_ID, Decimal("45.00"), "USD"
            )
            free = await resolve_service_price(
                db, ACCOUNT_ID, PROFESSIONAL_ID, OTHER_SERVICE_ID
            )
            self.assertEqual((free.amount, free.source), (Decimal("0.00"), "offer"))

    async def test_updates_increment_version_and_removal_returns_to_base(self):
        async with self.sessions() as db, db.begin():
            first = await dao_service_prices.apply_price(
                db, PROFESSIONAL_ID, SERVICE_ID, Decimal("18.00"), "USD"
            )
            self.assertEqual(first.version, 1)
            second = await dao_service_prices.apply_price(
                db, PROFESSIONAL_ID, SERVICE_ID, Decimal("20.00"), "USD"
            )
            self.assertEqual((second.amount, second.version), (Decimal("20.00"), 2))

            await dao_offer_prices.apply_price(
                db, ACCOUNT_ID, PROFESSIONAL_ID, SERVICE_ID, Decimal("15.00"), "USD"
            )
            removed = await dao_offer_prices.remove_price(
                db, ACCOUNT_ID, PROFESSIONAL_ID, SERVICE_ID
            )
            self.assertIsNot(removed, None)
            resolved = await resolve_service_price(
                db, ACCOUNT_ID, PROFESSIONAL_ID, SERVICE_ID
            )
            self.assertEqual((resolved.amount, resolved.source), (Decimal("20.00"), "base"))

    async def test_prices_never_cross_the_offer_or_the_catalog(self):
        async with self.sessions() as db, db.begin():
            from src.core.db import DAOIntegrityError

            with self.assertRaises(DAOIntegrityError):
                # No offer row in this account: the FK rejects the override.
                await dao_offer_prices.apply_price(
                    db, "019c0000-0000-7000-8000-0000000000a9",
                    PROFESSIONAL_ID, SERVICE_ID, Decimal("15.00"), "USD",
                )
                await db.flush()


if __name__ == "__main__":
    unittest.main()
