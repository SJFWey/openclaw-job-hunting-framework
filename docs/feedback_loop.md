# Feedback Loop

Feedback is intentionally explicit and append-only. The system should learn from repeated user decisions without silently rewriting durable memory.

## JSONL Path

Default local path:

```text
data/job_scout_feedback.jsonl
```

This file is ignored by git.

## Row Format

```json
{"date":"2026-05-31","action":"reject","rec_id":"REC-2026-012","reason":"far-south onsite and weak domain fit","source":"daily-report"}
```

Recommended fields:

- `date`: ISO date or datetime.
- `action`: `accept`, `reject`, or `ignore`.
- `rec_id`: recommendation id when available.
- `reason`: short reusable reason.
- `source`: where the feedback came from.
- `cluster`: optional search cluster.
- `company`: optional company.
- `role_pattern`: optional title or role pattern.

## User Commands

The agent can interpret messages such as:

```text
accept REC-2026-012
reject REC-2026-013 because senior C++ primary stack
ignore REC-2026-014 because already saw similar roles
```

The implementation can append a JSONL row and update tracker status when appropriate.

## Memory Policy

Preflight reads recent feedback and uses it as run context. It should not rewrite stable memory automatically.

After 3 or more consistent signals, the agent should propose a durable memory update, for example:

```text
Proposed MEMORY update: Downrank far-south onsite test roles unless remote/hybrid or score >= 0.82.
Evidence: 4 recent rejects.
```
