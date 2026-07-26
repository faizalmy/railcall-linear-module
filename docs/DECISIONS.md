# Decision Log: RailCall Linear Module

**Project:** RailCall Linear Module  
**Contest:** RailCall Community Contest 2026 Q3 — Track A (Best Module)  
**Created:** 2026-07-26  
**Last Updated:** 2026-07-26

---

## Decision 001: Choose Linear over other integrations

**Date:** 2026-07-26  
**Status:** Accepted  
**Deciders:** AgentStack Labs

### Context

The RailCall marketplace has 7,240 workflow templates but only 2 actual modules (Salesforce, HubSpot). We need to pick one integration to build for Track A ($1,500 + $500 prizes). Candidates evaluated:

- Linear (project management)
- Slack (team communication)
- Notion (knowledge management)
- Twilio (SMS/voice)
- Zendesk (support tickets)
- Stripe (payments)
- Jira (project management)

### Decision

Build a **Linear module** (`agentstack/linear`).

### Rationale

| Factor | Linear | Slack | Notion | Twilio | Zendesk | Stripe | Jira |
|--------|--------|-------|--------|--------|---------|--------|------|
| Marketplace presence | 0 modules | 0 modules | 0 modules | 0 modules | 0 modules | 0 modules | 0 modules |
| Referenced in workflows | 20+ | Many | Few | Few | Few | Few | Few |
| API complexity | GraphQL (clean) | REST + OAuth | REST | REST | REST | REST | REST (verbose) |
| Auth pattern | API key (simple) | OAuth2 (complex) | API key | API key | API key | API key | Basic/OAuth |
| Target audience | Dev teams (pay for tools) | Every team | Knowledge workers | Ops/support | Support teams | Finance/dev | Enterprise |
| Airlock demo value | High (create/update issues) | High (send messages) | Medium (create pages) | Very high (all external) | High (create tickets) | High (refunds) | High |
| Build time estimate | ~2 days | ~3 days (OAuth) | ~2 days | ~2 days | ~2 days | ~2 days | ~3 days (verbose API) |
| Competition risk | Low | Low | Low | Low | Low | Medium (Umut building) | Low |
| Personal experience | Yes (Solarware) | Yes | Yes | No | No | Yes | No |

**Key factors:**
1. Linear is referenced in 20+ workflow templates but has no module — proven demand
2. GraphQL API is clean and well-documented
3. API key auth (no OAuth complexity)
4. Dev teams are the exact audience that pays for productivity automation
5. Personal experience with Linear (Solarware project)
6. Zero competition confirmed via API search

**Rejected alternatives:**
- **Stripe**: Umut S. is building it (per clarification board)
- **Slack**: OAuth2 adds complexity; API key auth not available for bots
- **Jira**: API is verbose; Linear is cleaner for same use case
- **Twilio**: Good airlock demo but smaller market than Linear

### Consequences

- **Positive**: Fast build time, clean API, proven demand, zero competition
- **Negative**: Linear doesn't support OAuth2 for third-party apps (API keys only) — limits enterprise adoption post-contest
- **Risk**: Another contestant could publish Linear module first — mitigated by publishing early (Jul 30)

---

## Decision 002: API key auth over OAuth2

**Date:** 2026-07-26  
**Status:** Accepted  
**Deciders:** AgentStack Labs

### Context

Linear supports only API key authentication for third-party integrations. OAuth2 is not available for marketplace modules.

### Decision

Use **API key auth** (`LINEAR_API_KEY` env var).

### Rationale

- Linear doesn't support OAuth2 for third-party apps
- API key is simpler to implement (no OAuth flow)
- API key is simpler for users to set up (generate key in Linear settings, set env var)
- Contest judges care about working module, not auth complexity
- Can add OAuth2 post-contest if Linear opens up the API

### Consequences

- **Positive**: Fast implementation, simple UX, no OAuth callback server needed
- **Negative**: API keys are less secure than OAuth2 (no scoping, no expiry) — acceptable for contest
- **Risk**: Enterprise users may reject API key auth — acceptable trade-off for contest win

---

## Decision 003: 8 commands (not more, not fewer)

**Date:** 2026-07-26  
**Status:** Accepted  
**Deciders:** AgentStack Labs

### Context

Contest judging criteria: "coverage (the top 6-10 actions someone would want, not just one)". We need to pick how many commands to implement.

### Decision

Implement **8 commands**: 4 read + 4 write.

| # | Command | Type | Rationale |
|---|---------|------|-----------|
| 1 | `create_issue` | Write | Core action — every team creates issues |
| 2 | `update_issue` | Write | Core action — update title, state, assignee, priority |
| 3 | `list_issues` | Read | Core action — triage, filter, search |
| 4 | `list_teams` | Read | Needed to get team_id for other commands |
| 5 | `list_projects` | Read | High-value — project-level visibility |
| 6 | `list_cycles` | Read | High-value — sprint planning |
| 7 | `add_comment` | Write | High-value — collaboration |
| 8 | `update_state` | Write | High-value — state transitions (most common mutation) |

### Rationale

- 8 commands hits the "6-10" sweet spot in judging criteria
- 4 read + 4 write = balanced coverage
- Covers the top actions a dev team needs daily
- Not so many that quality suffers (each command gets proper error handling, docs)
- Build time: ~2 days (feasible before contest deadline)

**Rejected:**
- 6 commands: Too few, misses `list_projects` and `list_cycles` (high-value)
- 10 commands: Too many, risks quality (e.g., `delete_issue`, `list_users`, `create_project` are lower priority)

### Consequences

- **Positive**: Balanced coverage, feasible build time, hits judging criteria
- **Negative**: Some edge cases not covered (e.g., file attachments, labels) — acceptable for MVP
- **Risk**: Judges may want more depth — mitigated by strong error handling + docs

---

## Decision 004: Free launch, monetize post-contest

**Date:** 2026-07-26  
**Status:** Accepted  
**Deciders:** AgentStack Labs

### Context

RailCall modules can be free or paid. Paid modules require publisher-trust allowlist approval. Contest rules: "Paid modules eligible — marketplace revenue-share is 5% one-time / 25% subscription."

### Decision

Launch as **free module** for contest. Monetize post-contest if we win.

### Rationale

- Free modules work immediately (no allowlist approval needed)
- Paid modules require staff approval (email sami@railcall.ai) — adds delay
- Free launch maximizes install count (ties broken by install count in 72h after publish)
- Can flip to paid post-contest (flip `license_required: true`, set price)
- Contest prize money ($1,500) is guaranteed; revenue is uncertain

### Consequences

- **Positive**: Fast publish, no approval delay, max install count
- **Negative**: No immediate revenue — acceptable trade-off for contest win
- **Risk**: Free users may not convert to paid — acceptable (we keep IP + 75% of future revenue)

---

## Decision 005: Publish by Jul 30 (not Aug 24)

**Date:** 2026-07-26  
**Status:** Accepted  
**Deciders:** AgentStack Labs

### Context

Contest deadline: Aug 25, 2026. We could publish anytime before then.

### Decision

Publish by **Jul 30, 2026** (4 days from now).

### Rationale

- Ties broken by "real-world install count in the 72 hours after publish" — earlier publish = more time to accumulate installs
- Pre-publish review is "same-day during contest window" but could be delayed — publish early to avoid deadline crunch
- First-mover advantage: if another contestant builds Linear module, we're already live
- Leaves 25 days for iteration based on user feedback (if any)

### Consequences

- **Positive**: Max install time, avoids deadline crunch, first-mover advantage
- **Negative**: Less time to polish — mitigated by strong MVP (8 commands, good docs)
- **Risk**: Bug discovered post-publish — mitigated by versioning (publish v0.1.0, iterate to v0.2.0)

---

## Decision 006: Use `requests` over `httpx` or `aiohttp`

**Date:** 2026-07-26  
**Status:** Accepted  
**Deciders:** AgentStack Labs

### Context

Need HTTP client for Linear GraphQL API. Options: `requests`, `httpx`, `aiohttp`.

### Decision

Use **`requests`** library.

### Rationale

- `requests` is the most widely used HTTP library in Python (familiar to most developers)
- Synchronous is fine for RailCall handlers (no async runtime needed)
- Simpler API than `httpx` or `aiohttp`
- No performance benefit from async (handlers are I/O-bound, not CPU-bound)
- Judges care about working code, not HTTP client choice

### Consequences

- **Positive**: Simple, familiar, well-documented
- **Negative**: Synchronous only — acceptable for contest
- **Risk**: None — `requests` is battle-tested

---

## Decision 007: Minimal field selection in GraphQL queries

**Date:** 2026-07-26  
**Status:** Accepted  
**Deciders:** AgentStack Labs

### Context

Linear's GraphQL API allows fetching any field. We need to decide how much data to request.

### Decision

Use **minimal field selection** — request only the fields we need.

### Rationale

- Reduces response size (faster API calls)
- Reduces token count if responses are passed to LLMs (cost savings)
- Shows good API hygiene (judges notice)
- Easier to reason about (less data to handle)

### Example

```python
# Good — minimal fields
query = """
query {
  teams {
    nodes {
      id
      name
      key
    }
  }
}
"""

# Bad — over-fetching
query = """
query {
  teams {
    nodes {
      id
      name
      key
      description
      private
      createdAt
      updatedAt
      # ... 20 more fields
    }
  }
}
"""
```

### Consequences

- **Positive**: Faster API calls, lower token costs, cleaner code
- **Negative**: May need to add fields later if use cases expand — acceptable (version the module)
- **Risk**: None — minimal selection is best practice

---

## Decision 008: Cursor-based pagination for list operations

**Date:** 2026-07-26  
**Status:** Accepted  
**Deciders:** AgentStack Labs

### Context

Linear's GraphQL API uses cursor-based pagination (first/after, last/before). We need to handle pagination for list operations.

### Decision

Implement **cursor-based pagination** with a `limit` parameter.

### Rationale

- Linear API requires cursor-based pagination (no offset-based)
- `limit` parameter gives users control over result size
- Default limit: 50 (reasonable for most use cases)
- Pagination handled internally (user doesn't need to manage cursors)

### Example

```python
def list_issues(inputs: dict, context: dict) -> dict:
    limit = inputs.get("limit", 50)
    cursor = None
    all_issues = []
    
    while len(all_issues) < limit:
        query = """
        query($after: String, $first: Int) {
          issues(after: $after, first: $first) {
            nodes { id identifier title }
            pageInfo { hasNextPage endCursor }
          }
        }
        """
        
        variables = {"first": min(50, limit - len(all_issues))}
        if cursor:
            variables["after"] = cursor
        
        data = _make_request(query, variables)
        issues = data["issues"]["nodes"]
        all_issues.extend(issues)
        
        if not data["issues"]["pageInfo"]["hasNextPage"]:
            break
        cursor = data["issues"]["pageInfo"]["endCursor"]
    
    return {"issues": all_issues[:limit]}
```

### Consequences

- **Positive**: Handles large datasets, user-friendly API
- **Negative**: More complex than single-request queries — acceptable (necessary for correctness)
- **Risk**: Rate limit hit during pagination — mitigated by retry logic

---

## Decision 009: README ≤500 words (not longer)

**Date:** 2026-07-26  
**Status:** Accepted  
**Deciders:** AgentStack Labs

### Context

Contest judging: "docs (a README that lets a stranger install and use it in under 10 minutes)". Contest brief: "500 words max — density beats length."

### Decision

Write README with **≤500 words**.

### Rationale

- Contest brief explicitly says "500 words max"
- Density beats length — judges prefer concise, actionable docs
- "Stranger test" — someone unfamiliar can install + use in <10 min
- Shorter README = faster to read = better UX

### Structure

```markdown
# agentstack/linear

Linear project management — create/update issues, list teams/projects/cycles, add comments.

## Install

railcall market install agentstack/linear

## Setup

1. Get API key: Linear → Settings → API → Create key
2. Set env var: export LINEAR_API_KEY=lin_api_xxxxx

## Usage

# List teams
railcall run agentstack/linear.list_teams

# Create issue (approval required)
railcall run agentstack/linear.create_issue --team_id=ENG --title="Fix bug" --priority=1

# List issues
railcall run agentstack/linear.list_issues --team_id=ENG

## Commands

- create_issue — Create issue (external)
- update_issue — Update issue (external)
- list_issues — List issues (read)
- list_teams — List teams (read)
- list_projects — List projects (read)
- list_cycles — List cycles (read)
- add_comment — Add comment (external)
- update_state — Update state (external)

## Limitations

- No OAuth2 (API key only)
- No file attachments
- No webhook triggers
```

### Consequences

- **Positive**: Concise, actionable, passes judging criteria
- **Negative**: May omit edge cases — acceptable (link to full docs if needed)
- **Risk**: Users may have questions — mitigated by Discord support

---

## Decision 010: Enter Track A only (not Track B)

**Date:** 2026-07-26  
**Status:** Accepted  
**Deciders:** AgentStack Labs

### Context

Contest has two tracks:
- Track A: Best Module ($1,500 + $500)
- Track B: Best Workflow ($500)

Rules: "One entry per person per track — you can enter both tracks with different submissions."

### Decision

Enter **Track A only** (Best Module).

### Rationale

- Track A has larger prize pool ($1,500 + $500 vs $500)
- Module is more valuable long-term (recurring revenue, IP ownership)
- Building both module + workflow splits focus — better to nail one
- Module is harder to build (more technical) — less competition
- Workflow can be built later using our own module (or existing ones)

### Consequences

- **Positive**: Focused effort, higher prize pool, long-term value
- **Negative**: Miss Track B opportunity — acceptable (can enter next contest)
- **Risk**: Module doesn't win — mitigated by keeping IP + monetizing independently

---

## Summary of Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 001 | Choose Linear | Zero competition, proven demand, clean API, personal experience |
| 002 | API key auth | Linear doesn't support OAuth2; simpler for contest |
| 003 | 8 commands | Hits 6-10 sweet spot; 4 read + 4 write = balanced |
| 004 | Free launch | No approval delay; max install count; monetize later |
| 005 | Publish by Jul 30 | Max install time; first-mover advantage; avoids deadline crunch |
| 006 | Use `requests` | Simple, familiar, synchronous is fine |
| 007 | Minimal field selection | Faster API calls; lower token costs; best practice |
| 008 | Cursor-based pagination | Handles large datasets; user-friendly |
| 009 | README ≤500 words | Contest brief says "density beats length" |
| 010 | Track A only | Larger prize pool; focused effort; long-term value |

---

## Open Questions

| Question | Status | Notes |
|----------|--------|-------|
| Should we add `list_users` command? | Deferred | Low priority; can add in v0.2.0 |
| Should we support file attachments? | Deferred | Out of scope for MVP |
| Should we build a workflow using this module? | Deferred | Can do post-contest |
| Should we monetize immediately after contest? | Deferred | Depends on install count + feedback |

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2026-07-26 | 1.0.0 | Initial decision log |
