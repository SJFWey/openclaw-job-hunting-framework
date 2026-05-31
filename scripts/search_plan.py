#!/usr/bin/env python3
"""Deterministic search planner for job scouting.

The planner does not search the web. It turns the keyword pack and tuning
config into a coverage-oriented matrix that the OpenClaw agent can execute.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

WORKDIR = Path(__file__).resolve().parent.parent
DEFAULT_KEYWORD_PACK = WORKDIR / "docs" / "agent_job_search_keywords.json"
DEFAULT_TUNING_CONFIG = WORKDIR / "docs" / "job_scout_tuning.yaml"
DEFAULT_DIAGNOSTICS = WORKDIR / "docs" / "search_diagnostics.md"

sys.path.insert(0, str(WORKDIR / "scripts"))
from job_scout_tuning import load_tuning  # noqa: E402


FALLBACK_CLUSTERS: list[dict[str, Any]] = [
    {
        "cluster_id": "vision-core",
        "priority": "P0",
        "description": "Computer vision, image processing, and machine vision roles.",
        "keywords": ["computer vision", "image processing", "machine vision", "OpenCV"],
        "boolean_queries": [
            '"Computer Vision Engineer" Germany junior OR graduate',
            '"Softwareentwickler Bildverarbeitung" Deutschland Python OR OpenCV',
        ],
    },
    {
        "cluster_id": "test-validation",
        "priority": "P0",
        "description": "Testing and validation roles tied to sensors, cameras, or measurement.",
        "keywords": ["validation", "test automation", "sensor testing", "measurement"],
        "boolean_queries": [
            '"Test Engineer" camera OR sensor Germany Python',
            '"Validierungsingenieur" Sensorik Messtechnik Deutschland',
        ],
    },
    {
        "cluster_id": "optical-metrology",
        "priority": "P1",
        "description": "Optical metrology, calibration, and measurement systems.",
        "keywords": ["optical metrology", "calibration", "3D metrology"],
        "boolean_queries": [
            '"optische Messtechnik" Ingenieur Berufseinsteiger',
            '"Optical Metrology Engineer" Germany calibration',
        ],
    },
    {
        "cluster_id": "adjacent-junior-engineering",
        "priority": "P2",
        "description": "Broader junior engineering roles with plausible technical overlap.",
        "keywords": ["application engineering", "test bench", "data acquisition"],
        "boolean_queries": [
            '"Application Engineer" machine vision Germany',
            '"Pruefstandsautomatisierung" Python Sensor Deutschland',
        ],
    },
]

SOURCE_FAMILY_HINTS = {
    "direct_or_ats": "Prefer company career pages and ATS pages; validated-save may be possible after full JD.",
    "specialized_boards": "Use extractable specialist boards such as JOIN, DEVjobs, or individual StepStone pages.",
    "aggregate_boards": "Use broad boards for discovery only; keep snippet or login-gated hits in Manual-check.",
    "xray_search": "Use search-engine x-ray queries to find public company/ATS alternatives.",
}

LOCATION_HINTS = {
    "local_north": "Prioritize Northern Germany: Hannover, Braunschweig, Goettingen, Hamburg, Bremen, Berlin.",
    "germany_remote": "Prefer Germany-wide remote or hybrid roles; verify travel and office expectations.",
    "broader_germany": "Explore broader Germany only when technical fit is strong or role is clearly junior.",
}


@dataclass(frozen=True)
class SearchSlot:
    index: int
    cluster_id: str
    priority: str
    source_family: str
    location_band: str
    freshness_intent: str
    validation_intent: str
    query: str
    search_instruction: str


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _cluster_from_priority_entry(priority: str, title: str) -> dict[str, Any]:
    safe = "".join(ch.lower() if ch.isalnum() else "-" for ch in title).strip("-")
    return {
        "cluster_id": safe or priority.lower(),
        "priority": priority,
        "description": title,
        "keywords": [title],
        "boolean_queries": [f'"{title}" Germany OR Deutschland'],
    }


def extract_clusters(pack: dict[str, Any]) -> list[dict[str, Any]]:
    clusters = pack.get("clusters")
    out: list[dict[str, Any]] = []
    if isinstance(clusters, list):
        for item in clusters:
            if not isinstance(item, dict):
                continue
            cid = str(item.get("cluster_id") or item.get("name") or "").strip()
            priority = str(item.get("priority") or "P2").upper()
            queries = _as_list(item.get("boolean_queries")) or _as_list(item.get("queries"))
            keywords = _as_list(item.get("keywords"))
            titles = _as_list(item.get("job_titles_en"))
            if not cid:
                cid = (titles or keywords or [priority.lower()])[0]
            if not queries:
                seed = (titles or keywords or [cid])[0]
                queries = [f'"{seed}" Germany OR Deutschland']
            out.append(
                {
                    "cluster_id": cid,
                    "priority": priority if priority in {"P0", "P1", "P2"} else "P2",
                    "description": str(item.get("description") or cid),
                    "keywords": keywords,
                    "boolean_queries": queries,
                }
            )
    if out:
        return out

    priority = pack.get("priority") if isinstance(pack.get("priority"), dict) else {}
    for key, label in (
        ("P0_highest_fit", "P0"),
        ("P1_strong_fit", "P1"),
        ("P2_reasonable_fit", "P2"),
    ):
        for title in _as_list(priority.get(key)):
            out.append(_cluster_from_priority_entry(label, title))
    return out or FALLBACK_CLUSTERS


def _normalize_counts(total: int, targets: dict[str, Any], fallback: dict[str, int]) -> list[str]:
    raw = {key: int(value) for key, value in targets.items() if int(value or 0) > 0}
    counts = raw or fallback
    current = sum(counts.values())
    if current <= 0:
        counts = fallback
        current = sum(counts.values())
    scaled = {key: int(total * value / current) for key, value in counts.items()}
    while sum(scaled.values()) < total:
        key = max(counts, key=lambda item: counts[item] - scaled.get(item, 0))
        scaled[key] = scaled.get(key, 0) + 1
    while sum(scaled.values()) > total:
        key = max(scaled, key=scaled.get)
        scaled[key] -= 1
    sequence: list[str] = []
    for key, count in scaled.items():
        sequence.extend([key] * max(0, count))
    return sequence[:total]


def _counts_from_ratios(total: int, ratios: dict[str, Any], fallback: dict[str, float]) -> list[str]:
    values = {key: float(value) for key, value in ratios.items() if float(value or 0) > 0}
    values = values or fallback
    raw_total = sum(values.values()) or 1.0
    floors = {key: int(total * value / raw_total) for key, value in values.items()}
    fractions = {
        key: (total * value / raw_total) - floors[key]
        for key, value in values.items()
    }
    while sum(floors.values()) < total:
        key = max(fractions, key=fractions.get)
        floors[key] += 1
        fractions[key] = 0.0
    sequence: list[str] = []
    for key, count in floors.items():
        sequence.extend([key] * max(0, count))
    return sequence[:total]


def _priority_sequence(tuning: dict[str, Any], total: int) -> list[str]:
    budgets = tuning.get("budgets") if isinstance(tuning.get("budgets"), dict) else {}
    coverage = tuning.get("coverage") if isinstance(tuning.get("coverage"), dict) else {}
    counts = {
        "P0": int(budgets.get("p0_queries") or 0),
        "P1": int(budgets.get("p1_queries") or 0),
        "P2": int(budgets.get("p2_queries") or 0),
    }
    if sum(counts.values()) <= 0:
        counts = {"P0": max(1, total // 2), "P1": total // 3, "P2": total}
    sequence = _normalize_counts(total, counts, {"P0": 6, "P1": 5, "P2": 3})
    floor = float(coverage.get("exploration_floor_ratio") or 0.0)
    needed = int(total * floor + 0.999)
    current = sum(1 for item in sequence if item in {"P1", "P2"})
    idx = len(sequence) - 1
    while current < needed and idx >= 0:
        if sequence[idx] == "P0":
            sequence[idx] = "P2"
            current += 1
        idx -= 1
    return sequence


def _rotated(items: list[Any], count: int, offset: int) -> list[Any]:
    if not items:
        return []
    return [items[(offset + i) % len(items)] for i in range(count)]


def _pick_cluster(clusters: list[dict[str, Any]], priority: str, index: int) -> dict[str, Any]:
    matching = [item for item in clusters if item.get("priority") == priority]
    pool = matching or clusters
    return pool[index % len(pool)]


def _slot_query(cluster: dict[str, Any], index: int) -> str:
    queries = _as_list(cluster.get("boolean_queries"))
    if not queries:
        seed = (_as_list(cluster.get("keywords")) or [str(cluster.get("cluster_id"))])[0]
        return f'"{seed}" Germany OR Deutschland'
    return " ".join(queries[index % len(queries)].split())


def build_search_plan(
    *,
    date: dt.date,
    keyword_pack: dict[str, Any],
    tuning: dict[str, Any],
) -> dict[str, Any]:
    budgets = tuning.get("budgets") if isinstance(tuning.get("budgets"), dict) else {}
    coverage = tuning.get("coverage") if isinstance(tuning.get("coverage"), dict) else {}
    freshness = tuning.get("freshness") if isinstance(tuning.get("freshness"), dict) else {}
    total = int(budgets.get("total_queries") or 14)

    clusters = extract_clusters(keyword_pack)
    day_offset = date.toordinal()
    priorities = _priority_sequence(tuning, total)
    source_families = _normalize_counts(
        total,
        coverage.get("source_family_targets") if isinstance(coverage.get("source_family_targets"), dict) else {},
        {"direct_or_ats": 4, "specialized_boards": 4, "aggregate_boards": 3, "xray_search": 3},
    )
    locations = _counts_from_ratios(
        total,
        coverage.get("location_band_targets") if isinstance(coverage.get("location_band_targets"), dict) else {},
        {"local_north": 0.45, "germany_remote": 0.25, "broader_germany": 0.30},
    )
    source_families = _rotated(source_families, total, day_offset % max(1, len(source_families)))
    locations = _rotated(locations, total, (day_offset // 3) % max(1, len(locations)))

    freshness_intent = (
        f"prefer <= {freshness.get('prefer_posted_within_days', 14)}d; "
        f"unknown date allowed={freshness.get('allow_unknown_date', True)}; "
        f"reject expired={freshness.get('reject_expired', True)}"
    )

    slots: list[SearchSlot] = []
    for i in range(total):
        cluster = _pick_cluster(clusters, priorities[i], day_offset + i)
        source_family = source_families[i]
        location_band = locations[i]
        validation_intent = (
            "full_jd_validation_candidate"
            if source_family in {"direct_or_ats", "specialized_boards"}
            else "discovery_manual_check_only"
        )
        query = _slot_query(cluster, day_offset + i)
        instruction = (
            f"{SOURCE_FAMILY_HINTS.get(source_family, source_family)} "
            f"{LOCATION_HINTS.get(location_band, location_band)}"
        )
        slots.append(
            SearchSlot(
                index=i + 1,
                cluster_id=str(cluster.get("cluster_id")),
                priority=priorities[i],
                source_family=source_family,
                location_band=location_band,
                freshness_intent=freshness_intent,
                validation_intent=validation_intent,
                query=query,
                search_instruction=instruction,
            )
        )

    return {
        "generated_for": date.isoformat(),
        "mode": "default",
        "total_queries": total,
        "coverage": _coverage_summary(slots, coverage),
        "slots": [asdict(slot) for slot in slots],
    }


def _coverage_summary(slots: list[SearchSlot], coverage: dict[str, Any]) -> dict[str, Any]:
    priorities = {key: 0 for key in ("P0", "P1", "P2")}
    source_families: dict[str, int] = {}
    location_bands: dict[str, int] = {}
    clusters: set[str] = set()
    for slot in slots:
        priorities[slot.priority] = priorities.get(slot.priority, 0) + 1
        source_families[slot.source_family] = source_families.get(slot.source_family, 0) + 1
        location_bands[slot.location_band] = location_bands.get(slot.location_band, 0) + 1
        clusters.add(slot.cluster_id)
    total = len(slots) or 1
    exploration_ratio = (priorities.get("P1", 0) + priorities.get("P2", 0)) / total
    return {
        "distinct_clusters": len(clusters),
        "min_distinct_clusters": int(coverage.get("min_distinct_clusters") or 8),
        "exploration_ratio": round(exploration_ratio, 2),
        "exploration_floor_ratio": float(coverage.get("exploration_floor_ratio") or 0.35),
        "priority_counts": priorities,
        "source_family_counts": source_families,
        "location_band_counts": location_bands,
    }


def format_markdown(plan: dict[str, Any], *, include_rollout_notes: bool = False) -> str:
    coverage = plan["coverage"]
    lines = [
        "## Search plan",
        "Mode: default coverage plan. Use this matrix as the daily scouting execution baseline.",
        (
            "Coverage: "
            f"clusters={coverage['distinct_clusters']}/{coverage['min_distinct_clusters']}; "
            f"exploration_ratio={coverage['exploration_ratio']}"
            f"/{coverage['exploration_floor_ratio']}"
        ),
        f"Priority mix: {coverage['priority_counts']}",
        f"Source-family mix: {coverage['source_family_counts']}",
        f"Location-band mix: {coverage['location_band_counts']}",
        "",
        "### Exploration matrix",
    ]
    for slot in plan["slots"]:
        lines.append(
            f"{slot['index']}. [{slot['priority']}] {slot['cluster_id']} | "
            f"{slot['source_family']} | {slot['location_band']} | "
            f"{slot['validation_intent']}"
        )
        lines.append(f"   Query: {slot['query']}")
        lines.append(f"   Instruction: {slot['search_instruction']}")
    if include_rollout_notes:
        lines.extend(
            [
                "",
                "### Execution notes",
                "- Execute the matrix before narrowing to obvious profile keywords.",
                "- Maintain broad candidate-pool coverage before spending full-JD validation budget.",
                "- Treat aggregate, blocked, or login-gated hits as Manual-check unless a full public JD validates them.",
            ]
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a job-search coverage plan")
    parser.add_argument("--keywords", default=str(DEFAULT_KEYWORD_PACK))
    parser.add_argument("--config", default=str(DEFAULT_TUNING_CONFIG))
    parser.add_argument("--date", help="YYYY-MM-DD date for deterministic rotation")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--execution-notes", action="store_true", help="Include execution notes")
    args = parser.parse_args(argv)

    run_date = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    plan = build_search_plan(
        date=run_date,
        keyword_pack=_load_json(Path(args.keywords)),
        tuning=load_tuning(Path(args.config)),
    )
    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    else:
        print(format_markdown(plan, include_rollout_notes=args.execution_notes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
