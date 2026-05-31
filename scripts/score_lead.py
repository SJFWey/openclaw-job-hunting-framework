#!/usr/bin/env python3
"""Deterministic job-lead dimension scoring for the job-hunting workspace."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

WEIGHT_TECHNICAL = 0.35
WEIGHT_LOCATION = 0.34
WEIGHT_SENIORITY = 0.26
WEIGHT_RISK = 0.05

SENIOR_TITLE_RE = re.compile(
    r"\b(senior|lead|principal|staff|expert|head of|team lead|architect)\b",
    re.I,
)
JUNIOR_TITLE_RE = re.compile(
    r"\b(junior|entry|graduate|trainee|berufseinsteiger|werkstudent|praktik|hiwi|absolvent)\b",
    re.I,
)
PHD_RE = re.compile(r"\b(ph\.?d|professor|promotion|doktorand|doctoral)\b", re.I)
POSTDOC_RE = re.compile(r"\b(postdoc|post-doctoral|postdoctoral)\b", re.I)
YEARS_RE = re.compile(
    r"(?:mindestens\s+|at least\s+|≥\s*)?"
    r"(\d+)\s*(?:\+|\s*[-–]\s*(\d+))?\s*(?:years?|yrs?|jahre?|j\.?\s*berufserfahrung|years?\s+of\s+experience)",
    re.I,
)
MEHRJAEHRIG_RE = re.compile(r"mehrj[aä]hrig", re.I)
CPP_CSHARP_RE = re.compile(r"(?:C\+\+|C\s*#|C#|\.NET)(?!\w)", re.I)
CPP_CSHARP_TITLE_RE = re.compile(
    r"(?:C\+\+|C\s*#|C#|\.NET).{0,24}(?:Developer|Entwickler|Engineer|Softwareentwickler)|"
    r"(?:Softwareentwickler|Entwickler|Developer|Engineer).{0,24}(?:C\+\+|C\s*#|C#|\.NET)",
    re.I,
)
CPP_CSHARP_SOLE_STRICT_RE = re.compile(
    r"(?:sehr\s+gute|fundiert|ausgeprägt|vertieft|expert|proficien|advanced)\s+"
    r"(?:kenntnisse\s+)?(?:in\s+)?(?:C\+\+|C\s*#|C#|\.NET)|"
    r"(?:C\+\+|C#|\.NET)\s*(?:als\s+)?(?:haupt|primary)|"
    r"(?:C\+\+|C#|\.NET).{0,30}(?:erforderlich|required|essential|zwingend|voraussetzung)|"
    r"(?:erforderlich|required|zwingend).{0,30}(?:C\+\+|C#|\.NET)|"
    r"kenntnisse\s+in\s+(?:C\+\+|C#|\.NET)(?!\s*/\s*Python)",
    re.I,
)
CPP_PYTHON_PAIR_RE = re.compile(
    r"(?:C\+\+|C#)\s*/\s*Python|Python\s*/\s*(?:C\+\+|C#)|"
    r"Erfahrung\s+in\s+C\+\+/Python|(?:C\+\+|C#)\s+und\s+Python|Python\s+und\s+(?:C\+\+|C#)|"
    r"Kenntnisse\s+in\s+C\+\+/Python",
    re.I,
)
PYTHON_CV_PRIMARY_RE = re.compile(
    r"(?:python|pytorch|tensorflow|opencv|computer\s+vision|bildverarbeitung|"
    r"deep\s+learning|machine\s+learning)",
    re.I,
)
CPP_CSHARP_OPTIONAL_RE = re.compile(
    r"(?:von\s+vorteil|nice\s+to\s+have|wünschenswert|optional|desirable)",
    re.I,
)
WISSMI_RE = re.compile(
    r"\b(wissenschaftlich(?:er|e|en|em)?\s+mitarbeit(?:er|erin)|"
    r"scientific\s+staff|research\s+associate)\b",
    re.I,
)
PROMOTION_REQUIRED_RE = re.compile(
    r"\b(promotion\s+(?:erforderlich|required|desired)|doktorand|doctoral\s+degree\s+required|"
    r"ph\.?\s*d\.?\s+(?:required|erforderlich))\b",
    re.I,
)

# Tier midpoints used when a city/region matches.
LOCATION_TIERS: list[tuple[float, tuple[str, ...]]] = [
    (
        0.98,
        (
            "clausthal",
            "clausthal-zellerfeld",
            "goslar",
            "osterode",
            "bad harzburg",
            "nordhausen",
        ),
    ),
    (
        0.91,
        (
            "braunschweig",
            "göttingen",
            "goettingen",
            "hildesheim",
            "hannover",
            "hanover",
            "wolfsburg",
            "salzgitter",
            "celle",
            "peine",
        ),
    ),
    (
        0.82,
        (
            "hamburg",
            "bremen",
            "lübeck",
            "luebeck",
            "magdeburg",
            "kassel",
            "oldenburg",
            "wilhelmshaven",
            "bremerhaven",
            "wedel",
            "pinneberg",
            "norderstedt",
            "kiel",
            "lüneburg",
            "lueneburg",
            "schleswig",
            "itzehoe",
            "elmshorn",
        ),
    ),
    (
        0.70,
        (
            "berlin",
            "leipzig",
            "dresden",
            "rostock",
            "schwerin",
            "osnabrück",
            "osnabrueck",
            "erfurt",
            "halle",
            "cottbus",
        ),
    ),
    (
        0.52,
        (
            "dortmund",
            "essen",
            "duesseldorf",
            "düsseldorf",
            "koeln",
            "köln",
            "cologne",
            "bonn",
            "duisburg",
            "bochum",
            "wuppertal",
            "bielefeld",
            "muenster",
            "münster",
        ),
    ),
    (
        0.38,
        (
            "frankfurt",
            "stuttgart",
            "nürnberg",
            "nuernberg",
            "nuremberg",
            "freiburg",
            "karlsruhe",
            "mannheim",
            "heidelberg",
            "mainz",
            "wiesbaden",
        ),
    ),
    (
        0.18,
        (
            "münchen",
            "muenchen",
            "munich",
            "augsburg",
            "regensburg",
            "ulm",
            "ingolstadt",
            "rosenheim",
        ),
    ),
]

REMOTE_RE = re.compile(r"\b(remote|homeoffice|100\s*%\s*remote|voll(?:ständig)?\s*remote)\b", re.I)
HYBRID_RE = re.compile(r"\b(hybrid|teilweise\s+remote|mix\s+aus\s+remote)\b", re.I)


@dataclass
class ScoreResult:
    technical_score: float
    location_score: float
    seniority_score: float
    risk_score: float
    score: float
    location_tier: str
    years_inferred: float | None
    notes: list[str]
    review_flags: list[str] = field(default_factory=list)
    save_recommendation: str = "yes"
    source_confidence: str = ""
    signal_conflicts: list[str] = field(default_factory=list)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _norm_level(value: Any) -> str:
    return str(value or "none").strip().lower().replace("-", "_").replace(" ", "_")


def _load_signals(raw_json: str | None, file_path: str | None) -> dict[str, Any]:
    if raw_json and file_path:
        raise ValueError("Use either --signals-json or --signals-file, not both")
    if file_path:
        return json.loads(Path(file_path).read_text(encoding="utf-8"))
    if raw_json:
        return json.loads(raw_json)
    return {}


def location_score_from_text(location: str, work_mode: str = "auto") -> tuple[float, str, list[str]]:
    text = (location or "").strip().lower()
    notes: list[str] = []

    mode = work_mode.lower()
    if mode == "auto":
        if REMOTE_RE.search(text):
            mode = "remote"
        elif HYBRID_RE.search(text):
            mode = "hybrid"
        else:
            mode = "onsite"

    if mode == "remote" or REMOTE_RE.search(text):
        notes.append("remote → location floor 0.88")
        return 0.88, "remote", notes

    tier_score = 0.55
    tier_label = "D-default (unmatched Germany)"
    for midpoint, keywords in LOCATION_TIERS:
        if any(k in text for k in keywords):
            tier_score = midpoint
            tier_label = f"tier ~{midpoint:.2f} ({keywords[0]})"
            break

    if "norddeutschland" in text or "northern germany" in text:
        tier_score = max(tier_score, 0.75)
        tier_label = "Northern Germany (region)"
        notes.append("Northern Germany region → location floor 0.75")

    if "germany" in text or "deutschland" in text:
        if tier_label.startswith("D-default"):
            tier_score = 0.62
            tier_label = "Germany-wide (unspecified city)"
            notes.append("unspecified German location → default score 0.62")

    if mode == "hybrid" or HYBRID_RE.search(text):
        adjusted = _clamp(tier_score + 0.10)
        notes.append(f"hybrid → +0.10 on office tier ({tier_score:.2f} → {adjusted:.2f})")
        return adjusted, f"hybrid/{tier_label}", notes

    return tier_score, tier_label, notes


def infer_years_required(text: str) -> float | None:
    if not text:
        return None
    if POSTDOC_RE.search(text) or PROMOTION_REQUIRED_RE.search(text):
        return 99.0
    if MEHRJAEHRIG_RE.search(text):
        return 3.0
    best: float | None = None
    for match in YEARS_RE.finditer(text):
        low = int(match.group(1))
        high = int(match.group(2)) if match.group(2) else low
        candidate = float(max(low, high))
        best = candidate if best is None else max(best, candidate)
    return best


def seniority_score_from_signals(
    years_required: float | None,
    title: str = "",
    jd_excerpt: str = "",
) -> tuple[float, float | None, list[str]]:
    notes: list[str] = []
    combined = f"{title}\n{jd_excerpt}".strip()
    inferred = years_required
    if inferred is None:
        inferred = infer_years_required(combined)

    if POSTDOC_RE.search(combined):
        notes.append("Postdoc program/track → seniority 0.12")
        return 0.12, inferred, notes

    if PROMOTION_REQUIRED_RE.search(combined) or (
        PHD_RE.search(combined)
        and re.search(r"(?:required|erforderlich|voraussetzung|mandatory)", combined, re.I)
    ):
        notes.append("PhD/Promotion required → seniority 0.20")
        return 0.20, inferred, notes

    if inferred is not None and inferred >= 99:
        notes.append("PhD required → seniority 0.20")
        return 0.20, inferred, notes

    if WISSMI_RE.search(combined) and not JUNIOR_TITLE_RE.search(title or ""):
        notes.append("Wissenschaftlicher Mitarbeiter without Postdoc/PhD-required signal → score normally with fixed-term/academic risk note")

    if SENIOR_TITLE_RE.search(title or "") and not JUNIOR_TITLE_RE.search(title or ""):
        notes.append("senior title without junior marker → cap 0.32")
        score = 0.32
        if inferred is not None and inferred >= 5:
            score = min(score, 0.22)
            notes.append(f"{inferred:.0f}+ yrs required → seniority 0.22")
        elif inferred is not None and inferred >= 3:
            score = min(score, 0.28)
            notes.append(f"{inferred:.0f}+ yrs required → seniority 0.28")
        return score, inferred, notes

    if inferred is None:
        if JUNIOR_TITLE_RE.search(combined):
            return 0.96, None, notes
        return 0.90, None, notes

    y = inferred
    if y <= 1:
        score = 0.96
    elif y <= 2:
        score = 0.84
    elif y <= 3:
        score = 0.70
    elif y <= 4:
        score = 0.56
    elif y <= 5:
        score = 0.28
    elif y <= 7:
        score = 0.20
    else:
        score = 0.12

    notes.append(f"{y:.0f} yrs experience required → seniority {score:.2f}")
    return score, inferred, notes


def infer_cpp_csharp_risk(
    jd_excerpt: str = "",
    title: str = "",
) -> tuple[float, float | None, list[str]]:
    """Return extra risk (0–1), optional technical cap, and notes."""
    combined = f"{title}\n{jd_excerpt}".strip()
    if not combined or not CPP_CSHARP_RE.search(combined):
        return 0.0, None, []

    notes: list[str] = []
    python_primary = bool(PYTHON_CV_PRIMARY_RE.search(combined))
    cpp_python_pair = bool(CPP_PYTHON_PAIR_RE.search(combined))

    if CPP_CSHARP_TITLE_RE.search(title or ""):
        notes.append("C++/C#-first title → risk +0.55, technical cap 0.40")
        return 0.55, 0.40, notes

    if CPP_CSHARP_SOLE_STRICT_RE.search(combined) and not CPP_CSHARP_OPTIONAL_RE.search(combined):
        if cpp_python_pair or python_primary:
            notes.append("C++/C# mentioned but Python/CV-primary JD → risk +0.18 (no stack cap)")
            return 0.18, None, notes
        notes.append("proficient C++/C# as primary stack → risk +0.55, technical cap 0.40")
        return 0.55, 0.40, notes

    if CPP_CSHARP_OPTIONAL_RE.search(combined):
        notes.append("optional C++/C# mention → risk +0.10")
        return 0.10, None, notes

    if cpp_python_pair or (python_primary and CPP_CSHARP_RE.search(combined)):
        notes.append("Python-primary with secondary C++/C# → risk +0.18")
        return 0.18, None, notes

    notes.append("C++/C# listed without clear optionality → risk +0.35")
    return 0.35, 0.55, notes


def compute_score(
    technical: float,
    location: str,
    *,
    years_required: float | None = None,
    title: str = "",
    jd_excerpt: str = "",
    work_mode: str = "auto",
    risk_score: float = 0.0,
    apply_regex_stack: bool = True,
) -> ScoreResult:
    technical_score = _clamp(technical)
    risk_score = _clamp(risk_score)

    location_score, tier_label, loc_notes = location_score_from_text(location, work_mode)
    seniority_score, years_inferred, sen_notes = seniority_score_from_signals(
        years_required, title=title, jd_excerpt=jd_excerpt
    )

    stack_risk = 0.0
    stack_notes: list[str] = []
    if apply_regex_stack:
        stack_risk, tech_cap, stack_notes = infer_cpp_csharp_risk(jd_excerpt, title=title)
        if stack_risk:
            risk_score = _clamp(risk_score + stack_risk)
        if tech_cap is not None:
            technical_score = min(technical_score, tech_cap)

    final = (
        WEIGHT_TECHNICAL * technical_score
        + WEIGHT_LOCATION * location_score
        + WEIGHT_SENIORITY * seniority_score
        + WEIGHT_RISK * (1.0 - risk_score)
    )
    if stack_risk >= 0.55:
        final = min(final, 0.48)
        stack_notes.append("proficient C++/C# → final score capped at 0.48 (do not validate-save)")

    if seniority_score <= 0.26:
        final = min(final, 0.47)
        sen_notes.append(
            "Postdoc / PhD-Promotion required track → final capped at 0.47 (manual-check)"
        )

    return ScoreResult(
        technical_score=round(technical_score, 2),
        location_score=round(location_score, 2),
        seniority_score=round(seniority_score, 2),
        risk_score=round(risk_score, 2),
        score=round(final, 2),
        location_tier=tier_label,
        years_inferred=years_inferred,
        notes=loc_notes + sen_notes + stack_notes,
    )


def _semantic_stack_adjustments(signals: dict[str, Any]) -> tuple[float, float | None, list[str], list[str]]:
    notes: list[str] = []
    review_flags: list[str] = []
    risk = 0.0
    tech_cap: float | None = None

    for lang in ("cpp", "csharp"):
        level = _norm_level(signals.get(f"{lang}_requirement_level"))
        if level in {"none", "not_mentioned", "absent"}:
            continue
        if level == "optional":
            risk = max(risk, 0.10)
            notes.append(f"{lang} optional by JD semantics → risk floor 0.10")
        elif level == "secondary":
            risk = max(risk, 0.18)
            notes.append(f"{lang} secondary by JD semantics → risk floor 0.18")
        elif level == "important":
            risk = max(risk, 0.35)
            tech_cap = min(tech_cap or 0.55, 0.55)
            review_flags.append(f"{lang}-important")
            notes.append(f"{lang} important by JD semantics → risk floor 0.35, technical cap 0.55")
        elif level == "primary":
            risk = max(risk, 0.55)
            tech_cap = min(tech_cap or 0.40, 0.40)
            review_flags.append(f"{lang}-primary")
            notes.append(f"{lang} primary by JD semantics → risk floor 0.55, technical cap 0.40")
        elif level == "unclear":
            risk = max(risk, 0.20)
            review_flags.append(f"{lang}-unclear")
            notes.append(f"{lang} requirement unclear by JD semantics → manual review")

    return risk, tech_cap, notes, review_flags


def _semantic_risk_adjustments(signals: dict[str, Any]) -> tuple[float, list[str], list[str]]:
    notes: list[str] = []
    review_flags: list[str] = []
    risk = 0.0

    travel = _norm_level(signals.get("travel_level"))
    if travel in {"frequent", "high", "extensive"}:
        risk += 0.25
        notes.append("frequent travel by JD semantics → risk +0.25")
    elif travel in {"occasional", "some"}:
        risk += 0.08
        notes.append("occasional travel by JD semantics → risk +0.08")
    elif travel == "unclear":
        risk += 0.05
        review_flags.append("travel-unclear")

    if _as_bool(signals.get("visa_blocker")) or _as_bool(signals.get("work_authorization_blocker")):
        risk += 0.30
        review_flags.append("work-authorization-risk")
        notes.append("work authorization or visa blocker by JD semantics → risk +0.30")

    source_confidence = _norm_level(signals.get("source_confidence"))
    if source_confidence in {"snippet", "search_result", "aggregate", "blocked", "login_gated"}:
        review_flags.append("source-not-full-jd")

    if _as_bool(signals.get("pure_plc")):
        risk += 0.35
        review_flags.append("pure-plc")
    if _as_bool(signals.get("robotics_control_heavy")):
        risk += 0.20
        review_flags.append("robotics-control-heavy")

    return _clamp(risk), notes, review_flags


def _semantic_years(signals: dict[str, Any]) -> float | None:
    direct = _as_float(signals.get("years_required"))
    if direct is not None:
        return direct
    level = _norm_level(signals.get("seniority_level"))
    mapping = {
        "junior": 1.0,
        "entry": 1.0,
        "graduate": 1.0,
        "junior_mixed": 2.0,
        "mixed": 3.0,
        "mid": 3.0,
        "senior": 5.0,
        "lead": 7.0,
    }
    return mapping.get(level)


def _apply_save_policy(
    result: ScoreResult,
    *,
    save_threshold: float = 0.5,
    manual_review_on_flags: bool = True,
    hard_manual_check: bool = False,
) -> ScoreResult:
    if result.score < save_threshold:
        result.save_recommendation = "no"
    elif manual_review_on_flags and (result.review_flags or result.signal_conflicts):
        result.save_recommendation = "manual_review"
    else:
        result.save_recommendation = "yes"

    if hard_manual_check:
        result.save_recommendation = "manual_check_only"
    if any(flag.endswith("-primary") for flag in result.review_flags):
        result.save_recommendation = "manual_check_only"
    return result


def compute_score_from_signals(
    signals: dict[str, Any],
    *,
    save_threshold: float = 0.5,
    manual_review_on_flags: bool = True,
) -> ScoreResult:
    title = str(signals.get("title") or "")
    location = str(signals.get("location") or "")
    jd_excerpt = str(signals.get("jd_excerpt") or signals.get("requirement_evidence") or "")
    work_mode = _norm_level(signals.get("work_mode")) or "auto"
    if work_mode not in {"auto", "onsite", "hybrid", "remote"}:
        work_mode = "auto"

    technical = _as_float(signals.get("technical_score"))
    if technical is None:
        technical = _as_float(signals.get("technical_overlap_score"))
    if technical is None:
        technical = 0.50

    academic_track = _norm_level(signals.get("academic_track"))
    postdoc = _as_bool(signals.get("postdoc")) or academic_track == "postdoc"
    phd_required = _as_bool(signals.get("phd_required")) or _as_bool(signals.get("promotion_required"))

    semantic_risk, risk_notes, risk_flags = _semantic_risk_adjustments(signals)
    stack_risk, stack_cap, stack_notes, stack_flags = _semantic_stack_adjustments(signals)
    if stack_cap is not None:
        technical = min(technical, stack_cap)
    base_risk = _as_float(signals.get("risk_score")) or 0.0
    risk_score = _clamp(base_risk + semantic_risk + stack_risk)

    semantic_jd = jd_excerpt
    if postdoc:
        semantic_jd = f"{semantic_jd}\nPostdoc program"
    if phd_required:
        semantic_jd = f"{semantic_jd}\nPhD required"

    result = compute_score(
        technical,
        location,
        years_required=_semantic_years(signals),
        title=title,
        jd_excerpt=semantic_jd,
        work_mode=work_mode,
        risk_score=risk_score,
        apply_regex_stack=False,
    )

    result.notes.extend(risk_notes + stack_notes)
    result.review_flags.extend(risk_flags + stack_flags)
    result.source_confidence = str(signals.get("source_confidence") or "")

    conflicts: list[str] = []
    regex_stack_risk, _, regex_stack_notes = infer_cpp_csharp_risk(jd_excerpt, title=title)
    if regex_stack_risk >= 0.55 and stack_risk < 0.55:
        conflicts.append("regex-detected-cpp-csharp-primary-but-signals-did-not")
        result.review_flags.append("stack-signal-conflict")
        result.notes.extend(regex_stack_notes)
    if (postdoc or phd_required) and result.score >= 0.5:
        conflicts.append("academic-hard-filter-score-conflict")
    result.signal_conflicts = conflicts

    return _apply_save_policy(
        result,
        save_threshold=save_threshold,
        manual_review_on_flags=manual_review_on_flags,
        hard_manual_check=postdoc or phd_required,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compute job lead dimension scores")
    parser.add_argument("--technical", type=float, default=None, help="0-1 technical overlap")
    parser.add_argument("--location", default="", help="City/region/work-mode text")
    parser.add_argument("--years-required", type=float, default=None)
    parser.add_argument("--title", default="")
    parser.add_argument("--jd-excerpt", default="", help="Optional requirement snippet")
    parser.add_argument(
        "--work-mode",
        default="auto",
        choices=["auto", "onsite", "hybrid", "remote"],
    )
    parser.add_argument("--risk-score", type=float, default=0.0)
    parser.add_argument("--signals-json", default="", help="Agent-extracted lead signal JSON object")
    parser.add_argument("--signals-file", default="", help="Path to agent-extracted lead signal JSON")
    parser.add_argument("--save-threshold", type=float, default=0.5)
    parser.add_argument(
        "--allow-review-flag-save",
        action="store_true",
        help="Return yes for score-qualified leads with non-hard review flags.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    args = parser.parse_args(argv)

    if args.signals_json or args.signals_file:
        result = compute_score_from_signals(
            _load_signals(args.signals_json or None, args.signals_file or None),
            save_threshold=args.save_threshold,
            manual_review_on_flags=not args.allow_review_flag_save,
        )
    else:
        if args.technical is None:
            parser.error("--technical is required unless --signals-json/--signals-file is provided")
        result = compute_score(
            args.technical,
            args.location,
            years_required=args.years_required,
            title=args.title,
            jd_excerpt=args.jd_excerpt,
            work_mode=args.work_mode,
            risk_score=args.risk_score,
        )

    if args.json:
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        return 0

    print(f"technical_score={result.technical_score}")
    print(f"location_score={result.location_score}  ({result.location_tier})")
    print(f"seniority_score={result.seniority_score}  (years_inferred={result.years_inferred})")
    print(f"risk_score={result.risk_score}")
    print(f"score={result.score}")
    print(f"save_recommendation={result.save_recommendation}")
    if result.review_flags:
        print(f"review_flags={','.join(result.review_flags)}")
    if result.signal_conflicts:
        print(f"signal_conflicts={','.join(result.signal_conflicts)}")
    for note in result.notes:
        print(f"note: {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
