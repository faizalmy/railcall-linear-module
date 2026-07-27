# Linear for RailCall

**contest:2026Q3**

Batch-triage a Linear backlog with a human approval gate and a signed receipt.

## The problem

Monday triage is death by a thousand clicks. Thirty issues came in over the
weekend; they need an owner, a priority and a state. In Linear's UI that is
thirty round trips. Scripting it against the API is fast but unreviewable —
nobody sees what is about to change, and nothing records who approved it.

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
2. In **Studio → Sends → Configure**, save it under the `linear` provider as
   `api_key`. That vault entry is the only credential source inside the Studio;
   `LINEAR_API_KEY` applies to standalone/library use only.
3. Run `linear.list_teams` — every other command needs a team UUID.

The key is read at call time from the vault. The published bundle contains no
credential environment read at all — the build strips them, since it only runs
inside the Studio. The key is never written to disk, logged, or put in a cache key.

## Scope

36 commands: issues, teams, projects, users, workflow states, labels, cycles,
comments, webhooks and project milestones. 16 reads execute immediately; 20
writes are `write_requires_approval` and gated by the Airlock.

## Known limitations

- **UUIDs only.** No command accepts `ENG-123` or a team name. Start with
  `linear.list_teams` and carry the ids.
- **`search_issues` matches titles only** — not descriptions or comments.
- **Milestones are project-scoped.** `create_milestone` requires a `project_id`;
  Linear has no workspace-level milestone.
- **`create_webhook` needs a scope** — exactly one of `team_id` or
  `all_public_teams`.
- **API key auth only.** No OAuth2 in this release.
- **Caching covers metadata only** (teams, projects, users, states, labels) with
  a 5-minute TTL. Issue and comment reads are never cached.
- **Mutations are never auto-retried.** Linear has no idempotency key, so a retry
  after an accepted write would duplicate it. Recovery is a fresh approval.

## Verification

208 unit tests and 47 live tests against a real Linear workspace; all 36
commands exercised end-to-end. Full source, architecture notes and the bundle
build tool: <https://github.com/faizalmy/railcall-linear-module>

MIT licensed.
