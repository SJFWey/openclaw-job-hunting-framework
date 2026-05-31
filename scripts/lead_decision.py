#!/usr/bin/env python3
"""Policy decision wrapper for scored job leads.

This script is intentionally side-effect free. It combines the deterministic
dimension score with source/freshness policy so the agent can make the same
validated-save vs manual-check decision consistently before tracker writes.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

WORKDIR = Path(__file__).resolve().parent.parent
DEFAULT_TUNING_CONFIG = WORKDIR / "docs" / "job_scout_tuning.yaml"

sys.path.insert(0, str(WORKDIR / "scripts"))
from job_scout_tuning import load_tuning  # noqa: E402
from score_lead import compute_score_from_signals  # noqa: E402


MANUAL_SOURCE_CONFIDENCE = {
    "snippet",
    "search_result",
    "aggregate",
    "aggregate_only",
    "blocked",
    "login_gated",
    "cookie_shell",
}

BLOCKED_SOURCE_CONFIDENCE = {"blocked", "login_gated", "cookie_shell"}


def _norm(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def _load_json(raw_json: str | None, file_path: str | None) -> dict[str, Any]:
    if raw_json and file_path:
        raise ValueError("Use either --signals-json or --signals-file, not both")
    if file_path:
        return json.loads(Path(file_path).read_text(encoding="utf-8"))
    if raw_json:
        return json.loads(raw_json)
    return {}


def _parse_date(value: Any) -> dt.date | None:
    if not value:
        return None
    text = str(value).strip()
    for candidate in (text[:10], text):
        try:
            return dt.date.fromisoformat(candidate)
        except ValueError:
            continue
    return None


def freshness_status(signals: dict[str, Any], tuning: dict[str, Any], today: dt.date) -> tuple[str, list[str]]:
    freshness = tuning.get("freshness") if isinstance(tuning.get("freshness"), dict) else {}
    stale_after = int(freshness.get("stale_manual_check_after_days") or 30)
    reject_expired = bool(freshness.get("reject_expired", True))
    notes: list[str] = []

    active_direct = any(
        _as_bool(signals.get(key))
        for key in ("active_direct_page", "direct_page_active", "direct_page_still_active")
    ) or _norm(signals.get("source_confidence")) == "active_direct_page"
    if active_direct:
        return "active_direct_page", ["direct/company page indicates the role is still active"]

    deadline = _parse_date(signals.get("application_deadline"))
    if deadline and deadline < today and reject_expired:
        notes.append(f"application deadline passed: {deadline.isoformat()}")
        return "expired", notes
    if _as_bool(signals.get("expired")) or _as_bool(signals.get("posting_expired")):
        notes.append("posting marked expired by source or agent signals")
        return "expired", notes

    published = _parse_date(signals.get("published_date") or signals.get("posted_date"))
    if published:
        age = (today - published).days
        if age > stale_after:
            notes.append(f"published {age} days ago; stale threshold is {stale_after} days")
            return "stale", notes
        notes.append(f"published {age} days ago")
        return "fresh", notes

    allow_unknown = bool(freshness.get("allow_unknown_date", True))
    notes.append("posting date unknown")
    return ("unknown_date" if allow_unknown else "stale"), notes


def source_policy(signals: dict[str, Any], tuning: dict[str, Any]) -> tuple[str, list[str]]:
    confidence = _norm(signals.get("source_confidence"))
    source_type = _norm(signals.get("source_type"))
    platform = _norm(signals.get("platform"))
    source_key = source_type or platform
    notes: list[str] = []

    if confidence in BLOCKED_SOURCE_CONFIDENCE:
        return "blocked_or_login_gated", [f"source_confidence={confidence}"]
    if confidence in MANUAL_SOURCE_CONFIDENCE:
        notes.append(f"source_confidence={confidence}; full JD not reliable enough for save")
        return "manual_check_only", notes

    sources = tuning.get("sources") if isinstance(tuning.get("sources"), dict) else {}
    if source_key in sources and isinstance(sources[source_key], dict):
        if not sources[source_key].get("save_allowed", False):
            return "manual_check_only", [f"{source_key} is configured discovery/manual-check only"]
        return "validated_save_allowed", [f"{source_key} is configured validated-save allowed"]

    if source_key in {"direct_company", "company_career", "company_ats", "join", "devjobs", "stepstone_individual"}:
        return "validated_save_allowed", [f"{source_key or 'source'} is treated as full-JD capable"]
    if source_key in {"linkedin", "indeed", "xing", "stepstone_aggregate"}:
        return "manual_check_only", [f"{source_key} is treated as discovery/manual-check only"]
    if confidence in {"full_jd", "direct_page", "company_page"}:
        return "validated_save_allowed", [f"source_confidence={confidence}"]
    return "manual_check_only", ["source policy unknown; keep in Manual-check until validated"]


def decide_lead(
    signals: dict[str, Any],
    tuning: dict[str, Any],
    *,
    today: dt.date | None = None,
) -> dict[str, Any]:
    today = today or dt.date.today()
    scoring = tuning.get("scoring") if isinstance(tuning.get("scoring"), dict) else {}
    score_result = compute_score_from_signals(
        signals,
        save_threshold=float(scoring.get("save_threshold") or 0.5),
        manual_review_on_flags=bool(scoring.get("manual_review_on_flags", True)),
    )
    freshness, freshness_notes = freshness_status(signals, tuning, today)
    policy, policy_notes = source_policy(signals, tuning)

    blockers: list[str] = []
    review_flags = list(score_result.review_flags)
    if freshness == "expired":
        blockers.append("expired-posting")
    elif freshness == "stale":
        review_flags.append("stale-posting")
    if policy == "blocked_or_login_gated":
        review_flags.append("blocked-or-login-gated-source")
    elif policy == "manual_check_only":
        review_flags.append("source-manual-check-only")
    if score_result.save_recommendation == "manual_check_only":
        review_flags.append("score-hard-gate-manual-check")
    if score_result.signal_conflicts:
        review_flags.append("signal-conflict")

    if blockers:
        decision_band = "reject"
        next_action = "Do not save; report as rejected/noise unless a fresh public source is found."
    elif policy == "blocked_or_login_gated":
        decision_band = "manual_check"
        next_action = "Find a public direct/ATS alternative or keep as Manual-check."
    elif freshness in {"stale", "unknown_date"} and freshness != "active_direct_page":
        decision_band = "manual_check"
        next_action = "Verify freshness on direct company/ATS page before saving."
    elif score_result.save_recommendation in {"manual_review", "manual_check_only"} or policy == "manual_check_only":
        decision_band = "manual_check"
        next_action = "Review flags and source evidence before saving."
    elif score_result.save_recommendation == "yes":
        decision_band = "validated_candidate"
        next_action = "Eligible for validated recommendation if dedupe passes."
    elif score_result.score >= 0.40:
        decision_band = "backup"
        next_action = "Keep as backup; do not validated-save during daily scouting."
    else:
        decision_band = "reject"
        next_action = "Reject or omit from report unless user asks for broader exploration."

    return {
        "decision_band": decision_band,
        "freshness_status": freshness,
        "source_policy": policy,
        "blockers": blockers,
        "review_flags": sorted(set(review_flags)),
        "next_action": next_action,
        "score": asdict(score_result),
        "notes": freshness_notes + policy_notes + score_result.notes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compute lead decision policy")
    parser.add_argument("--signals-json", default="", help="Agent-extracted lead signal JSON object")
    parser.add_argument("--signals-file", default="", help="Path to agent-extracted lead signal JSON")
    parser.add_argument("--config", default=str(DEFAULT_TUNING_CONFIG))
    parser.add_argument("--today", help="YYYY-MM-DD date for deterministic freshness tests")
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    args = parser.parse_args(argv)

    signals = _load_json(args.signals_json or None, args.signals_file or None)
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    decision = decide_lead(signals, load_tuning(Path(args.config)), today=today)
    if args.json:
        print(json.dumps(decision, ensure_ascii=False, indent=2))
    else:
        print(f"decision_band={decision['decision_band']}")
        print(f"freshness_status={decision['freshness_status']}")
        print(f"source_policy={decision['source_policy']}")
        print(f"next_action={decision['next_action']}")
        if decision["review_flags"]:
            print("review_flags=" + ",".join(decision["review_flags"]))
        if decision["blockers"]:
            print("blockers=" + ",".join(decision["blockers"]))
        print(f"score={decision['score']['score']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
