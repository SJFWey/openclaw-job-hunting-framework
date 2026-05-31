from __future__ import annotations

import datetime as dt
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from scripts.job_scout_tuning import DEFAULT_TUNING, PRESETS, load_tuning


PREFLIGHT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "job_scouting_preflight.py"


def _load_preflight_module():
    spec = importlib.util.spec_from_file_location("job_scouting_preflight", PREFLIGHT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load preflight module: {PREFLIGHT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class JobScoutTuningTests(unittest.TestCase):
    def test_missing_config_uses_defaults(self) -> None:
        missing = Path(tempfile.gettempdir()) / "missing-job-scout-tuning.yaml"
        config = load_tuning(missing)

        self.assertEqual(config["preset"], DEFAULT_TUNING["preset"])
        self.assertIn("missing; using defaults", config["config_status"])
        self.assertGreater(config["budgets"]["total_queries"], 0)

    def test_each_preset_keeps_non_empty_query_mix(self) -> None:
        for preset in PRESETS:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".yaml") as tmp:
                tmp.write(f"preset: {preset}\n")
                tmp.flush()
                config = load_tuning(Path(tmp.name))

            budgets = config["budgets"]
            self.assertGreater(budgets["total_queries"], 0, preset)
            self.assertGreater(budgets["p0_queries"], 0, preset)
            self.assertGreaterEqual(budgets["p1_queries"], 0, preset)
            self.assertGreaterEqual(budgets["p2_queries"], 0, preset)
            self.assertLessEqual(
                budgets["p0_queries"] + budgets["p1_queries"] + budgets["p2_queries"],
                budgets["total_queries"],
                preset,
            )

    def test_preflight_run_plan_respects_query_budget(self) -> None:
        preflight = _load_preflight_module()
        preflight._recent_recommendation_keys = lambda: "none"
        preflight._recent_diagnostics = lambda: "none"
        preflight._feedback_summary = lambda tuning: "none"
        tuning = load_tuning()
        tuning["budgets"]["total_queries"] = 7
        tuning["budgets"]["p0_queries"] = 3
        tuning["budgets"]["p1_queries"] = 2
        tuning["budgets"]["p2_queries"] = 2

        plan = preflight.run_plan(dt.datetime(2026, 5, 31), tuning)
        query_lines = [
            line
            for line in plan.splitlines()
            if line[:2].rstrip(".").isdigit() or line[:3].rstrip(".").isdigit()
        ]

        self.assertEqual(len(query_lines), 7)
        self.assertIn("Configured mix: P0=3, P1=2, P2=2, total=7", plan)

    def test_preflight_final_line_is_wake_gate_json(self) -> None:
        preflight = _load_preflight_module()
        preflight._tracker_fingerprint = lambda: {
            "tracker_exists": True,
            "tracker_mtime": 1,
            "application_count": 1,
            "recommendation_count": 1,
        }
        preflight.run = lambda *args, **kwargs: (True, "ok")
        preflight.workbook_snapshot = lambda: "snapshot"
        preflight.run_plan = lambda now, tuning=None: "## Daily run plan\nnone"

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            preflight.main(["--dry-run"])

        last_line = [line for line in stdout.getvalue().splitlines() if line][-1]
        gate = json.loads(last_line)
        self.assertEqual(gate, {"wakeAgent": True, "reason": "ok"})


if __name__ == "__main__":
    unittest.main()
