#!/usr/bin/env python3
"""Config loader for daily job-scouting tuning controls.

The workspace intentionally avoids a PyYAML dependency. If PyYAML is installed
we use it; otherwise a small parser handles the simple YAML subset used by
docs/job_scout_tuning.yaml.
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
from pathlib import Path
from typing import Any

WORKDIR = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = WORKDIR / "docs" / "job_scout_tuning.yaml"
DEFAULT_FEEDBACK_PATH = WORKDIR / "data" / "job_scout_feedback.jsonl"

PRESETS: dict[str, dict[str, Any]] = {
    "balanced": {},
    "precision": {
        "budgets": {
            "total_queries": 10,
            "p0_queries": 6,
            "p1_queries": 3,
            "p2_queries": 1,
            "manual_check_target_min": 8,
            "manual_check_target_max": 15,
        },
        "depth": {"validation_mode": "deep", "max_full_jd_validations": 12},
        "breadth": {"adjacent_role_ratio": 0.25, "broad_junior_ratio": 0.05},
    },
    "exploration": {
        "budgets": {
            "total_queries": 18,
            "p0_queries": 6,
            "p1_queries": 7,
            "p2_queries": 5,
            "manual_check_target_min": 20,
            "manual_check_target_max": 30,
        },
        "breadth": {"adjacent_role_ratio": 0.50, "broad_junior_ratio": 0.25},
        "depth": {"validation_mode": "standard", "max_full_jd_validations": 8},
    },
    "freshness": {
        "budgets": {"total_queries": 14, "p0_queries": 5, "p1_queries": 5, "p2_queries": 4},
        "freshness": {
            "prefer_posted_within_days": 7,
            "allow_unknown_date": False,
            "recheck_seen_after_days": 14,
        },
    },
    "target_company": {
        "budgets": {
            "total_queries": 12,
            "p0_queries": 5,
            "p1_queries": 5,
            "p2_queries": 2,
            "target_companies_per_run": 12,
        },
        "sources": {"direct_company": {"weight": 1.20}, "join": {"weight": 0.95}},
    },
    "local_first": {
        "budgets": {"total_queries": 14, "p0_queries": 6, "p1_queries": 5, "p2_queries": 3},
        "breadth": {"local_first": True, "far_south_requires_score": 0.82},
        "scoring": {"save_threshold": 0.52},
    },
}

DEFAULT_TUNING: dict[str, Any] = {
    "preset": "balanced",
    "budgets": {
        "total_queries": 14,
        "p0_queries": 6,
        "p1_queries": 5,
        "p2_queries": 3,
        "target_companies_per_run": 8,
        "validated_target_min": 3,
        "validated_target_max": 8,
        "manual_check_target_min": 15,
        "manual_check_target_max": 25,
    },
    "freshness": {
        "prefer_posted_within_days": 14,
        "allow_unknown_date": True,
        "recheck_seen_after_days": 21,
        "reject_expired": True,
        "stale_manual_check_after_days": 30,
    },
    "breadth": {
        "adjacent_role_ratio": 0.35,
        "broad_junior_ratio": 0.15,
        "local_first": True,
        "remote_germany_enabled": True,
        "far_south_requires_score": 0.75,
    },
    "depth": {
        "validation_mode": "standard",
        "require_full_jd_for_save": True,
        "extract_structured_signals": True,
        "read_project_narratives_for_high_fit": True,
        "max_full_jd_validations": 10,
    },
    "sources": {
        "direct_company": {"weight": 1.0, "save_allowed": True},
        "join": {"weight": 0.9, "save_allowed": True},
        "devjobs": {"weight": 0.8, "save_allowed": True},
        "stepstone_individual": {"weight": 0.75, "save_allowed": True},
        "stepstone_aggregate": {"weight": 0.45, "save_allowed": False},
        "linkedin": {"weight": 0.35, "save_allowed": False},
        "indeed": {"weight": 0.55, "save_allowed": False},
        "xing": {"weight": 0.50, "save_allowed": False},
    },
    "scoring": {
        "save_threshold": 0.50,
        "high_fit_threshold": 0.80,
        "manual_review_on_flags": True,
        "weights": {"technical": 0.35, "location": 0.34, "seniority": 0.26, "risk": 0.05},
    },
    "feedback": {
        "use_recent_feedback": True,
        "feedback_window_days": 30,
        "downrank_rejected_patterns": True,
        "boost_accepted_clusters": True,
        "min_signals_for_memory_proposal": 3,
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def _parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if not value:
        return ""
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "None", "~"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        body = value[1:-1].strip()
        if not body:
            return []
        return [_parse_scalar(part.strip()) for part in body.split(",")]
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _load_simple_yaml(path: Path) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        text = line.strip()
        if ":" not in text:
            continue
        key, raw_value = text.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        current = stack[-1][1]
        if raw_value == "":
            child: dict[str, Any] = {}
            current[key] = child
            stack.append((indent, child))
        else:
            current[key] = _parse_scalar(raw_value)
    return root


def load_yaml_subset(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError:
        return _load_simple_yaml(path)
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def load_tuning(path: Path | None = None) -> dict[str, Any]:
    path = path or DEFAULT_CONFIG_PATH
    config = copy.deepcopy(DEFAULT_TUNING)
    if path.exists():
        loaded = load_yaml_subset(path)
        preset = str(loaded.get("preset") or config["preset"])
        config = _deep_merge(config, PRESETS.get(preset, {}))
        config = _deep_merge(config, loaded)
        config["config_status"] = f"loaded: {path}"
    else:
        preset = str(config["preset"])
        config = _deep_merge(config, PRESETS.get(preset, {}))
        config["config_status"] = f"missing; using defaults: {path}"
    return normalize_tuning(config)


def normalize_tuning(config: dict[str, Any]) -> dict[str, Any]:
    budgets = config.setdefault("budgets", {})
    total = int(budgets.get("total_queries") or 0)
    p_counts = [
        int(budgets.get("p0_queries") or 0),
        int(budgets.get("p1_queries") or 0),
        int(budgets.get("p2_queries") or 0),
    ]
    if total <= 0:
        total = sum(p_counts) or 10
        budgets["total_queries"] = total
    if sum(p_counts) > total:
        scale = total / sum(p_counts)
        budgets["p0_queries"] = max(1, int(round(p_counts[0] * scale)))
        budgets["p1_queries"] = max(0, int(round(p_counts[1] * scale)))
        budgets["p2_queries"] = max(0, total - budgets["p0_queries"] - budgets["p1_queries"])
    return config


def source_priority(config: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    sources = config.get("sources") if isinstance(config.get("sources"), dict) else {}
    items = []
    for name, settings in sources.items():
        if isinstance(settings, dict):
            items.append((name, settings))
    return sorted(items, key=lambda item: float(item[1].get("weight") or 0), reverse=True)


def format_tuning_summary(config: dict[str, Any]) -> str:
    budgets = config["budgets"]
    freshness = config["freshness"]
    breadth = config["breadth"]
    depth = config["depth"]
    scoring = config["scoring"]
    lines = [
        "## Tuning profile",
        f"Preset: {config.get('preset')} ({config.get('config_status')})",
        (
            "Query budget: "
            f"total={budgets['total_queries']}, "
            f"P0={budgets['p0_queries']}, P1={budgets['p1_queries']}, P2={budgets['p2_queries']}, "
            f"target companies={budgets['target_companies_per_run']}"
        ),
        (
            "Targets: "
            f"validated {budgets['validated_target_min']}-{budgets['validated_target_max']}; "
            f"manual-check {budgets['manual_check_target_min']}-{budgets['manual_check_target_max']}"
        ),
        (
            "Freshness: "
            f"prefer <= {freshness['prefer_posted_within_days']}d; "
            f"recheck seen after {freshness['recheck_seen_after_days']}d; "
            f"allow unknown date={freshness['allow_unknown_date']}"
        ),
        (
            "Breadth: "
            f"adjacent_ratio={breadth['adjacent_role_ratio']}; "
            f"broad_junior_ratio={breadth['broad_junior_ratio']}; "
            f"far_south_requires_score={breadth['far_south_requires_score']}"
        ),
        (
            "Depth: "
            f"mode={depth['validation_mode']}; "
            f"max_full_jd_validations={depth['max_full_jd_validations']}; "
            f"require_full_jd_for_save={depth['require_full_jd_for_save']}"
        ),
        (
            "Scoring: "
            f"save_threshold={scoring['save_threshold']}; "
            f"high_fit_threshold={scoring['high_fit_threshold']}; "
            f"manual_review_on_flags={scoring['manual_review_on_flags']}"
        ),
        "",
        "### Source priority",
    ]
    for name, settings in source_priority(config):
        save = "validated-save allowed" if settings.get("save_allowed") else "manual-check/discovery only"
        lines.append(f"- {name}: weight={settings.get('weight')} | {save}")
    return "\n".join(lines)


def load_recent_feedback(
    path: Path | None = None,
    *,
    window_days: int = 30,
    today: dt.date | None = None,
) -> list[dict[str, Any]]:
    path = path or DEFAULT_FEEDBACK_PATH
    today = today or dt.date.today()
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        raw_date = str(payload.get("date") or payload.get("created_at") or "")
        try:
            seen_at = dt.date.fromisoformat(raw_date[:10])
        except ValueError:
            seen_at = today
        if (today - seen_at).days <= window_days:
            rows.append(payload)
    return rows


def summarize_feedback(feedback_rows: list[dict[str, Any]], *, min_signals: int = 3) -> str:
    if not feedback_rows:
        return "No recent explicit feedback found."
    by_action: dict[str, int] = {}
    reasons: dict[str, int] = {}
    for row in feedback_rows:
        action = str(row.get("action") or "unknown").strip().lower()
        by_action[action] = by_action.get(action, 0) + 1
        reason = str(row.get("reason") or "").strip().lower()
        if reason:
            reasons[reason] = reasons.get(reason, 0) + 1
    lines = [f"Recent explicit feedback items: {len(feedback_rows)} | by action: {by_action}"]
    repeated = [(reason, count) for reason, count in reasons.items() if count >= min_signals]
    if repeated:
        lines.append("Repeated feedback patterns worth proposing as MEMORY updates:")
        for reason, count in sorted(repeated, key=lambda item: item[1], reverse=True):
            lines.append(f"- {reason} ({count}x)")
    else:
        lines.append("No feedback pattern has enough repeated signals for a durable MEMORY update.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect job scouting tuning configuration")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--feedback", default=str(DEFAULT_FEEDBACK_PATH))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    config = load_tuning(Path(args.config))
    if args.json:
        print(json.dumps(config, ensure_ascii=False, indent=2))
        return 0
    print(format_tuning_summary(config))
    if config.get("feedback", {}).get("use_recent_feedback", True):
        rows = load_recent_feedback(
            Path(args.feedback),
            window_days=int(config.get("feedback", {}).get("feedback_window_days", 30)),
        )
        print()
        print("## Feedback summary")
        print(
            summarize_feedback(
                rows,
                min_signals=int(config.get("feedback", {}).get("min_signals_for_memory_proposal", 3)),
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
