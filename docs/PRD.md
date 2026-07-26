# Product Requirements Document: RailCall Linear Module

**Version:** 1.0.0  
**Status:** Draft  
**Author:** AgentStack Labs  
**Date:** 2026-07-26  
**Contest:** RailCall Community Contest 2026 Q3 — Track A (Best Module)

---

## 1. Overview

### 1.1 What We're Building

A signed RailCall module (`agentstack/linear`) that provides governed access to Linear's project management API. Every command runs through the RailCall airlock — preview → approve → execute → signed receipt — so teams can automate Linear workflows with full audit trails and human-in-the-loop control.

### 1.2 Problem Statement

Linear is referenced in 20+ RailCall workflow templates (Bug Triage, Incident Response, Employee Onboarding, etc.) but **no standalone Linear module exists** in the marketplace. Users cannot execute governed Linear actions through the airlock. They must either bypass RailCall's governance or forgo Linear integration entirely.

### 1.3 Why This Matters

- **Governance gap**: 20+ workflow templates reference Linear as a dependency but have no module to execute against
- **Market demand**: Linear is the project management tool for dev teams — the exact audience that pays for productivity automation
- **Contest opportunity**: Track A (Best Module) has $1,500 + $500 prizes; Linear is explicitly mentioned as a desirable integration in the contest brief
- **Revenue potential**: Paid module with subscription pricing (RailCall takes 25% platform fee, creator keeps 75%)
- **Zero competition**: API search confirms 0 Linear modules in marketplace

### 1.4 Target Users

| Persona | Role | Pain Point |
|---------|------|------------|
| Engineering Manager | Team lead | Needs audit trail on issue state changes for compliance |
| Product Manager | Feature owner | Wants governed automation for issue triage and routing |
| DevOps Engineer | Incident responder | Needs approval gates before updating incident issues |
| Startup CTO | Technical founder | Wants AI-driven Linear automation with human oversight |

### 1.5 Success Criteria

| Criterion | Metric | Target |
|-----------|--------|--------|
| Installability | Fresh install + run in clean workspace | <5 minutes |
| Command coverage | Core actions a real team needs | 8 commands |
| Airlock integration | Write operations gated by preview→approve→execute | 100% of mutations |
| Documentation quality | README passes "stranger test" | <10 min to first successful run |
| Contest submission | Published + tagged before deadline | Before Aug 25, 2026 |
| Judging score | Does it work + real problem + code quality + docs | >80/100 |

### 1.6 Out of Scope

- OAuth2 flow (use API key for simplicity; OAuth can be added post-contest)
- Workflow templates (this is a module, not a workflow — Track A only)
- Paid tier at launch (publish free for contest; monetize after)
- Webhook triggers (module is command-driven, not event-driven)
- File attachments (Linear API supports them but out of scope for MVP)

---

## 2. Requirements

### 2.1 Functional Requirements

#### FR-1: Module Manifest

**Priority:** P0 (must have)

`module.json` declares 8 commands with input schemas, auth pattern, side_effects flags.

**Acceptance criteria:**
- Manifest validates against RailCall schema
- Each command has `name`, `description`, `input_schema`, `side_effects`
- Auth pattern: `api_key` with env var `LINEAR_API_KEY`
- Write commands set `side_effects: "external"`
- Read commands set `side_effects: "none"`

#### FR-2: Command Implementation

**Priority:** P0 (must have)

`handlers/handler.py` implements 8 functions matching manifest.

**Commands:**

| # | Command | Type | Description |
|---|---------|------|-------------|
| 1 | `create_issue` | Write | Create new issue in a team |
| 2 | `update_issue` | Write | Update issue title, state, assignee, priority |
| 3 | `list_issues` | Read | List issues with optional filters (team, state, assignee) |
| 4 | `list_teams` | Read | List all teams in workspace |
| 5 | `list_projects` | Read | List all projects in workspace |
| 6 | `list_cycles` | Read | List active cycles for a team |
| 7 | `add_comment` | Write | Add comment to an issue |
| 8 | `update_state` | Write | Transition issue to new state |

**Acceptance criteria:**
- Each function signature: `def command(inputs: dict, context: dict) -> dict`
- Input validation matches `input_schema`
- Errors raised with clear messages (no swallowed exceptions)
- No secrets logged
- GraphQL queries use minimal field selection (no over-fetching)

#### FR-3: Linear API Integration

**Priority:** P0 (must have)

Handler calls Linear GraphQL API using `requests` or `httpx`.

**Acceptance criteria:**
- API key read from env var `LINEAR_API_KEY`
- Endpoint: `https://api.linear.app/graphql`
- Handles rate limits (429 responses) with retry logic
- Handles pagination for list operations (cursor-based)
- Returns structured responses (dict)
- Error responses include Linear error codes + actionable messages

#### FR-4: Airlock Integration

**Priority:** P0 (must have)

Write commands trigger preview → approve → execute flow.

**Acceptance criteria:**
- `create_issue` shows preview of title, description, team, assignee before approval
- `update_issue` shows diff of changed fields before approval
- `add_comment` shows comment content + target issue before approval
- `update_state` shows current state → new state transition before approval
- All external commands emit signed receipts
- Receipt payload includes command name, inputs, outputs, timestamp

### 2.2 Non-Functional Requirements

#### NFR-1: Security

**Priority:** P0 (must have)

Secrets never logged, never touch DB, never exposed in receipts.

**Acceptance criteria:**
- API key read from env var only
- No `print(api_key)` or `logging.info(api_key)` anywhere
- Receipt payload excludes auth headers
- No secrets in error messages

#### NFR-2: Documentation

**Priority:** P0 (must have)

README explains what, who, install, example, credentials, limitations.

**Acceptance criteria:**
- ≤500 words
- Includes working example with expected output
- Explains how to get API key from Linear + set env var
- Lists known limitations (e.g., no OAuth, no file attachments)
- Passes "stranger test" — someone unfamiliar can install + use in <10 min

#### NFR-3: Testability

**Priority:** P1 (should have)

Module can be tested locally before publishing.

**Acceptance criteria:**
- `railcall module install --from-path` succeeds
- `railcall run agentstack/linear.list_teams` works
- Fresh install test passes (install as buyer would from marketplace)

#### NFR-4: Code Quality

**Priority:** P1 (should have)

Clean, readable, well-commented code.

**Acceptance criteria:**
- Functions ≤30 lines
- Comments where they matter (not obvious ones)
- Error messages are actionable ("Team not found" not "Error 404")
- No dead code or unused imports

---

## 3. User Stories

### US-1: Create Issue with Approval

**As an** engineering manager  
**I want** to create a Linear issue through the airlock  
**So that** I can review the issue details before it's created and have an audit trail

**Acceptance criteria:**
- Run `railcall run agentstack/linear.create_issue --team=ENG --title="Fix login bug" --priority=high`
- Airlock shows preview: team, title, priority, description
- Approve → issue created → signed receipt emitted
- Receipt includes issue ID, URL, timestamp

### US-2: List Issues for Triage

**As a** product manager  
**I want** to list all unassigned issues in my team  
**So that** I can triage and assign them

**Acceptance criteria:**
- Run `railcall run agentstack/linear.list_issues --team=ENG --assignee=none`
- Returns list of issues with ID, title, state, priority
- No approval needed (read operation)
- Signed receipt emitted (audit trail)

### US-3: Update Issue State

**As a** DevOps engineer  
**I want** to transition an issue from "In Progress" to "Done"  
**So that** I can close out completed work with an audit trail

**Acceptance criteria:**
- Run `railcall run agentstack/linear.update_state --issue=ENG-123 --state=done`
- Airlock shows preview: current state → new state
- Approve → state updated → signed receipt emitted
- Receipt includes issue ID, old state, new state, timestamp

---

## 4. Technical Constraints

### 4.1 RailCall Constraints

- Python 3.9+
- Module structure: `module.json` + `handlers/handler.py`
- Ed25519-signed publisher key (local, never leaves machine)
- Publish rate limit: 5/hour per account
- Manual review before listing goes live (same-day during contest)

### 4.2 Linear API Constraints

- GraphQL API at `https://api.linear.app/graphql`
- Rate limit: 50 requests per 10 seconds (per API key)
- Pagination: cursor-based (first/after, last/before)
- Auth: API key (personal or team-scoped)
- No OAuth2 for third-party apps (Linear uses API keys only)

### 4.3 Contest Constraints

- Must publish before Aug 25, 2026
- Must tag description with `contest:2026Q3`
- Must be original work (no forked OSS)
- Must use real APIs (no mocks/stubs)
- Must pass pre-publish review queue

---

## 5. Timeline

| Date | Milestone |
|------|-----------|
| Jul 26 | PRD + architecture finalized |
| Jul 27-28 | Implement 8 commands + test locally |
| Jul 29 | Write README + test fresh install |
| Jul 30 | Publish to marketplace + submit contest entry |
| Aug 25 | Contest submissions close |
| Aug 29 | Winners announced |

---

## 6. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Linear API rate limit hit during testing | Medium | Low | Implement retry logic with exponential backoff |
| Pre-publish review rejects module | Low | High | Follow reference modules (sami666/hubspot) exactly |
| Another contestant publishes Linear module first | Low | High | Publish early (Jul 30) to establish first-mover |
| GraphQL query complexity exceeds limits | Low | Medium | Use minimal field selection, test queries in Linear's GraphQL playground first |

---

## 7. Appendix

### 7.1 Reference Modules

- `sami666/hubspot` — Free, 2 commands, Bearer token auth
- `sami666/salesforce` — $199/mo, 20 commands, OAuth2

### 7.2 Linear API Documentation

- GraphQL schema: https://studio.apollographql.com/public/Linear-API/variant/current/home
- API key setup: https://linear.app/docs/api-keys
- Rate limits: https://developers.linear.app/docs/graphql/working-with-the-graphql-api/rate-limiting

### 7.3 RailCall Documentation

- Module developer guide: https://railcall.ai/docs/marketplace-developer/your-first-module
- Auth patterns: https://railcall.ai/docs/marketplace-developer/modules/#auth-patterns
- Contest brief: https://railcall.ai/contest
