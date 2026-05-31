from __future__ import annotations

import unittest

from scripts.score_lead import compute_score, compute_score_from_signals


class ScoreLeadTests(unittest.TestCase):
    def test_far_south_onsite_penalty(self) -> None:
        result = compute_score(
            0.95,
            "München",
            title="Computer Vision Engineer",
            years_required=1,
            work_mode="onsite",
        )

        self.assertLessEqual(result.location_score, 0.22)
        self.assertLess(result.score, 0.7)

    def test_remote_and_hybrid_location_adjustment(self) -> None:
        remote = compute_score(0.7, "Germany remote", title="ML Engineer", years_required=1)
        hybrid = compute_score(
            0.7,
            "Hannover hybrid",
            title="ML Engineer",
            years_required=1,
            work_mode="hybrid",
        )

        self.assertGreaterEqual(remote.location_score, 0.88)
        self.assertGreater(hybrid.location_score, 0.91)

    def test_senior_or_five_years_penalty(self) -> None:
        result = compute_score(
            0.9,
            "Hamburg",
            title="Senior Computer Vision Engineer",
            years_required=5,
        )

        self.assertLessEqual(result.seniority_score, 0.22)
        self.assertLess(result.score, 0.5)

    def test_cpp_primary_gate(self) -> None:
        result = compute_score_from_signals(
            {
                "title": "C++ Software Engineer",
                "location": "Hannover",
                "technical_score": 0.9,
                "cpp_requirement_level": "primary",
                "csharp_requirement_level": "none",
                "seniority_level": "junior",
                "source_confidence": "full_jd",
            }
        )

        self.assertEqual(result.save_recommendation, "manual_check_only")
        self.assertIn("cpp-primary", result.review_flags)
        self.assertLessEqual(result.technical_score, 0.4)

    def test_python_cv_with_secondary_cpp_is_review_not_hard_gate(self) -> None:
        result = compute_score_from_signals(
            {
                "title": "Computer Vision Engineer",
                "location": "Hamburg hybrid",
                "work_mode": "hybrid",
                "technical_score": 0.88,
                "cpp_requirement_level": "secondary",
                "csharp_requirement_level": "none",
                "python_requirement_level": "primary",
                "seniority_level": "junior_mixed",
                "source_confidence": "full_jd",
                "jd_excerpt": "Python, PyTorch and OpenCV are central; C++ is used for integration.",
            }
        )

        self.assertGreaterEqual(result.score, 0.5)
        self.assertEqual(result.save_recommendation, "yes")

    def test_phd_postdoc_are_manual_check_only(self) -> None:
        phd = compute_score_from_signals(
            {
                "title": "Research Scientist Computer Vision",
                "location": "Berlin",
                "technical_score": 0.95,
                "phd_required": True,
                "source_confidence": "full_jd",
            }
        )
        postdoc = compute_score_from_signals(
            {
                "title": "Postdoc Computer Vision",
                "location": "Berlin",
                "technical_score": 0.95,
                "postdoc": True,
                "source_confidence": "full_jd",
            }
        )

        self.assertEqual(phd.save_recommendation, "manual_check_only")
        self.assertEqual(postdoc.save_recommendation, "manual_check_only")

    def test_source_not_full_jd_manual_review(self) -> None:
        result = compute_score_from_signals(
            {
                "title": "Computer Vision Engineer",
                "location": "Hannover",
                "technical_score": 0.9,
                "seniority_level": "junior",
                "source_confidence": "snippet",
            }
        )

        self.assertIn("source-not-full-jd", result.review_flags)
        self.assertEqual(result.save_recommendation, "manual_review")


if __name__ == "__main__":
    unittest.main()
