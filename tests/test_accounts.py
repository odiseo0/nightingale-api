import unittest
from datetime import UTC, datetime
from uuid import uuid7

from pydantic import ValidationError

from src.api.accounts.domain.accounts import (
    AccessResponse,
    AccountDetails,
    AccountResponse,
    BootstrapPracticeInput,
    MeResponse,
    PracticeCreated,
    ProfessionalResponse,
)
from src.core.schema import BaseModel, PageQuery
from tests import test_foundation as foundation


class AccountSchemaTests(unittest.TestCase):
    def details(self):
        return {
            "displayName": " Fixture Practice ",
            "timeZone": "America/Caracas",
            "locationName": "Fixture Office",
            "locationAddress": "Fictional address",
            "locationState": "Fixture State",
            "locationCity": "Fixture City",
        }

    def test_bootstrap_uses_base_aliases_without_changing_external_identity(self):
        data = BootstrapPracticeInput.model_validate({
            **self.details(),
            "ownerIssuer": "https://fixture.invalid/realm ",
            "ownerSubject": " fixture-subject ",
            "ownerName": " Fixture Owner ",
            "professionalName": " Fixture Professional ",
        })

        self.assertIsInstance(data, BaseModel)
        self.assertEqual(data.display_name, "Fixture Practice")
        self.assertEqual(data.owner_subject, " fixture-subject ")
        self.assertEqual(data.owner_issuer, "https://fixture.invalid/realm ")
        self.assertEqual(data.owner_name, "Fixture Owner")
        self.assertEqual(data.location_country, "VE")
        self.assertIn("ownerSubject", data.model_dump(by_alias=True))

    def test_details_reject_unknown_country_blank_zone_and_injected_fields(self):
        for change in (
            {"locationCountry": "ZZ"}, {"timeZone": " "},
            {"ownerUserId": str(uuid7())}, {"displayName": " "},
        ):
            with self.subTest(fields=list(change)):
                with self.assertRaises(ValidationError):
                    AccountDetails.model_validate({**self.details(), **change})

    def test_responses_use_the_base_and_explicit_utc_projection(self):
        for schema in (AccountResponse, ProfessionalResponse, AccessResponse, MeResponse, PracticeCreated):
            self.assertTrue(issubclass(schema, BaseModel))

        now = datetime(2026, 10, 26, 13, tzinfo=UTC)
        response = ProfessionalResponse(
            id=uuid7(), user_id=uuid7(), public_name="Fixture", status="active",
            created_at=now, updated_at=now, version=1,
        ).model_dump(mode="json", by_alias=True)

        self.assertEqual(response["createdAt"], "2026-10-26T13:00:00Z")
        self.assertNotIn("oidcSubject", response)
        self.assertNotIn("secretHash", response)

    def test_page_parameters_keep_existing_defaults_and_reject_old_cursor_fields(self):
        self.assertEqual(PageQuery().model_dump(), {"page": 1, "shows": 100})
        self.assertEqual(PageQuery(page=2, shows=500).page, 2)
        for fields in ({"page": 0}, {"shows": 0}, {"shows": 501}, {"cursor": "old"}, {"limit": 100}):
            with self.subTest(fields=list(fields)):
                with self.assertRaises(ValidationError):
                    PageQuery(**fields)


class AccessMatrixTests(unittest.TestCase):
    run_python = foundation.FoundationTests.run_python
    database_settings = foundation.FoundationTests.database_settings

    def test_roles_account_and_device_states_keep_exact_actions_and_order(self):
        result = self.run_python('''
            import asyncio
            from datetime import UTC, datetime
            from types import SimpleNamespace
            from unittest.mock import AsyncMock, patch
            from uuid import uuid7
            from sqlalchemy.ext.asyncio import AsyncSession
            from src.api.accounts.application import accounts_cases as cases
            from src.api.sync.application.capabilities_cases import get_capabilities
            from src.core import Err, Ok
            from src.core.utils.utils import Empty

            common = """RegisterPatient UpdatePatientProfile SetPatientProfileStatus
                SetPatientCompletion AddPatientIdentifier CreateContactPerson UpdateContactPerson
                SetContactPersonStatus CreatePatientContactRelationship UpdatePatientContactRelationship
                SetPatientContactRelationshipStatus CreateScheduleRule UpdateScheduleRule SetScheduleRuleStatus
                CreateScheduleException UpdateScheduleException SetScheduleExceptionStatus CreateScheduleBlock
                UpdateScheduleBlock SetScheduleBlockStatus CreateAppointment ConfirmAppointment
                RescheduleAppointment CancelAppointment CompleteAppointment MarkAppointmentNoShow""".split()
            clinical = """SetPatientSexAtBirth CreatePatientCondition UpdatePatientCondition
                InvalidatePatientCondition SetPatientClinicalSectionReview CreatePatientAllergyIntolerance
                UpdatePatientAllergyIntolerance InvalidatePatientAllergyIntolerance SetPatientClinicalSectionReview
                CreatePatientEncounter UpdatePatientEncounter InvalidatePatientEncounter CreatePatientNote
                UpdatePatientNote InvalidatePatientNote RecordPatientMeasurement CorrectPatientMeasurement
                InvalidatePatientMeasurement RecordPatientImmunization UpdatePatientImmunization
                InvalidatePatientImmunization CreatePatientAntecedent UpdatePatientAntecedent
                InvalidatePatientAntecedent DeclarePatientMedication UpdatePatientDeclaredMedication
                ReviewPatientDeclaredMedication InvalidatePatientDeclaredMedication CreatePatientCarePlan
                UpdatePatientCarePlan InvalidatePatientCarePlan AddCarePlanGoal UpdateCarePlanGoal
                EvaluateCarePlanGoal InvalidateCarePlanGoal AddCarePlanAction UpdateCarePlanAction
                CompleteCarePlanAction InvalidateCarePlanAction AddCarePlanReview
                InvalidateCarePlanReview CreateDiagnosticReport UpdateDiagnosticReport
                CorrectDiagnosticReport AddDiagnosticReportResult UpdateDiagnosticReportResult
                InvalidateDiagnosticReportResult UploadReportAttachment
                InvalidateReportAttachment CreateSpecialtyTemplate UpdateSpecialtyTemplate
                RetireSpecialtyTemplate CaptureSpecialtyRecord UpdateSpecialtyRecord
                InvalidateSpecialtyRecord RecordDentalFinding UpdateDentalFinding
                ResolveDentalFinding InvalidateDentalFinding AddDentalTreatment UpdateDentalTreatment
                InvalidateDentalTreatment""".split()
            owner_actions = """CreateInvitation RevokeInvitation SetMembershipStatus SetMemberClinicalPermissions
                UpdateAccountDetails UpdateAccountPolicy SetAccountStatus RevokeAccountDevice RestoreAccountDevice
                UpdateProfessionalProfile CreateService UpdateService SetServiceStatus OfferService
                UpdateServiceOffer SetServiceOfferStatus""".split()

            async def check():
                account_id, user_id, device_id = [uuid7() for _ in range(3)]
                now = datetime.now(UTC)
                actor = SimpleNamespace(user_id=user_id, device_id=device_id)
                membership = SimpleNamespace(**{name + '_access': 'read_write' for name in
                    ('clinical_profile', 'conditions', 'allergies', 'encounters', 'notes',
                     'measurements', 'immunizations', 'antecedents', 'declared_medications', 'care_plans', 'diagnostic_reports', 'specialty_templates')})
                count = 0
                for owner in (False, True):
                    for account_state in ('active', 'inactive'):
                        for device_state in (None, 'active', 'revoked'):
                            account = SimpleNamespace(id=account_id, kind='independent',
                                owner_user_id=user_id if owner else uuid7(), display_name='Fixture',
                                time_zone='America/Caracas', location_name='Fixture', location_address='Fixture',
                                location_country='VE', location_state='Fixture', location_city='Fixture',
                                status=account_state, no_show_grace_minutes=15,
                                created_at=now, updated_at=now, version=1)
                            device = Empty if device_state is None else SimpleNamespace(status=device_state)
                            with patch.object(cases, 'authenticate', new=AsyncMock(return_value=Ok(actor))), \
                                patch.object(cases.dao_accounts, 'get_for_member', new=AsyncMock(return_value=(account, membership))), \
                                patch.object(cases.dao_account_devices, 'get_scoped', new=AsyncMock(return_value=device)), \
                                patch.object(cases, 'get_permission_epoch', new=AsyncMock(return_value=Ok(7))):
                                async with AsyncSession() as db:
                                    response = await cases.get_access(db, None, account_id)
                            count += 1
                            if not owner and account_state == 'inactive':
                                assert isinstance(response, Err), (owner, account_state, device_state)
                                continue
                            assert isinstance(response, Ok)
                            value = response.value
                            state = 'inactive' if account_state == 'inactive' else device_state or 'registration_required'
                            expected = []
                            if state in ('active', 'registration_required'):
                                expected = ['RegisterAccountDevice']
                            if state == 'active':
                                expected += common + clinical + (owner_actions if owner else [])
                            if state == 'inactive' and owner and device_state == 'active':
                                expected = ['SetAccountStatus']
                            assert value.allowed_actions == expected, (owner, account_state, device_state)
                            assert value.status == state and value.permission_epoch == 7
                            assert value.role == ('owner' if owner else 'assistant')
                # One action has two published positions; invitation acceptance uses its own route.
                published = {'RegisterAccountDevice', *common, *clinical, *owner_actions}
                assert published == set(get_capabilities().value.operation_catalog) - {'AcceptInvitation'}
                assert clinical.count('SetPatientClinicalSectionReview') == 2
                return {'states': count}
            print(json.dumps(asyncio.run(check())))
        ''', self.database_settings())
        self.assertEqual(result, {'states': 12})


if __name__ == "__main__":
    unittest.main()
