import unittest
from decimal import Decimal
from uuid import uuid7

from pydantic import ValidationError

from src.api.care_plans.domain.goals import (
    AddCarePlanActionPayload,
    AddCarePlanGoalPayload,
    CompleteCarePlanActionPayload,
    EvaluateCarePlanGoalPayload,
    UpdateCarePlanGoalPayload,
)
from src.api.care_plans.domain.plans import (
    CreatePatientCarePlanPayload,
    UpdatePatientCarePlanPayload,
)


class CarePlanSchemaTests(unittest.TestCase):
    def test_preventive_plan_without_condition_and_partial_dates(self):
        result = CreatePatientCarePlanPayload.model_validate({
            "patientId": str(uuid7()), "title": "PRIV-E17-PLAN-PREVENTIVO",
            "purpose": "Control anual", "startDate": "2026-11",
        })
        self.assertIsNone(result.condition_id)
        self.assertEqual(result.start_date, "2026-11")

    def test_measurable_goal_needs_reference(self):
        with self.assertRaises(ValidationError):
            AddCarePlanGoalPayload.model_validate({
                "planId": str(uuid7()), "patientId": str(uuid7()),
                "description": "Bajar peso", "goalKind": "measurable",
            })
        result = AddCarePlanGoalPayload.model_validate({
            "planId": str(uuid7()), "patientId": str(uuid7()),
            "description": "Bajar peso", "goalKind": "measurable",
            "measurementKind": "weight", "targetValue": str(Decimal("70")),
            "unit": "kg",
        })
        self.assertEqual(result.measurement_kind, "weight")

    def test_status_change_requires_reason_and_empty_patch_fails(self):
        with self.assertRaises(ValidationError):
            UpdatePatientCarePlanPayload.model_validate({"planStatus": "closed"})
        with self.assertRaises(ValidationError):
            UpdatePatientCarePlanPayload.model_validate({})
        UpdatePatientCarePlanPayload.model_validate({
            "planStatus": "closed", "statusReason": "Cumplido",
        })

    def test_action_completion_and_goal_evaluation_are_distinct(self):
        action = CompleteCarePlanActionPayload.model_validate({"completionNote": "Hecho"})
        self.assertIsNone(action.completed_at)
        evaluation = EvaluateCarePlanGoalPayload.model_validate({
            "evaluationStatus": "achieved",
        })
        self.assertEqual(evaluation.evaluation_status, "achieved")
        with self.assertRaises(ValidationError):
            EvaluateCarePlanGoalPayload.model_validate({"evaluationStatus": "pending"})

    def test_action_goal_must_belong_to_payload_shape(self):
        payload = AddCarePlanActionPayload.model_validate({
            "planId": str(uuid7()), "patientId": str(uuid7()),
            "description": "Caminar 30 minutos",
        })
        self.assertIsNone(payload.goal_id)
        self.assertIsNone(payload.responsible_user_id)

    def test_null_on_present_field_fails(self):
        with self.assertRaises(ValidationError):
            UpdateCarePlanGoalPayload.model_validate({"description": None})


if __name__ == "__main__":
    unittest.main()
