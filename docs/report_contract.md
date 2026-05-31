# Daily Report Contract

The daily scouting report should be short, operational, and traceable. It should separate high-confidence recommendations from links that still need manual validation.

## Required Sections

### Today's Best Actions

1-5 highest-value actions for the day. Each item should include:

- lead or action name,
- why it matters now,
- compact score or risk,
- one application angle.

### Saved Recommendations

Validated leads saved to the tracker. Each row should include:

- title,
- company,
- location and work mode,
- source,
- score breakdown,
- reason for save,
- one application angle.

Only save when full-JD confidence is sufficient and the source policy allows validated saves.

### Manual-Check Queue

Plausible leads that should not be validated yet because of missing full JD, access limits, source failure, stale date, unclear seniority, or policy risk.

Include the `lead_decision.py` policy reason when it differs from the raw score,
for example: `decision=manual_check | source_policy=manual_check_only |
freshness=unknown_date`.

### Rejected / Noise Patterns

Summarize recurring rejected patterns, for example:

- senior-only search drift,
- C++/C# primary stack,
- PhD/Postdoc track,
- far-south onsite role,
- aggregate source without enough evidence,
- expired or stale posting.

### Search Coverage

Report what was searched:

- P0/P1/P2 query mix,
- search-plan cluster/source/location coverage,
- target-company checks,
- sources visited,
- freshness coverage,
- why validated or manual-check targets were missed.

## Scoring Format

Use compact scores:

```text
score=0.72 | technical=0.82 location=0.70 seniority=0.84 risk=0.10
```

Include review flags when present:

```text
manual_review: source-not-full-jd, csharp-secondary
```

## Missed Target Explanation

If fewer leads were saved than configured, explicitly state the blocker:

- duplicates,
- stale postings,
- no full JD,
- access-limited source,
- seniority mismatch,
- location mismatch,
- hard stack mismatch,
- weak domain fit.
