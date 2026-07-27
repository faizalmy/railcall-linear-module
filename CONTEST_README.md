# Linear for RailCall

**contest:2026Q3**

Batch-triage a Linear backlog with a human approval gate and a signed receipt.

## The problem

Monday triage is death by a thousand clicks. Thirty issues came in over the
weekend, each needing an owner, a priority and a state — thirty round trips in
Linear's UI. Scripting it is fast but unreviewable: nobody sees what is about to
change, and nothing records who approved it.

## What this does

One command stages the whole batch. RailCall renders a preview, a human
approves once, and the run emits a signed receipt naming the approver and the
exact payload.

```bash
railcall market install agentstack-labs/linear
```

```json
{ "command": "linear.bulk_update_issues",
  "inputs": { "issue_ids": ["<uuid>", "..."],
              "assignee_id": "<uuid>", "state_id": "<uuid>", "priority": 2 } }
```

If Linear rate-limits mid-batch the command stops and returns `not_attempted`,
so a re-run resumes exactly where it left off instead of redoing the work.

## Who it is for

Small engineering teams whose triage, sprint setup and release bookkeeping live
in Linear, and who need an audit trail because someone eventually asks "who
closed those twelve tickets?"

## Setup (about two minutes)

1. Generate a key at **Linear → Settings → API**.
2. Run `railcall studio`, open the **Sends** tab, choose **Linear — API key +
   team**, and save both `api_key` and `team_id` (the form requires both; the
   team UUID is in your team settings URL). There is no CLI equivalent.
3. Run `linear.list_teams` to confirm it works. The saved team is the default
   for every team-scoped command, so most calls never repeat the UUID.

The key is read at call time from the vault. The published bundle contains no
credential environment read at all — the build strips them, since it only runs
inside the Studio. The key is never written to disk, logged, or put in a cache key.

## Scope

45 commands across issues, teams, projects, users, states, labels, cycles,
comments, webhooks, milestones and **initiatives** — Linear's roadmap, where
projects roll up under a goal and carry health updates. Search uses Linear's own engine, so descriptions and comments match. 18 reads
run immediately; 27 writes are gated by the Airlock.

## Known limitations

- **UUIDs only** for issues, states and labels; no `ENG-123`. The team UUID is
  the exception — it defaults to the one saved with the key.
- **Milestones are project-scoped.** `create_milestone` requires a `project_id`;
  Linear has no workspace-level milestone.
- **`create_webhook` needs a scope** — one of `team_id` or `all_public_teams`.
- **API key auth only.** No OAuth2 in this release.
- **Caching covers metadata only** (teams, projects, users, states, labels),
  5-minute TTL. Issue and comment reads are never cached.
- **Mutations are never auto-retried.** Linear has no idempotency key, so a retry
  after an accepted write would duplicate it. Recovery is a fresh approval.

## Verification

240 unit tests and 56 live tests against a real Linear workspace; all 45
commands exercised end-to-end. Full source, architecture notes and the bundle
build tool: <https://github.com/faizalmy/railcall-linear-module>

MIT licensed.
