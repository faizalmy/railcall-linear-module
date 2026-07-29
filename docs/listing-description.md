Batch-triage your Linear backlog behind a human approval gate.

Monday triage is thirty round trips in the UI. A script is faster, but nobody sees what it is about to change and nothing records who approved it. This module stages the whole batch as one command: RailCall previews it, a human approves once, and the run leaves a receipt bound to that exact payload.

**45 commands** across issues, teams, projects, users, workflow states, labels, cycles, comments, webhooks, milestones and initiatives. 18 reads run immediately; 27 writes are gated by the Approval Airlock.

## What sets it apart

- **Paste `ENG-123`** straight from the Linear URL — no hunting for a UUID
- **Real full-text search** — Linear's own engine, so descriptions and comments match, not just titles
- **Rate-limited mid-batch?** The command stops and returns `not_attempted`, so a re-run resumes where it left off
- **Mutations are never auto-retried** — Linear has no idempotency key, so a retry after an accepted write would duplicate it. Recovery is a fresh approval.
- **Initiatives** — roll projects up under a goal and post health updates (onTrack / atRisk / offTrack)

## Setup (two minutes)

Run `railcall studio`, open **Sends**, pick **Linear — API key + team**. The saved team becomes the default for every team-scoped command, so most calls never repeat the UUID.

## Security

The key lives in the station vault, read at call time. The published bundle contains zero `os.environ` reads. Nothing is persisted, logged, or written into a cache key; receipts store field names and a hash, never values. Stdlib `urllib` only — zero dependencies.

287 unit tests and 57 live tests against a real Linear workspace. MIT licensed.

[Source](https://github.com/faizalmy/railcall-linear-module) · [CI](https://github.com/faizalmy/railcall-linear-module/actions/workflows/ci.yml)

contest:2026Q3
