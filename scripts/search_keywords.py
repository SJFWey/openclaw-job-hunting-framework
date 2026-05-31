#!/usr/bin/env python3
"""Load and format agent job-search keyword pack for cron/preflight context."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

WORKDIR = Path(__file__).resolve().parent.parent
DEFAULT_PATH = WORKDIR / "docs" / "agent_job_search_keywords.json"
LEGACY_NAME = "agent_job_search_keywords_legacy.json"


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, dict):
        out: list[str] = []
        for k, v in value.items():
            if isinstance(v, list):
                out.extend(str(x).strip() for x in v if str(x).strip())
            elif isinstance(v, str) and v.strip():
                out.append(f"{k}: {v.strip()}")
        return out
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _pick(data: dict, *keys: str) -> list[str]:
    for key in keys:
        if key in data:
            items = _as_list(data[key])
            if items:
                return items
    return []


def _collect_clusters_dict(data: dict) -> list[str]:
    clusters = data.get("clusters") or data.get("keyword_clusters") or data.get("search_clusters")
    if not isinstance(clusters, dict):
        return []
    lines: list[str] = []
    for name, items in clusters.items():
        vals = _as_list(items)
        if vals:
            preview = ", ".join(vals[:8])
            if len(vals) > 8:
                preview += f", … (+{len(vals) - 8})"
            lines.append(f"- **{name}**: {preview}")
    return lines


def _collect_cluster_objects(clusters: Any, *, max_keywords: int = 6) -> list[str]:
    if not isinstance(clusters, list):
        return []
    lines: list[str] = []
    for cluster in clusters:
        if not isinstance(cluster, dict):
            continue
        cid = cluster.get("cluster_id") or cluster.get("name") or "cluster"
        priority = cluster.get("priority") or ""
        desc = cluster.get("description") or ""
        kws = _as_list(cluster.get("keywords"))[:max_keywords]
        titles = _as_list(cluster.get("job_titles_en"))[:3]
        label = f"{cid} ({priority})" if priority else str(cid)
        parts = []
        if titles:
            parts.append("titles: " + ", ".join(titles))
        if kws:
            parts.append("kw: " + ", ".join(kws))
        if desc:
            parts.append(desc[:120])
        lines.append(f"- **{label}**: " + " | ".join(parts))
    return lines


def _suggest_queries(data: dict, *, limit: int = 8) -> list[str]:
    priority = data.get("priority") if isinstance(data.get("priority"), dict) else {}
    p0 = _as_list(priority.get("P0_highest_fit"))[:4]
    regions = []
    loc = data.get("locations")
    if isinstance(loc, dict):
        regions = _as_list(loc.get("region_keywords"))[:2]
    if not regions:
        regions = ["Germany", "Deutschland"]
    region = regions[0]
    queries: list[str] = []
    for title in p0:
        queries.append(f'"{title}" {region}')
    clusters = data.get("clusters")
    if isinstance(clusters, list):
        for cluster in clusters[:3]:
            if not isinstance(cluster, dict):
                continue
            kws = _as_list(cluster.get("keywords"))[:2]
            if kws:
                queries.append(f'{" ".join(kws)} {region}')
    notes = data.get("platform_search_notes")
    if isinstance(notes, dict):
        for platform_items in notes.values():
            queries.extend(_as_list(platform_items)[:2])
    seen: set[str] = set()
    unique: list[str] = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique.append(q)
        if len(unique) >= limit:
            break
    return unique


def _format_structured_pack(data: dict, *, path: Path, max_items: int = 12) -> str:
    """Format structured agent_job_search_keywords-style JSON."""
    lines = ["## Search keyword pack", f"Source: `{path}`"]
    name = data.get("candidate_name")
    if name:
        lines.append(f"Candidate: {name}")
    if data.get("document_date"):
        lines.append(f"Pack date: {data['document_date']}")

    positioning = data.get("candidate_positioning")
    if isinstance(positioning, dict):
        for lang in ("de", "en"):
            if positioning.get(lang):
                lines.append(f"Positioning ({lang}): {positioning[lang]}")

    markets = _as_list(data.get("target_market"))
    if markets:
        lines.append(f"Target market: {', '.join(markets)}")

    priority = data.get("priority")
    if isinstance(priority, dict):
        for key in ("P0_highest_fit", "P1_strong_fit", "P2_reasonable_fit"):
            titles = _as_list(priority.get(key))
            if titles:
                lines.append("")
                lines.append(f"### {key.replace('_', ' ')}")
                for t in titles[:max_items]:
                    lines.append(f"- {t}")
                if len(titles) > max_items:
                    lines.append(f"- … (+{len(titles) - max_items} in file)")

    cluster_lines = _collect_cluster_objects(data.get("clusters"))
    if cluster_lines:
        lines.extend(["", "### Clusters (daily P0; P1 every 2–3d; P2 weekly)", *cluster_lines[:max_items]])
        if len(cluster_lines) > max_items:
            lines.append(f"- … (+{len(cluster_lines) - max_items} clusters in file)")

    suggested = _suggest_queries(data, limit=8)
    if suggested:
        lines.extend(["", "### Suggested query seeds (rotate 3–5 per run)", *[f"- {q}" for q in suggested]])

    loc = data.get("locations")
    if isinstance(loc, dict):
        high = _as_list(loc.get("high_priority_germany_regions"))
        region_kw = _as_list(loc.get("region_keywords"))
        if high:
            lines.extend(["", "### High-priority locations"])
            for item in high[:max_items]:
                lines.append(f"- {item}")
            if len(high) > max_items:
                lines.append(f"- … (+{len(high) - max_items} in file)")
        if region_kw:
            lines.extend(["", "### Region keywords", *[f"- {x}" for x in region_kw[:8]]])

    exp = data.get("experience_filters")
    if isinstance(exp, dict):
        for label, key in (
            ("Include seniority", "include"),
            ("Use cautiously", "use_cautiously"),
            ("Exclude if too strict", "exclude_if_too_strict"),
        ):
            items = _as_list(exp.get(key))
            if items:
                lines.append("")
                lines.append(f"### {label}")
                for item in items:
                    lines.append(f"- {item}")

    negative = _as_list(data.get("negative_keywords"))
    if negative:
        lines.extend(["", "### Exclude / de-prioritize"])
        for item in negative[:max_items]:
            lines.append(f"- {item}")
        if len(negative) > max_items:
            lines.append(f"- … (+{len(negative) - max_items} in file)")

    workflow = _as_list(data.get("agent_workflow"))
    if workflow:
        lines.extend(["", "### Agent workflow (from pack)", *[f"- {w}" for w in workflow]])

    scoring = data.get("scoring_model")
    if isinstance(scoring, dict):
        base = scoring.get("base_relevance_score_100")
        classification = scoring.get("classification")
        lines.append("")
        lines.append("### Pack scoring hints (0–100; map to tracker 0–1 via score_lead.py)")
        if isinstance(base, dict):
            lines.append(
                f"- Title boosts: P0 +{base.get('title_match_P0', '?')}, "
                f"P1 +{base.get('title_match_P1', '?')}, P2 +{base.get('title_match_P2', '?')}; "
                f"penalty senior {base.get('penalty_senior_required', '?')}, "
                f"unrelated {base.get('penalty_unrelated_domain', '?')}"
            )
        if isinstance(classification, dict):
            for band, action in classification.items():
                lines.append(f"- {band}: {action}")

    companies = _as_list(data.get("company_types"))
    if companies:
        lines.extend(
            ["", "### Target company types", *[f"- {c}" for c in companies[:8]]]
        )

    lines.extend(
        [
            "",
            "### Usage (cron)",
            "- Run **P0** clusters/titles daily; align tracker saves with `score_lead.py` (0–1) not only pack 0–100.",
            "- Prefer Hannover/Northern DE locations; far south (e.g. München) gets location penalty per scoring rubric.",
            "- Apply **negative_keywords** and **exclude_if_too_strict** when filtering.",
            f"- Pack loaded: {date.today().isoformat()}.",
        ]
    )
    return "\n".join(lines)


def _is_structured_pack(data: dict) -> bool:
    return bool(data.get("candidate_name")) and isinstance(data.get("clusters"), list)


def resolve_keywords_path(explicit: str | None = None) -> Path | None:
    if explicit:
        p = Path(explicit).expanduser()
        return p if p.is_file() else None
    candidates = [
        DEFAULT_PATH,
        WORKDIR / "docs" / LEGACY_NAME,
        WORKDIR / LEGACY_NAME,
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


def load_keywords(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def format_context(data: dict, *, path: Path, max_queries: int = 12) -> str:
    if _is_structured_pack(data):
        return _format_structured_pack(data, path=path, max_items=max_queries)

    meta = data.get("meta") or data.get("metadata") or {}
    if not isinstance(meta, dict):
        meta = {}

    lines = [
        "## Search keyword pack",
        f"Source: `{path}`",
    ]
    if meta:
        name = meta.get("candidate") or meta.get("name") or meta.get("owner")
        version = meta.get("version") or meta.get("updated")
        if name:
            lines.append(f"Candidate: {name}")
        if version:
            lines.append(f"Pack version: {version}")

    sections: list[tuple[str, list[str]]] = [
        (
            "Ready-to-run queries (rotate across today’s searches)",
            _pick(
                data,
                "search_queries",
                "queries",
                "query_templates",
                "ready_queries",
                "daily_queries",
            ),
        ),
        (
            "Exploration / adjacent queries",
            _pick(
                data,
                "exploration_queries",
                "broad_queries",
                "adjacent_queries",
                "discovery_queries",
            ),
        ),
        (
            "Role / title keywords",
            _pick(data, "role_titles", "titles", "job_titles", "target_roles"),
        ),
        (
            "Technical / skill keywords",
            _pick(
                data,
                "technical_keywords",
                "skills",
                "technologies",
                "tech_keywords",
                "positive_keywords",
                "keywords",
            ),
        ),
        (
            "Location / region hints",
            _pick(
                data,
                "location_keywords",
                "locations",
                "regions",
                "geo_keywords",
                "location_hints",
            ),
        ),
        (
            "Seniority / level hints",
            _pick(data, "seniority_keywords", "seniority", "level_keywords", "entry_keywords"),
        ),
        (
            "Exclude / de-prioritize",
            _pick(
                data,
                "exclude_keywords",
                "negative_keywords",
                "exclude",
                "avoid_keywords",
                "deemphasize",
            ),
        ),
    ]

    cluster_lines = _collect_clusters_dict(data)
    if cluster_lines:
        lines.extend(["", "### Keyword clusters", *cluster_lines])

    for heading, items in sections:
        if not items:
            continue
        lines.append("")
        lines.append(f"### {heading}")
        for item in items[:max_queries]:
            lines.append(f"- {item}")
        if len(items) > max_queries:
            lines.append(f"- … (+{len(items) - max_queries} more in file)")

    de = data.get("de") if isinstance(data.get("de"), dict) else {}
    en = data.get("en") if isinstance(data.get("en"), dict) else {}
    for lang_label, block in (("German", de), ("English", en)):
        if not block:
            continue
        lang_items = _pick(block, "keywords", "search_queries", "queries", "technical_keywords")
        if lang_items:
            lines.append("")
            lines.append(f"### {lang_label} block")
            for item in lang_items[:max_queries]:
                lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "### Usage (cron)",
            "- Build **3–5** search queries per run from this pack; combine role + technical + location + `Germany`/`Deutschland` in query text.",
            "- Use **exploration** lines for at least one query outside obvious CV keywords.",
            "- Apply **exclude** terms when filtering; do not save obvious matches to excluded patterns.",
            f"- Pack loaded: {date.today().isoformat()}.",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Format job-search keyword JSON for cron context")
    parser.add_argument("--path", help="Override keyword JSON path")
    parser.add_argument("--json", action="store_true", help="Print raw JSON")
    parser.add_argument("--max-queries", type=int, default=12)
    args = parser.parse_args(argv)

    path = resolve_keywords_path(args.path)
    if path is None:
        print(
            "## Search keyword pack\n"
            f"**Missing:** copy `{LEGACY_NAME}` to `{DEFAULT_PATH}`.\n"
            "Cron scouting should still run using `docs/profile.md` + `MEMORY.md`, but keyword pack is unavailable.",
            file=sys.stderr,
        )
        return 1

    try:
        data = load_keywords(path)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"## Search keyword pack\n**Error reading {path}:** {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    print(format_context(data, path=path, max_queries=args.max_queries))
    return 0


if __name__ == "__main__":
    sys.exit(main())
