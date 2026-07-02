from __future__ import annotations

import unittest
from pathlib import Path

from database import initialize_database
from prediction_engine import PredictionRequest, PredictionService


class PredictionSequenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        tmp_dir = Path("tmp")
        tmp_dir.mkdir(exist_ok=True)
        cls.db_path = tmp_dir / "test_changsha_prediction.db"
        if cls.db_path.exists():
            cls.db_path.unlink()
        initialize_database(cls.db_path)
        cls.service = PredictionService(cls.db_path)

    def test_prediction_returns_fixed_reach_target_safety_counts(self) -> None:
        result = self.service.predict(
            PredictionRequest(year=2026, score=636, quality_level="5A", rank=6881)
        )

        self.assertEqual(len(result["groups"]["reach"]), 3)
        self.assertEqual(len(result["groups"]["target"]), 4)
        self.assertEqual(len(result["groups"]["safety"]), 3)
        self.assertEqual(sum(len(group) for group in result["groups"].values()), 10)

    def test_recommendations_are_ordered_by_reference_rank_sequence(self) -> None:
        result = self.service.predict(
            PredictionRequest(year=2026, score=636, quality_level="5A", rank=6881)
        )

        ranks = [
            school["adjustedAdmissionRank"]
            for group_name in ("reach", "target", "safety")
            for school in result["groups"][group_name]
        ]
        self.assertEqual(ranks, sorted(ranks))

    def test_front_rank_returns_focused_recommendations_without_forcing_ten(self) -> None:
        result = self.service.predict(
            PredictionRequest(year=2026, score=680, quality_level="5A", rank=1)
        )

        self.assertEqual(len(result["groups"]["reach"]), 0)
        self.assertGreaterEqual(len(result["groups"]["target"]), 1)
        self.assertLess(sum(len(group) for group in result["groups"].values()), 10)
        self.assert_no_duplicate_schools(result)

    def test_late_rank_still_returns_fixed_counts_without_duplicates(self) -> None:
        result = self.service.predict(
            PredictionRequest(year=2026, score=500, quality_level="5A", rank=50000)
        )

        self.assert_group_counts(result, {"reach": 3, "target": 4, "safety": 3})
        self.assert_no_duplicate_schools(result)

    def test_small_school_set_returns_actual_count_without_duplicates(self) -> None:
        items = [self.fake_school(index) for index in range(1, 7)]
        groups, landing_school = self.service._recommend_by_rank_sequence(items, 3500)

        self.assertEqual(len(groups["reach"]), 2)
        self.assertEqual(len(groups["target"]), 2)
        self.assertEqual(len(groups["safety"]), 2)
        self.assertEqual(sum(len(group) for group in groups.values()), 6)
        self.assertEqual(landing_school["schoolId"], 3)

        school_ids = [
            school["schoolId"]
            for group_name in ("reach", "target", "safety")
            for school in groups[group_name]
        ]
        self.assertEqual(len(school_ids), len(set(school_ids)))

    def test_prediction_requires_rank(self) -> None:
        with self.assertRaisesRegex(ValueError, "位次"):
            self.service.predict(PredictionRequest(year=2026, score=636, quality_level="5A"))

    def test_score_does_not_change_rank_based_recommendations(self) -> None:
        low_score_result = self.service.predict(
            PredictionRequest(year=2026, score=1, quality_level="5A", rank=6881)
        )
        high_score_result = self.service.predict(
            PredictionRequest(year=2026, score=630, quality_level="5A", rank=6881)
        )

        low_score_schools = [
            school["schoolId"]
            for group in low_score_result["groups"].values()
            for school in group
        ]
        high_score_schools = [
            school["schoolId"]
            for group in high_score_result["groups"].values()
            for school in group
        ]
        self.assertEqual(low_score_schools, high_score_schools)

    def assert_group_counts(self, result: dict, expected: dict[str, int]) -> None:
        for group_name, count in expected.items():
            self.assertEqual(len(result["groups"][group_name]), count)

    def assert_no_duplicate_schools(self, result: dict) -> None:
        school_ids = [
            school["schoolId"]
            for group_name in ("reach", "target", "safety")
            for school in result["groups"][group_name]
        ]
        self.assertEqual(len(school_ids), len(set(school_ids)))

    def fake_school(self, index: int) -> dict:
        rank = index * 1000
        return {
            "schoolId": index,
            "schoolName": f"测试学校{index}",
            "category": "",
            "probability": 0,
            "admissionScore": 600 - index,
            "admissionRank": rank,
            "adjustedAdmissionRank": rank,
            "structureAdjustment": 0,
            "structureAdjustmentItems": [],
            "rankGap": 3500 - rank,
            "enrollmentPlan": None,
            "tier": "测试",
            "admissionBatch": "first",
            "stars": 0,
            "reason": "",
            "referenceYear": 2025,
        }


if __name__ == "__main__":
    unittest.main()
