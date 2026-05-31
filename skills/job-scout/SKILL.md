---
name: job-scout
description: Discovers, scores, deduplicates, and records job leads for the job-search pipeline. Use when the user asks to find jobs, scout openings, review recommendations, add a lead, or promote a recommendation into an application.
---

# Job Scout

## What This Skill Does
Discovers new job leads, scores them, deduplicates them, and writes validated leads to the recommendations sheet.
On user acceptance, promote leads into full applications via the `job-intake` flow.

## Workflow
1. Load explicit preferences from `docs/profile.md`.
2. Load stable preferences and scoring rules from `MEMORY.md`.
3. Load the search keyword pack from `docs/agent_job_search_keywords.json` and search-quality tuning from `docs/job_scout_tuning.yaml` (see `scripts/search_keywords.py` and `scripts/job_scout_tuning.py`); use preflight output when present. Build daily queries from that config-driven plan before generic guessing.
4. When the JD or lead description is strongly technical, read **only the matching canonical** narratives (`docs/<Name>.md` without `-Hintergrund`; see `TOOLS.md`). Use them to justify fit and to avoid generic scoring. Optional: `docs/<Name>-Hintergrund.md` for deeper stack/domain matching — scoring still follows canonical claim bounds. Skip for non-technical or broad leads.
5. Extract implicit signals from recent `applications` and `recommendations` history.
6. If a stable preference pattern appears, summarize the evidence and ask before updating `MEMORY.md`.
7. Read `docs/target_companies.md` and start with relevant direct company career pages when the search scope matches the target pool.
8. Use the preflight `Search plan` as the daily scouting execution baseline. Cover role clusters, source families, location bands, freshness intent, and validation intent before narrowing to obvious CV/profile terms.
9. Run scouting in two phases:
   - **Broad candidate pool:** collect a wide, shallow set across the search/exploration matrix. Do not overfit to the candidate's most prominent experience keywords; include adjacent sensor, metrology, validation, application-engineering, and junior engineering clusters when configured.
   - **Validation queue:** choose the most promising candidates for full-JD validation based on source confidence, freshness, role cluster coverage, and likely fit. Do not spend full validation budget only on the first obvious search family.
10. Collect job leads from search results. Treat provider filters as hints, not guarantees.
   - Check posting freshness early. Jobs published more than 1 month ago should not be considered for validated recommendations; if date is missing/old but a direct company/ATS page clearly proves the posting is still active and the fit is unusually strong, keep it as Manual-check with the caveat.
11. Before scoring a validated-save candidate, use LLM semantic reading of the JD to extract structured lead signals. Do this for every full-JD candidate, not just obvious edge cases. Include:
   - `title`, `company`, `location`, `work_mode`, `source_confidence`
   - `source_type`, `platform`, `published_date`, `posted_date`, `application_deadline`, `active_direct_page`, `expired` when known
   - `technical_score` (0-1) and compact evidence
   - `cpp_requirement_level`, `csharp_requirement_level`, `python_requirement_level`: `none`, `optional`, `secondary`, `important`, `primary`, or `unclear`
   - `seniority_level`, `years_required`, `academic_track`, `phd_required`, `postdoc`
   - `travel_level`, `visa_blocker` / `work_authorization_blocker`, `pure_plc`, `robotics_control_heavy`
   - `published_date`, `application_deadline`, or direct-page active evidence; stale postings older than 1 month are Manual-check/reject by default.
   Save the JSON temporarily and pass it to `score_lead.py --signals-file`.
12. Score each lead with dimensions before assigning the final 0.0-1.0 score. **Read `references/scoring-rubric.md`** and prefer the deterministic helper:
   ```sh
   uv run python scripts/score_lead.py --signals-file /tmp/lead_signals.json --json
   ```
   Run the policy decision helper before every validated save:
   ```sh
   uv run python scripts/lead_decision.py --signals-file /tmp/lead_signals.json --json
   ```
   Treat `lead_decision.py` as the save policy gate: `validated_candidate` may be saved after dedupe; `manual_check`, `backup`, and `reject` must not be saved as validated recommendations.
   Use its output for tracker fields unless you have a documented override reason.
   - `technical_score` (weight **0.35**): CV/3D/industrial vision/testing overlap — agent-assessed.
   - `location_score` (weight **0.34**): commute from **Clausthal-Zellerfeld**; **strong penalty** for far south (e.g. München ~0.15–0.22 onsite).
   - `seniority_score` (weight **0.26**): junior/entry fit vs multi-year or senior-heavy requirements — **strong penalty** for 3+/5+ years.
   - `risk_score` (weight **0.05**, lower is better): travel, PLC-only, robotics-control-heavy, language, work-authorization, inactive posting.
   - Formula: `score = 0.35*technical + 0.34*location + 0.26*seniority + 0.05*(1-risk)`.
   - `seniority_fit`: e.g. junior, mixed, senior-heavy.
   - `domain_fit`: e.g. calibration, 3d, aoi, validation, detection-tracking, lidar, automation-adjacent.
   - `risk_flags`: compact comma-separated risk labels (include `cpp-csharp-primary` when proficient C++/C# is required).
   - If `save_recommendation` is `manual_check_only`, do not save it as a validated recommendation.
   - If `review_flags` or `signal_conflicts` are returned, keep the lead in Manual-check unless the report explicitly resolves the issue.
   - Do **not** save C++/C#-**first** roles (Developer title, sehr gute/fundiert C++ or C# alone). Python-primary JDs with `C++/Python` may be saved with a weak-C++ note in `reason`.
   - Exclude Postdoc programs from validated recommendations. PhD/Promotion-required roles should be manual-check or rejected. Wissenschaftliche*r Mitarbeiter*in roles are allowed when they are not Postdoc/PhD-required and the fit/location are plausible.
13. Verify the original job page before saving whenever possible.
    - Verify posting freshness where possible. Do not validated-save postings published more than 1 month ago unless the direct company/ATS page clearly shows the role is still active and the report explains the exception.
    - For LinkedIn/StepStone/search-result leads with only snippets, keep them in a separate `Manual-check links` section unless full body metadata is available.
    - For LinkedIn guest search, dismiss sign-in/cookie modals in the browser and extract title/company/location/date/link from the results list; use these as manual-check candidates, not validated recommendations by default.
    - Do not bypass anti-bot controls, login walls, or access restrictions. If the page is blocked, login-gated, cookie-shell-only, or snippet-only, downgrade to Manual-check and look for a public direct company/ATS alternative.
    - WeAreDevelopers and individual StepStone/Indeed pages can sometimes expose full job bodies for validation when LinkedIn only gives snippets.
    - When the user asks whether prior daily recommendations were recorded, distinguish tracker-backed validated recommendations from Manual-check links: validated score-qualified leads are stored in the Recommendations sheet; access-limited Manual-check links are normally report-only unless enough reliable metadata exists to save them.
14. Deduplicate: skip if normalized URL already exists, then check company+position+location.
    - In scheduled/heartbeat runs, re-read or validate the tracker immediately before and after adding recommendations; another concurrent run may have added adjacent REC IDs or equivalent company/title leads after your initial snapshot.
    - If you accidentally add a same-company/same-role duplicate under an alternate title/URL, do not delete it during heartbeat; mark the later/less canonical recommendation `rejected` with `decision_reason="Duplicate of REC-..."`, then run `validate` and `dedupe-recs --dry-run`.
15. Write qualifying validated leads (score >= 0.5) to recommendations sheet with source type, score dimensions, fit labels, risk flags, and short reason.
16. Present `Today’s best actions` first: top validated leads or manual checks with priority, compact score/risk, and one application angle. Then separate `Saved recommendations`, `Manual-check queue`, `Rejected/noise patterns`, and `Search coverage`.
    - In Search coverage, mention cluster/source/location breadth and any leads blocked by source/freshness policy.
    - Treat acceptance rate as the main long-term quality signal; saved count alone is not the success metric.
17. Append scouting diagnostics to `docs/search_diagnostics.md` when a run reveals useful repeated noise, stale sources, or strong source patterns. If the file does not exist yet, create it with a dated run note rather than treating that as an error.
    - Before patching diagnostics, re-read the file if the edit tool reports an external modification; heartbeat/scouting runs can update it between your first read and write.
18. For daily mass-application heartbeat reports, use the configured validated/manual targets from `docs/job_scout_tuning.yaml`; explicitly explain if fewer are found due to coverage, duplicates, access restrictions, source failures, freshness, or weak relevance.
19. If user says "take this one" or "intake", call `tracker_ops.promote_recommendation_to_application()` only after a short application-readiness review.

## References
- `references/scoring-rubric.md` — dimension weights, location tiers from Clausthal-Zellerfeld, seniority penalties, and `score_lead.py` usage.
- Workspace `docs/agent_job_search_keywords.json` — personal keyword/query pack (`scripts/search_keywords.py`).
- Workspace `docs/job_scout_tuning.yaml` — configurable search breadth, freshness, validation depth, source priority, score thresholds, and feedback loop controls (`scripts/job_scout_tuning.py`).
- `scripts/search_plan.py` — default exploration matrix for broader source/cluster/location coverage.
- `scripts/lead_decision.py` — source/freshness/score policy gate before validated saves.
- `references/daily-heartbeat-source-patterns.md` — recurring source/validation patterns for the mass-application scouting heartbeat.
- `references/cron-heartbeat-troubleshooting.md` — diagnosis and recovery notes for missing/paused/removed daily job-scouting cron jobs.

## OpenClaw Cron Operations
- Daily scouting is owned by OpenClaw Cron job `95f0899bca1d` / `Daily job scouting`, `sessionTarget=isolated`, schedule `0 8 * * *` Europe/Berlin.
- Preserve the operating shape unless the user asks otherwise: agent `job-hunter`, workspace `/home/xjwei/.openclaw/workspace-job-hunter`, launcher `cron-prompts/daily-job-scouting.txt`, checklist `HEARTBEAT.md`, preflight `scripts/job_scouting_preflight.py`.
- The preflight prints runtime health, tuning profile, source priority, freshness/depth settings, tracker health, duplicate dry-run status, a rotated daily search plan, target-company focus, recent recommendations, feedback summary, and diagnostics.
- For Telegram topics, keep cron `delivery.threadId` and `failureAlert.threadId` explicit when the intended conversation is a topic; otherwise OpenClaw delivery fallback can drift to a stale topic.
- Verify with `openclaw cron list --all`, `openclaw cron get 95f0899bca1d`, and `uv run python scripts/job_scouting_preflight.py --dry-run` after cron or preflight changes.

## Preference Learning
- Monitor which recommendations the user accepts vs. ignores/rejects.
- Capture short rejection or ignore reasons in `decision_reason` whenever the user provides one.
- Treat `data/job_scout_feedback.jsonl` as short-term tuning input for query/source/cluster hints.
- After 3+ consistent signals, propose updating `MEMORY.md` scoring rules and wait for user confirmation.
- Always explain why a lead was scored high; make scoring transparent.
- Do not write durable memory from scouting alone without explicit approval.

## CLI Integration
```sh
# Add a lead manually
uv run python scripts/job_scout_tuning.py

uv run python scripts/tracker_ops.py add-rec "Company" "Position" \
    --url "https://..." --platform LinkedIn --source-type job-board \
    --score 0.85 --technical-score 0.9 --location-score 0.8 \
    --seniority-score 0.8 --risk-score 0.1 \
    --domain-fit calibration --seniority-fit junior \
    --risk-flags "" --reason "3D calibration + Northern Germany"

# Promote to application
uv run python scripts/tracker_ops.py promote-rec-to-app REC-2026-001

# List leads
uv run python scripts/tracker_ops.py list-recs

# Check tracker health and duplicates
uv run python scripts/tracker_ops.py validate
uv run python scripts/tracker_ops.py dedupe-recs --dry-run
```

## Key Paths
- Tracker: `data/applications.xlsx`
- Preferences: `docs/profile.md`, `MEMORY.md`
- Search keywords: `docs/agent_job_search_keywords.json` (user-maintained; copy from `agent_job_search_keywords_xianjian_wei.json`)
- Search tuning: `docs/job_scout_tuning.yaml`
- Explicit feedback: `data/job_scout_feedback.jsonl`
- Target companies: `docs/target_companies.md`
- Search diagnostics: `docs/search_diagnostics.md`
- Technical narratives (scoped): canonical `docs/<Name>.md`; optional depth `docs/<Name>-Hintergrund.md`—see `TOOLS.md`
- Daily logs: `memory/YYYY-MM-DD.md`
- OneDrive root: `/mnt/onedrive/Jobsuche/Bewerbungsunterlagen`
