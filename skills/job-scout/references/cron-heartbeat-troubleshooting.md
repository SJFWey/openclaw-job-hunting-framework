# Daily Job-Scouting Heartbeat Cron Troubleshooting

Use this when the user asks why the daily JobScouting / job-scouting heartbeat did not fire.

## Fast diagnosis sequence
1. Check the scheduler and current jobs:
   - `cronjob(action="list")`
   - `hermes --profile job-hunter cron status`
   - `hermes --profile job-hunter cron list --all`
2. Inspect profile cron state if the tool shows no jobs:
   - `~/.hermes/profiles/job-hunter/cron/jobs.json`
   - The default profile `~/.hermes/cron/jobs.json` only matters if the job was created outside the `job-hunter` profile.
3. Check gateway logs for chronology:
   - `~/.hermes/profiles/job-hunter/logs/gateway.log`
   - Look for `Cron ticker started/stopped`, inbound user messages mentioning `cron`, `job-scout`, `heartbeat`, and delivery errors.
4. If the job is missing, search session transcripts for the previous job ID or job name:
   - Typical name: `Daily job scouting heartbeat`
   - Common prompt phrase: `daily job-scouting heartbeat`
   - A previous job ID may appear in the session where it was paused/removed.

## Interpretations
- Gateway running + `No active jobs` + `jobs.json` has `"jobs": []` means the heartbeat will not fire because no cron job exists.
- A paused job should still appear in `cron list --all` with `enabled: false` / `state: paused`; it can be resumed.
- If `jobs.json` is empty, there is no job to resume. Recreate the heartbeat instead.
- If a previous session shows `cronjob(action="pause")`, report it as paused at that time. If a later `jobs.json` update removed all jobs, state that it has since been removed/cleared.
- `last_status: error` with `last_delivery_error: null` means the job failed before producing a final report; do not diagnose it as a Telegram delivery failure.
- For Telegram topic/thread delivery, a target like `telegram:<chat_id>` can lose the topic. If logs warn that `origin has thread_id=... but delivery target lost it`, update the job delivery to the explicit three-part target `telegram:<chat_id>:<thread_id>` for the intended topic and verify with `cronjob(action="list")`.

## Reporting style
Be direct and concrete:
- State the root cause first.
- Include the job name, schedule, job ID, and last known state when available.
- Distinguish clearly between scheduler failure, delivery failure, paused job, and missing/removed job.
- Do not imply a gateway problem when the gateway is running and the cron list is empty.
