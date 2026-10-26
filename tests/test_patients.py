import unittest
from datetime import date, datetime
from uuid import uuid7

from pydantic import ValidationError

from src.api.patients.domain.patients import AddPatientIdentifierPayload, IdentifierInput, PatientCompletionPayload, PatientFields, PatientPatch, PatientProfileResponse, PatientQuery, RegisterPatientPayload
from src.api.patients.domain.contacts import ContactData, ContactPatch, RelationshipData, RelationshipPatch


class PatientSchemaTests(unittest.TestCase):
    def test_minor_boundary_uses_the_local_calendar_and_keeps_leap_day(self):
        profile = PatientProfileResponse.model_construct(birth_date=date(2010, 1, 1))
        self.assertTrue(profile.is_minor_on(date(2027, 12, 31)))
        self.assertFalse(profile.is_minor_on(date(2028, 1, 1)))
        profile.birth_date = date(2012, 2, 29)
        self.assertTrue(profile.is_minor_on(date(2030, 2, 28)))
        self.assertFalse(profile.is_minor_on(date(2030, 3, 1)))

    def test_completion_and_added_documents_do_not_claim_verification(self):
        self.assertEqual(PatientCompletionPayload(completion_status="complete").completion_status, "complete")
        for extra in ({"verificationStatus": "verified"}, {"verifiedAt": "2026-10-26T00:00:00Z"}, {"issuingCountry": "ZZ"}):
            with self.subTest(extra=extra), self.assertRaises(ValidationError):
                AddPatientIdentifierPayload.model_validate({"patientId": str(uuid7()), "documentType": "passport", "documentNumber": "FICT-001", **extra})

    def test_calendar_dates_and_instants_do_not_coerce_numeric_times(self):
        for value in ("20261026", "2026-10-26T00:00:00Z", "1792962000"):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                PatientFields(birth_date=value)
        for value in (True, 1792962000, "1792962000"):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                RelationshipData(relationship_kind="other", valid_from=value)
        data = RelationshipData(relationship_kind="other", valid_from="2026-01-01T00:00:00-04:00")
        self.assertIsInstance(data.model_dump()["valid_from"], datetime)
        self.assertEqual(data.model_dump(mode="json")["valid_from"], "2026-01-01T04:00:00Z")

    def test_contact_patches_preserve_required_name_and_document_sets(self):
        for payload in ({"fullName": "Fixture", "documentNumber": "ALONE"}, {"fullName": "Fixture", "phoneCode": "+58"}, {"fullName": "Fixture", "accountId": str(uuid7())}):
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                ContactData.model_validate(payload)
        for payload in ({}, {"fullName": None}, {"phone": None}):
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                ContactPatch.model_validate(payload)

    def test_relationship_does_not_accept_verification_or_invalid_ranges(self):
        payload = {"relationshipKind": "guardian", "validFrom": "2026-01-01T00:00:00Z"}
        self.assertFalse(RelationshipData.model_validate(payload).is_responsible_contact)
        for extra in ({"representationStatus": "verified"}, {"verifiedByUserId": str(uuid7())}, {"isResponsibleContact": 1}, {"validUntil": "2025-01-01T00:00:00Z"}, {"validFrom": "2026-01-01T00:00:00"}):
            with self.subTest(extra=extra), self.assertRaises(ValidationError):
                RelationshipData.model_validate({**payload, **extra})
        with self.assertRaises(ValidationError):
            RelationshipPatch(valid_from=None)

    def test_draft_can_be_empty_but_cannot_claim_identity_or_completion(self):
        self.assertIsNone(RegisterPatientPayload().full_name)
        for payload in ({"patientId": str(uuid7())}, {"completionStatus": "complete"}, {"status": "inactive"}, {"birthDate": True}, {"birthDate": 0}):
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                RegisterPatientPayload.model_validate(payload)

    def test_patch_preserves_absence_and_allows_explicit_nulls(self):
        patch = PatientPatch.model_validate({"fullName": None})
        self.assertEqual(patch.model_dump(by_alias=True, exclude_unset=True), {"fullName": None})
        for payload in ({}, {"fullName": "  "}, {"phone": None}, {"phoneCode": None}, {"version": 2}):
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                PatientPatch.model_validate(payload)

    def test_phone_structure_and_significant_zeros(self):
        number = PatientFields(phone_code="+39", phone="0212345678")
        self.assertEqual(number.phone, "0212345678")
        normalized = PatientFields(phone_code="+58", phone="04120000000")
        self.assertEqual(normalized.phone, "4120000000")
        for payload in ({"phoneCode": "+58"}, {"phoneCode": "+999", "phone": "1234567890"}, {"phoneCode": "+58", "phone": "1"}):
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                PatientFields.model_validate(payload)

    def test_documents_keep_text_and_do_not_accept_verification(self):
        payload = {"id": str(uuid7()), "documentType": "passport", "documentNumber": "  AB-00001  "}
        item = IdentifierInput.model_validate(payload)
        self.assertEqual(item.document_number, "AB-00001")
        self.assertEqual(item.issuing_country, "VE")
        for extra in ({"issuingCountry": "ZZ"}, {"verificationStatus": "verified"}, {"verifiedAt": "2026-10-26T00:00:00Z"}):
            with self.subTest(extra=extra), self.assertRaises(ValidationError):
                IdentifierInput.model_validate({**payload, **extra})
        with self.assertRaises(ValidationError):
            RegisterPatientPayload(identifiers=[item, item])

    def test_query_uses_public_aliases_and_bounds(self):
        self.assertEqual(PatientQuery.model_validate({"completionStatus": "draft"}).completion_status, "draft")
        for payload in ({"page": 0}, {"shows": 501}, {"q": " "}, {"cursor": "retired"}):
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                PatientQuery.model_validate(payload)
