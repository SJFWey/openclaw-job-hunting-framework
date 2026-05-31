# OpenClaw Job Hunting Framework

Skills-based job-hunting workflow for the OpenClaw agent harness. The framework defines scouting, intake, materials, and pipeline skills plus deterministic guardrail scripts. LLM execution happens in OpenClaw at runtime—not inside this repository's Python code.

Read [FRAMEWORK.md](FRAMEWORK.md) for the three-layer model, skill graph, and LLM vs script division.

## What Is in Git

| Path | Role |
|------|------|
| `skills/` | Agent runbooks (scout, intake, cover letter, packet, pipeline, …) |
| `scripts/` | Preflight, scoring, tracker, tuning, keywords |
| `docs/` | Architecture, setup, report contract, tuning YAML |
| `tests/` | Unit tests and signal fixtures |

Runtime bootstrap files (`AGENTS.md`, `HEARTBEAT.md`, `MEMORY.md`, …), candidate profiles, tracker workbooks, and generated materials stay on disk but are **gitignored**.

## Prerequisites

- OpenClaw gateway and a configured agent workspace
- Python 3.11+ with workspace venv
- Model provider configured in OpenClaw (e.g. GPT-5.5)

## Quickstart (Framework Scripts)

From the workspace root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[yaml]"
python -m unittest discover -s tests
python scripts/job_scout_tuning.py
python scripts/job_scouting_preflight.py --dry-run
```

Scoring smoke test:

```bash
python scripts/score_lead.py \
  --signals-file tests/fixtures/signals/python_cv_secondary_cpp.json \
  --json
```

## OpenClaw Setup

See [docs/openclaw_setup.md](docs/openclaw_setup.md) for workspace layout, runtime bootstrap files, cron wiring, and preflight environment variables.

## Safety Model

- Scout, score, dedupe, and recommend — yes.
- Save validated leads to the local tracker when present — yes.
- Send applications or external messages — **no** (explicit user approval required).
- Auto-write durable memory from feedback — **no** (propose updates; user confirms).

## Repository

Public framework repo: [github.com/SJFWey/openclaw-job-hunting-framework](https://github.com/SJFWey/openclaw-job-hunting-framework)

Runtime bootstrap files, candidate profiles, and tracker data remain gitignored locally even when pushing framework updates.

## Further Reading

- [FRAMEWORK.md](FRAMEWORK.md) — architecture and skill graph
- [docs/architecture.md](docs/architecture.md) — component diagram
- [docs/report_contract.md](docs/report_contract.md) — daily scouting report shape
- [docs/job_scout_tuning.yaml](docs/job_scout_tuning.yaml) — search-quality control file
