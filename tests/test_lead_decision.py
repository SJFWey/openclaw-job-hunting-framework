from __future__ import annotations

import datetime as dt
import unittest

from scripts.job_scout_tuning import load_tuning
from scripts.lead_decision import decide_lead


TODAY = dt.date(2026, 5, 31)


def base_signals(**overrides):
    signals = {
        "title": "Computer Vision Engineer",
        "location": "Hannover",
        "work_mode": "hybrid",
        "technical_score": 0.88,
        "seniority_level": "junior",
        "source_confidence": "full_jd",
        "source_type": "direct_company",
        "published_date": "2026-05-25",
        "cpp_requirement_level": "none",
        "csharp_requirement_level": "none",
        "python_requirement_level": "primary",
    }
    signals.update(overrides)
    return signals


class LeadDecisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tuning = load_tuning()

    def test_high_score_snippet_source_is_manual_check(self) -> None:
        decision = decide_lead(
            base_signals(source_confidence="snippet", source_type="linkedin"),
            self.tuning,
            today=TODAY,
        )

        self.assertEqual(decision["decision_band"], "manual_check")
        self.assertEqual(decision["source_policy"], "manual_check_only")
        self.assertIn("source-manual-check-only", decision["review_flags"])

    def test_expired_posting_is_rejected(self) -> None:
        decision = decide_lead(
            base_signals(application_deadline="2026-05-01"),
            self.tuning,
            today=TODAY,
        )

        self.assertEqual(decision["freshness_status"], "expired")
        self.assertEqual(decision["decision_band"], "reject")
        self.assertIn("expired-posting", decision["blockers"])

    def test_stale_posting_is_manual_check(self) -> None:
        decision = decide_lead(
            base_signals(published_date="2026-04-01"),
            self.tuning,
            today=TODAY,
        )

        self.assertEqual(decision["freshness_status"], "stale")
        self.assertEqual(decision["decision_band"], "manual_check")

    def test_active_direct_page_can_validate_old_posting(self) -> None:
        decision = decide_lead(
            base_signals(published_date="2026-04-01", active_direct_page=True),
            self.tuning,
            today=TODAY,
        )

        self.assertEqual(decision["freshness_status"], "active_direct_page")
        self.assertEqual(decision["decision_band"], "validated_candidate")

    def test_cpp_primary_cannot_validated_save(self) -> None:
        decision = decide_lead(
            base_signals(
                title="C++ Software Engineer",
                cpp_requirement_level="primary",
                python_requirement_level="secondary",
            ),
            self.tuning,
            today=TODAY,
        )

        self.assertEqual(decision["decision_band"], "manual_check")
        self.assertIn("score-hard-gate-manual-check", decision["review_flags"])

    def test_full_fresh_allowed_source_can_validate(self) -> None:
        decision = decide_lead(base_signals(), self.tuning, today=TODAY)

        self.assertEqual(decision["source_policy"], "validated_save_allowed")
        self.assertEqual(decision["freshness_status"], "fresh")
        self.assertEqual(decision["decision_band"], "validated_candidate")


if __name__ == "__main__":
    unittest.main()
