---
name: job-intake
description: Converts one or more job postings into tracked, folder-backed application entries. Use when the user sends a job posting URL, asks to add a job to the tracker, create an APP-ID, save a JD, or start a new application.
---

# Job Intake

## What This Skill Does

Converts a job posting URL into a fully tracked, folder-backed application entry.

## Workflow

1. Extract one or more job posting URLs from conversation.
2. Fetch page content (company, position, location, JD text, source platform).
3. Show structured summary to user.
4. Run an application-readiness review before writing anything:
   - job page is active or JD text is manually confirmed,
   - no obvious hard blocker (work authorization, native-level language, seniority, long-term travel),
   - company and role are worth an application,
   - 2-3 candidate selling points are identified,
   - likely evidence sources are named (e.g. Masterarbeit, AOI, Perception2D, HiWi, Fraunhofer).
5. Get user confirmation.
6. Check `scripts/tracker_ops.py validate` output and existing applications/recommendations for duplicates.
7. Call `tracker_ops.add_application()` to assign APP-ID and write to workbook.
8. Create job folder in OneDrive: `/mnt/onedrive/Jobsuche/Bewerbungsunterlagen/<Company>/<Position [APP-ID]>/`
9. Save `JD.md` to the job folder.
10. Update `folder_path` and `jd_path` in tracker via `tracker_ops.update_application_paths()`.
11. Run tracker validation again and return intake summary with APP-ID and suggested next step.

## Inputs

- One or more job posting URLs (required)
- Optional: manual overrides for company, position, location

## Outputs

- APP-ID assigned
- Tracker row created (status: draft)
- OneDrive folder created
- `JD.md` saved

## CLI Integration

```sh
uv run python scripts/tracker_ops.py add-app "<Company>" "<Position>" \
    --source-url "<url>" --platform "<platform>" --location "<location>"
```

## Rules

- Always confirm with user before writing to tracker.
- If page fetch fails, ask user to paste JD text manually.
- Do not create duplicate entries; check existing applications first.
- OneDrive folder creation requires confirmed mount at `/mnt/onedrive`.
- Do not render cover letters or build packets from this skill; hand off to `cover-letter`.
- Do not promote a weak or unclear lead into an application without showing the readiness review and getting confirmation.
