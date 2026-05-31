# OpenClaw Setup

This framework lives inside an OpenClaw agent workspace. Platform config is outside this repo; framework files are tracked in git; runtime bootstrap and candidate data are local and gitignored.

See [FRAMEWORK.md](../FRAMEWORK.md) for the three-layer model.

## 1. Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[yaml]"
```

Optional PDF helpers:

```bash
pip install -e ".[pdf,yaml]"
```

## 2. Register the Agent (Platform)

In `~/.openclaw/openclaw.json`, point an agent at this workspace and register framework skills:

- `workspace`: path to this directory
- `skills`: `job-scout`, `job-intake`, `cover-letter`, `application-packet`, `pipeline`, `candidate-materials`, `pdf`

Model and channel bindings are platform concerns, not framework files.

## 3. Create Runtime Bootstrap Files

Create these at the workspace root (gitignored). They define your agent instance—not the reusable framework:

- `AGENTS.md` — role, scope, safety, scheduled work pointers
- `HEARTBEAT.md` — daily cron checklist (references `job-scout` skill)
- `MEMORY.md` — durable preferences and scoring heuristics (user-approved writes only)
- `TOOLS.md` — paths, commands, workspace-specific runbook
- `SOUL.md`, `IDENTITY.md`, `USER.md` — persona and user context

If migrating from an existing Harvey workspace, these files may already exist locally.

## 4. Create Candidate Overlay (Runtime)

Add private search and profile inputs (all gitignored):

- `docs/profile.md`
- `docs/agent_job_search_keywords.json` (see anonymized shape in `tests/fixtures/agent_job_search_keywords.example.json`)
- `docs/target_companies.md`
- `docs/search_diagnostics.md` (optional; appended during scouting runs)
- Project narratives under `docs/` as needed for cover-letter matching

## 5. Create Local Runtime Data

```bash
python scripts/tracker_ops.py init
mkdir -p data
touch data/job_scout_feedback.jsonl
```

Files under `data/` are runtime state and must not be committed.

## 6. Configure Preflight

The preflight script discovers the workspace from its own location. Override with environment variables when needed:

```bash
export JOB_HUNTER_WORKDIR="$PWD"
export JOB_HUNTER_TRACKER="$PWD/data/applications.xlsx"
export JOB_HUNTER_TUNING_CONFIG="$PWD/docs/job_scout_tuning.yaml"
export JOB_HUNTER_FEEDBACK_LOG="$PWD/data/job_scout_feedback.jsonl"
export JOB_HUNTER_KEYWORD_PACK="$PWD/docs/agent_job_search_keywords.json"
export OPENCLAW_JOB_SCOUT_CRON_ID="<your-openclaw-cron-id>"
```

Verify:

```bash
python scripts/job_scouting_preflight.py --dry-run
```

## 7. Cron Prompt

Copy [cron-prompts/daily-job-scouting.example.txt](../cron-prompts/daily-job-scouting.example.txt) to a live cron message (e.g. `cron-prompts/daily-job-scouting.txt`) with your workspace path. Register in `~/.openclaw/cron/jobs.json`:

- `payload.kind`: `agentTurn`
- Run preflight first; inject stdout into agent context
- Respect final wake-gate JSON (`wakeAgent` true/false)
- Follow [docs/report_contract.md](report_contract.md)

## 8. Before Pushing to a Remote

```bash
git status --short
git ls-files
```

Only framework paths should appear. Bootstrap markdown, profiles, resumes, tracker workbooks, feedback logs, and generated packets must stay untracked.
