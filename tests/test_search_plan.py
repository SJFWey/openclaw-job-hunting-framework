from __future__ import annotations

import datetime as dt
import json
import unittest
from pathlib import Path

from scripts.job_scout_tuning import load_tuning
from scripts.search_plan import build_search_plan


FIXTURE = Path(__file__).parent / "fixtures" / "agent_job_search_keywords.example.json"


class SearchPlanTests(unittest.TestCase):
    def _plan(self, run_date: dt.date = dt.date(2026, 5, 31)) -> dict:
        pack = json.loads(FIXTURE.read_text(encoding="utf-8"))
        tuning = load_tuning()
        tuning["budgets"]["total_queries"] = 9
        tuning["budgets"]["p0_queries"] = 4
        tuning["budgets"]["p1_queries"] = 3
        tuning["budgets"]["p2_queries"] = 2
        tuning["coverage"]["min_distinct_clusters"] = 3
        tuning["coverage"]["source_family_targets"] = {
            "direct_or_ats": 2,
            "specialized_boards": 2,
            "aggregate_boards": 2,
            "xray_search": 3,
        }
        return build_search_plan(date=run_date, keyword_pack=pack, tuning=tuning)

    def test_query_budget_is_strict(self) -> None:
        plan = self._plan()

        self.assertEqual(plan["total_queries"], 9)
        self.assertEqual(len(plan["slots"]), 9)

    def test_priority_and_exploration_mix(self) -> None:
        plan = self._plan()
        coverage = plan["coverage"]

        self.assertEqual(coverage["priority_counts"]["P0"], 4)
        self.assertEqual(coverage["priority_counts"]["P1"], 3)
        self.assertEqual(coverage["priority_counts"]["P2"], 2)
        self.assertGreaterEqual(
            coverage["exploration_ratio"],
            coverage["exploration_floor_ratio"],
        )

    def test_source_and_location_coverage_are_explicit(self) -> None:
        plan = self._plan()
        coverage = plan["coverage"]

        self.assertEqual(
            set(coverage["source_family_counts"]),
            {"direct_or_ats", "specialized_boards", "aggregate_boards", "xray_search"},
        )
        self.assertEqual(
            set(coverage["location_band_counts"]),
            {"local_north", "germany_remote", "broader_germany"},
        )
        self.assertGreaterEqual(
            coverage["distinct_clusters"],
            coverage["min_distinct_clusters"],
        )

    def test_rotation_is_stable_per_day_and_changes_across_days(self) -> None:
        same_a = self._plan(dt.date(2026, 5, 31))
        same_b = self._plan(dt.date(2026, 5, 31))
        next_day = self._plan(dt.date(2026, 6, 1))

        self.assertEqual(same_a, same_b)
        self.assertNotEqual(same_a["slots"], next_day["slots"])


if __name__ == "__main__":
    unittest.main()
