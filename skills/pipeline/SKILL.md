---
name: pipeline
description: Manages application status, follow-ups, tracker queries, and archival. Use when the user asks about active applications, status changes, overdue follow-ups, pipeline stats, rejected or withdrawn applications, or tracker hygiene.
---

# Pipeline

## What This Skill Does
Manages application status, follow-ups, queries, and archival.

## Workflows

### Status Update
- Parse natural language intent (e.g. "I got rejected from Acme").
- Map to status enum: draft / submitted / screening / interview / offer / rejected / withdrawn / terminal.
- For terminal changes signaled by the user (rejected, withdrawn, abandoned, not continuing), treat status update and application-material archival as one combined operation. Do not ask for a separate confirmation unless the matching application or material folder is ambiguous.
- Call `tracker_ops.update_application_status()` or `tracker_ops.mark_terminal()` as appropriate.
- Archive the related application materials after the tracker update when status is terminal.
- Log change in daily memory file.

### Query
- Active applications: filter by status not in {rejected, withdrawn, terminal}.
- By platform, location, date range.
- Stats: count by status, average time in each stage.

### Follow-up
- `tracker_ops.due_followups(days=7)` to list overdue.
- Log follow-up event with `tracker_ops.add_followup()`.

### Recommendation Feedback
- When the user ignores or rejects a recommendation and gives a reason, update both status and `decision_reason`.
- Keep reasons short and reusable: too far, too senior, PLC-only, robotics-control-heavy, frequent-travel, weak-domain-fit, company-not-interesting, can-wait.
- After 3+ repeated reasons, propose a durable preference update; do not silently change `MEMORY.md`.

### Archive / Terminal
- Terminal statuses: rejected, withdrawn, offer-accepted.
- `tracker_ops.mark_terminal()` marks application as terminal.
- Terminal applications excluded from follow-up reminders.

## CLI Integration
Run tracker commands from the job-hunting workspace that contains `scripts/tracker_ops.py` and `data/applications.xlsx`. If the current directory is not that workspace, locate it first rather than assuming repo-local paths.

```sh
uv run python scripts/tracker_ops.py list-apps --status submitted
uv run python scripts/tracker_ops.py update-app APP-2026-001 interview
uv run python scripts/tracker_ops.py due-followups --days 7
uv run python scripts/tracker_ops.py add-followup APP-2026-001 --channel email
uv run python scripts/tracker_ops.py update-rec-status REC-2026-001 rejected --decision-reason "too senior"
```

## Verification
- After any status update, verify with a filtered list command for the target status, e.g. `list-apps --status rejected`.
- For natural-language rejection notices, identify the matching submitted/screening application first, then update that exact APP id.
- Log the change in the daily workspace memory file; if the date file does not exist, create it with a concise bullet.

## Key Paths
- Tracker: `data/applications.xlsx` inside the job-hunting workspace
- Daily workspace log: `memory/YYYY-MM-DD.md` inside the job-hunting workspace
- Final materials: `/mnt/onedrive/Jobsuche/Bewerbungsunterlagen`
