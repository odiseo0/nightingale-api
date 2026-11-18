import unittest
from pathlib import Path

from src.api.care_plans.repository.models import (
    CarePlan,
    CarePlanAction,
    CarePlanActionHistory,
    CarePlanGoal,
    CarePlanGoalHistory,
    CarePlanHistory,
    CarePlanReview,
    CarePlanReviewHistory,
)

ROOT = Path(__file__).resolve().parents[1]


class CarePlanPersistenceModelTests(unittest.TestCase):
    def test_models_map_care_plan_tables(self):
        self.assertEqual(CarePlan.__tablename__, "care_plans")
        self.assertEqual(CarePlanHistory.__tablename__, "care_plan_histories")
        self.assertEqual(CarePlanGoal.__tablename__, "care_plan_goals")
        self.assertEqual(CarePlanGoalHistory.__tablename__, "care_plan_goal_histories")
        self.assertEqual(CarePlanAction.__tablename__, "care_plan_actions")
        self.assertEqual(
            CarePlanActionHistory.__tablename__, "care_plan_action_histories"
        )
        self.assertEqual(CarePlanReview.__tablename__, "care_plan_reviews")
        self.assertEqual(
            CarePlanReviewHistory.__tablename__, "care_plan_review_histories"
        )
        for model in (
            CarePlanHistory,
            CarePlanGoalHistory,
            CarePlanActionHistory,
            CarePlanReviewHistory,
        ):
            self.assertEqual(
                set(model.__table__.primary_key.columns.keys()),
                {"account_id", "id", "version"},
            )

    def test_plan_columns_match_design(self):
        columns = CarePlan.__table__.columns
        self.assertFalse(columns["title"].nullable)
        self.assertTrue(columns["condition_id"].nullable)
        self.assertTrue(columns["purpose"].nullable)
        self.assertFalse(columns["plan_status"].nullable)

    def test_migration_declares_section_and_grants(self):
        path = ROOT / "migrations/versions/20261117_02_care_plans.py"
        source = path.read_text(encoding="utf-8")
        self.assertIn('revision = "20261117_02"', source)
        self.assertIn('down_revision = "20261117_01"', source)
        self.assertIn("care_plans_access", source)
        self.assertIn("patient_conditions_scoped_uq", source)
        self.assertIn("REFERENCES nightingale.care_plan_goals", source)
        self.assertIn('GRANT SELECT,INSERT ON nightingale.{table}', source)


if __name__ == "__main__":
    unittest.main()
