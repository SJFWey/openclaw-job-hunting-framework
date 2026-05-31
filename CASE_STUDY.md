# Case Study: Skills-Based Job Scouting on OpenClaw

This repository is a practical case study in designing an LLM-assisted workflow
on top of an agent harness. Job hunting is the concrete domain, but the main
subject is system design: which work belongs to deterministic scripts, which
work benefits from LLM judgment, how tools and skills are coordinated, and where
human approval remains mandatory.

## Problem Context

Daily job scouting is messy production work. Sources change, postings expire,
job boards hide content behind login walls, search results overfit to obvious
keywords, and a single numeric score can hide important trade-offs. The system
must remain useful for daily job search while also being transparent enough to
debug and improve.

The design goal is not to automate applications. The goal is to turn a noisy
search problem into a structured workflow that produces traceable
recommendations and clear manual-check queues.

## Production Constraints

- Search sources have uneven reliability: direct company pages and ATS pages
  are usually stronger than aggregate snippets or login-gated boards.
- Freshness matters: stale or expired postings should not become validated
  recommendations unless a direct source proves the role is still active.
- Runtime data is private: CVs, tracker workbooks, daily memory, and candidate
  preferences stay in the local overlay and are not committed.
- The daily workflow must remain explainable while it evolves, so search
  coverage and source/freshness gates are explicit script-level contracts.
- The system must be explainable: every recommendation needs a source,
  freshness, score, risk, and next-action rationale.

## LLM Capability Boundaries

LLMs are used where semantic judgment matters:

- reading job descriptions and extracting structured signals,
- identifying domain overlap and application angles,
- summarizing search coverage and missed targets,
- drafting reports and application materials,
- interpreting user feedback in natural language.

LLMs are not trusted with tasks that need stable invariants:

- query budget and coverage planning,
- score formulas and hard gates,
- freshness/source policy,
- tracker CRUD and deduplication,
- cron wake gates and runtime health checks.

Those parts are handled by scripts and tests.

## Workflow Architecture

The system has three layers:

- **Platform:** OpenClaw provides cron turns, model routing, tools, and delivery.
- **Framework:** this repository provides skills, guardrail scripts, tests, and
  public contracts.
- **Runtime:** private local data provides candidate profile, tracker, daily
  memory, and materials.

The daily scouting loop is:

1. `job_scouting_preflight.py` checks runtime health, tracker state, tuning, and
   recent diagnostics.
2. `search_plan.py` produces the exploration matrix across role clusters,
   source families, locations, freshness, and validation intent.
3. The OpenClaw agent uses the `job-scout` skill to search, read pages, extract
   lead signals, and separate broad discovery from validation.
4. `score_lead.py` computes deterministic dimension scores.
5. `lead_decision.py` applies source/freshness/manual-check policy before
   validated saves.
6. `tracker_ops.py` records only validated recommendations after dedupe.
7. The report separates saved recommendations, manual-check links, rejected
   patterns, and search coverage.

## Human Decision Points

The human remains responsible for decisions with external consequences:

- approving applications,
- sending external messages,
- accepting or rejecting recommendations,
- updating durable memory from repeated feedback,
- approving any override when a lead is blocked by source/freshness policy.

The system can propose, rank, explain, and prepare. It does not submit or
communicate externally without explicit approval.

## Failure Modes and Mitigations

| Failure mode | Mitigation |
|--------------|------------|
| Search overfits to obvious CV keywords | Exploration matrix forces cluster/source/location breadth |
| Job board blocks access or exposes only snippets | Downgrade to Manual-check and look for public direct/ATS sources |
| Old postings look attractive | Freshness policy prevents validated saves unless active direct evidence exists |
| Single score hides source risk | `lead_decision.py` separates score from source and freshness policy |
| Framework changes disrupt daily use | Planner and policy gates are deterministic, tested, and side-effect free |
| Private candidate data leaks into public repo | Runtime overlay is gitignored and public tests use synthetic fixtures |

## Lessons Learned

The useful unit of design is not a prompt. It is a coordinated workflow:
contracts, scripts, skills, runtime state, LLM judgment, tool use, and human
approval boundaries. The LLM is strongest when the surrounding system gives it
structured context and deterministic guardrails; the fixed workflow is strongest
when it delegates semantic ambiguity back to the LLM instead of pretending every
decision is a static rule.
