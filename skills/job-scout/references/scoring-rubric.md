# Job Lead Scoring Rubric

Home base for commute distance: **Clausthal-Zellerfeld** (Harz, Niedersachsen).  
Candidate level: **junior / entry** (recent M.Sc.; ~0–1 years full-time industry experience).

Use this rubric for every validated save. The agent should first read the JD semantically and extract structured signals; the deterministic helper then applies fixed scoring, hard caps, and conflict flags.

```bash
uv run python scripts/score_lead.py --signals-file /tmp/lead_signals.json --json
```

Use legacy direct flags only for quick manual checks. For cron/validated saves, prefer signals JSON so nuanced JD wording such as C++ importance, travel burden, academic track, and source confidence is captured by LLM semantic reading before rule-based scoring.

## Dimension weights (final score)

| Dimension | Weight | Notes |
|-----------|--------|-------|
| `technical_score` | **0.35** | CV/3D/vision/testing overlap (agent-assessed) |
| `location_score` | **0.34** | **Strong penalty for far south / long commute** |
| `seniority_score` | **0.26** | **Strong penalty for multi-year experience requirements** |
| `(1 - risk_score)` | **0.05** | `risk_score` 0–1, lower is better |

**Formula**

```
score = 0.35 * technical_score
      + 0.34 * location_score
      + 0.26 * seniority_score
      + 0.05 * (1 - risk_score)
```

Round final score to two decimals. Always store all four dimension scores in the tracker.

## Location score (from Clausthal-Zellerfeld)

Assess the **primary work location** (onsite/hybrid office). Remote roles use the remote rules below.

| Tier | Examples | `location_score` | Typical one-way travel |
|------|----------|------------------|------------------------|
| A — local | Clausthal-Zellerfeld, Goslar, Osterode, Bad Harzburg, Nordhausen | 0.95–1.00 | ≤ ~45 min |
| B — close North | Braunschweig, Göttingen, Hildesheim, Hannover, Wolfsburg, Salzgitter | 0.88–0.94 | ~1–1.5 h |
| C — northern ~2 h | Hamburg, Bremen, Lübeck, Wedel, Kiel, Magdeburg, Kassel, Oldenburg | 0.82 | ~1.5–2.5 h |
| D — ~3 h (acceptable) | Berlin, Leipzig, Dresden, Rostock, Osnabrück, Erfurt | 0.70 | ~2.5–3 h |
| E — central / NRW | Dortmund, Essen, Düsseldorf, Köln, Bonn, Bielefeld, Münster | 0.52 | ~3.5–4+ h |
| E — far south / southwest | Frankfurt, Stuttgart, Nürnberg, Freiburg, Karlsruhe | 0.28–0.47 | ~4–5 h |
| F — very far south | **München**, Augsburg, Regensburg, Ulm, Ingolstadt | **0.15–0.22** | **~5–6+ h** |

**Work-mode adjustments** (apply after tier base, cap at 1.0):
- **Fully remote (Germany)**: set `location_score` ≥ **0.88** unless timezone/travel caveats apply.
- **Hybrid**: `min(1.0, office_tier_score + 0.10)`.
- **Onsite**: use office tier only — **no bonus**.

When a posting lists multiple cities, score the **worst** plausible office the candidate would need to reach regularly.

## Seniority / experience score

Candidate baseline: recent graduate; internships/HiWi count as learning, not as satisfying "3+ years professional experience".

| Requirement signal | `seniority_score` |
|--------------------|-------------------|
| Entry / Junior / Graduate / Trainee / Werkstudent / HiWi / ≤ 1 yr | 0.92–1.00 |
| "1–2 years" / "some experience" / Berufseinsteiger with soft preference | 0.78–0.91 |
| "2–3 years" | 0.62–0.77 |
| "3–5 years" | 0.42–0.61 |
| "5+ years" / Senior / Lead / Principal / Expert (without Junior) | **0.12–0.32** |
| **Wissenschaftliche*r Mitarbeiter*in** without Postdoc/PhD requirement | Score normally; add academic/fixed-term caveat |
| PhD / Promotion **required** | **≤ 0.20** |
| Postdoc program / Postdoc track | **≤ 0.12** |

**Title overrides** (apply the lower cap):
- Title contains Senior/Lead/Principal/Staff/Expert → cap `seniority_score` at **0.38** unless JD explicitly says Junior/Entry.
- "Mehrjährige Berufserfahrung" without number → treat as **≥ 3 years** (score ≤ 0.61).

## Risk score (0 = low risk, 1 = high risk)

Additive flags (cap at 1.0):
- Long-term frequent travel: +0.25
- Pure PLC / pure automation maintenance: +0.35
- Robotics-control-heavy, vision minor: +0.20
- **C++/C# as primary stack** (Developer title, sehr gute/fundiert C++ or C# alone): **+0.55** — usually **do not save**
- **Python/CV-primary** with secondary C++/Python pair (e.g. integration): **+0.18** — save only if candidate accepts light C++ touch; note in `reason`
- Optional C++ mention alongside clear Python/PyTorch primary: +0.10
- Language/work-authorization blocker: +0.30
- Stale/unverified posting: +0.20

## Thresholds

- **Save validated** recommendation: `score >= 0.5` (mass-application phase).
- **High-fit label** in reports: `score >= 0.8`.
- A strong technical match **does not** override far location, heavy experience, **C#/C++-first stack**, **Postdoc**, or **PhD/Promotion-required** tracks — final score is capped at **0.47–0.48** for those cases.

## Reporting transparency

In `reason`, briefly cite:
- technical overlap
- location tier + commute note (e.g. "München ~5–6h from Clausthal → location 0.22")
- experience requirement vs junior profile (e.g. "5+ yrs required → seniority 0.30")
