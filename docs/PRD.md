# Product Requirements Document: RailCall Linear Module (Production)

**Version:** 0.2.1  
**Status:** Planning  
**Author:** AgentStack Labs  
**Date:** 2026-07-26  
**Contest:** RailCall Community Contest 2026 Q3 — Track A (Best Module)

---

## 1. Overview

### 1.1 What We're Building

A production-grade RailCall module (`agentstack-labs/linear`) providing comprehensive governed access to Linear's project management API. The module implements 36 commands across 10 functional categories, supports OAuth2 authentication, includes caching and webhook handlers, and ships with comprehensive test coverage and CI/CD automation.

### 1.2 Problem Statement

Linear is referenced in 20+ RailCall workflow templates but no standalone module exists. The MVP (8 commands) demonstrates feasibility but lacks production requirements: OAuth2 for enterprise adoption, comprehensive command coverage for real workflows, test coverage for reliability, and monitoring for operational visibility.

### 1.3 Target Users

| Persona | Role | Pain Point |
|---------|------|------------|
| Engineering Manager | Team lead | Needs audit trail on issue state changes for compliance |
| Product Manager | Feature owner | Wants governed automation for issue triage and routing |
| DevOps Engineer | Incident responder | Needs approval gates before updating incident issues |
| Startup CTO | Technical founder | Wants AI-driven Linear automation with human oversight |
| Enterprise Admin | IT operations | Requires OAuth2, SSO, and audit log exports |

### 1.4 Success Criteria

| Criterion | Metric | Target |
|-----------|--------|--------|
| Command coverage | Full API surface | 36 commands across 10 categories |
| Authentication | OAuth2 + API key | Both supported |
| Test coverage | Unit + integration | >80% code coverage |
| Performance | Cached reads | <200ms for cached operations |
| Reliability | Error handling | 100% of errors return actionable messages |
| Documentation | API reference + guides | Complete coverage |
| CI/CD | Automated testing | All tests pass on every commit |
| Contest submission | Published + tagged | Before Aug 25, 2026 |
| Judging score | All criteria | >90/100 |

---

## 2. Requirements

### 2.1 Functional Requirements

#### FR-1: Command Categories (36 commands)

**Priority:** P0 (must have)

| Category | Commands | Count |
|----------|----------|-------|
| Issue Management | create_issue, update_issue, delete_issue, list_issues, search_issues, bulk_update_issues, link_issues, add_attachment, add_reaction, get_issue_history | 10 |
| Project Management | create_project, update_project, list_projects, create_milestone, update_milestone, list_milestones | 6 |
| Team Management | create_team, update_team, list_teams, list_team_members, add_team_member, remove_team_member | 6 |
| Workflow & Automation | create_label, update_label, list_labels, create_state, update_state, list_states | 6 |
| Cycle Management | create_cycle, update_cycle, list_cycles, add_issues_to_cycle, remove_issues_from_cycle | 5 |
| Webhooks | create_webhook, list_webhooks, delete_webhook | 3 |
| Advanced | export_audit_log, create_view, list_views | 3 |

**Acceptance criteria:**
- Each command has `name`, `description`, `input_schema`, `side_effects`
- Write commands set `side_effects: "external"`
- Read commands set `side_effects: "none"`
- All commands validated against Linear GraphQL API

#### FR-2: OAuth2 Authentication

**Priority:** P0 (must have)

Module supports both API key and OAuth2 authentication.

**Acceptance criteria:**
- OAuth2 flow: authorize → callback → token exchange → refresh
- Tokens stored securely (encrypted at rest)
- Refresh tokens handled automatically
- API key auth remains available for simple use cases
- Auth pattern declared in `module.json`

#### FR-3: Caching Layer

**Priority:** P1 (should have)

Redis-based caching for read operations.

**Acceptance criteria:**
- Cache TTL: 5 minutes for read operations
- Cache invalidation on write operations
- Configurable cache backend (Redis, in-memory)
- Cache hit/miss metrics exposed

#### FR-4: Webhook Handlers

**Priority:** P1 (should have)

Event-driven automation via webhooks.

**Acceptance criteria:**
- Support for Linear webhook events (issue.created, issue.updated, etc.)
- Webhook signature verification
- Event routing to RailCall workflows
- Retry logic for failed deliveries

#### FR-5: Bulk Operations

**Priority:** P1 (should have)

Transaction support for multi-issue operations.

**Acceptance criteria:**
- `bulk_update_issues` updates up to 100 issues atomically
- Partial failures return detailed error report
- Rollback on critical errors

### 2.2 Non-Functional Requirements

#### NFR-1: Security

**Priority:** P0 (must have)

**Acceptance criteria:**
- OAuth2 tokens encrypted at rest (AES-256)
- API keys never logged, never in receipts
- Webhook signatures verified before processing
- All GraphQL queries use parameterized variables
- Input validation on all commands
- Rate limiting with exponential backoff + jitter

#### NFR-2: Testing

**Priority:** P0 (must have)

**Acceptance criteria:**
- Unit tests for all 36 commands (>80% coverage)
- Integration tests against Linear sandbox
- Mock API responses for offline testing
- Test fixtures for common scenarios
- CI runs tests on every commit

#### NFR-3: Performance

**Priority:** P1 (should have)

**Acceptance criteria:**
- Cached reads: <200ms
- Uncached reads: <2s
- Write operations: <5s
- Bulk operations: <30s for 100 issues
- Rate limit handling: no 429 errors in normal operation

#### NFR-4: Documentation

**Priority:** P0 (must have)

**Acceptance criteria:**
- API reference for all 36 commands
- Installation guide (OAuth2 + API key)
- Usage examples for common workflows
- Troubleshooting guide
- Migration guide from v1.0 to v2.0
- Architecture decision records

#### NFR-5: CI/CD

**Priority:** P1 (should have)

**Acceptance criteria:**
- GitHub Actions workflow
- Tests run on push + PR
- Linting (black, flake8, mypy)
- Automated publishing on release
- Version bumping (semver)

#### NFR-6: Monitoring

**Priority:** P2 (nice to have)

**Acceptance criteria:**
- Structured logging (JSON format)
- Metrics: command count, error rate, cache hit rate
- Health check endpoint
- Alerting on critical errors

---

## 3. User Stories

### US-1: Enterprise OAuth2 Setup

**As an** enterprise admin  
**I want** to authenticate via OAuth2 with SSO  
**So that** my team can use the module without managing API keys

**Acceptance criteria:**
- Run `railcall connect linear` → opens browser for OAuth2 flow
- User authenticates via Linear SSO
- Token stored encrypted in RailCall vault
- Module uses token for all subsequent operations
- Token refreshes automatically before expiry

### US-2: Bulk Issue Triage

**As a** product manager  
**I want** to update 50 issues in one operation  
**So that** I can triage a backlog efficiently

**Acceptance criteria:**
- Invoke `linear.bulk_update_issues` with `{issue_ids, state_id}` and approve the airlock preview
- Airlock shows preview of all 50 changes
- Approve → all issues updated atomically
- Receipt includes list of updated issue IDs
- Partial failures reported with details

### US-3: Webhook-Driven Automation

**As a** DevOps engineer  
**I want** to trigger workflows when issues are created  
**So that** I can automate incident response

**Acceptance criteria:**
- Invoke `linear.create_webhook` with `{url, resource_types, all_public_teams}`
- Webhook registered with Linear
- Issue created in Linear → webhook fires → RailCall workflow executes
- Signed receipt for webhook delivery
- Retry on failure (3 attempts, exponential backoff)

---

## 4. Technical Constraints

### 4.1 RailCall Constraints

- Python 3.9+
- Module structure: `module.json` + `handlers/handler.py`
- Ed25519-signed publisher key (local, never leaves machine)
- Publish rate limit: 5/hour per account
- Manual review before listing goes live

### 4.2 Linear API Constraints

- GraphQL API at `https://api.linear.app/graphql`
- Rate limit: 50 requests per 10 seconds (per API key)
- Pagination: cursor-based (first/after, last/before)
- OAuth2: supported for third-party apps (requires Linear approval)
- Webhooks: supported for issue, project, team events

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
| Jul 26 | Production PRD + architecture finalized |
| Jul 27-28 | Implement OAuth2 flow + caching layer |
| Jul 29-Aug 2 | Implement remaining 22 commands |
| Aug 3-5 | Write unit + integration tests |
| Aug 6-7 | Set up CI/CD pipeline |
| Aug 8-10 | Write comprehensive documentation |
| Aug 11-12 | Performance testing + optimization |
| Aug 13 | Publish v0.2.1 to marketplace |
| Aug 14-25 | Iterate based on feedback |
| Aug 25 | Contest submissions close |
| Aug 29 | Winners announced |

---

## 6. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| OAuth2 approval delayed by Linear | Medium | High | Ship with API key auth first, add OAuth2 post-approval |
| Linear API rate limit hit during bulk ops | High | Medium | Implement intelligent batching + rate limit awareness |
| Redis dependency adds complexity | Medium | Low | Support in-memory cache fallback |
| Test coverage gaps | Low | High | Require >80% coverage in CI |
| 30 commands too ambitious for timeline | Medium | Medium | Prioritize top 20 commands, defer remaining to v2.1 |

---

## 7. Appendix

### 7.1 Command Reference (Full List)

**Issue Management:**
1. `create_issue` — Create new issue
2. `update_issue` — Update issue fields
3. `delete_issue` — Soft delete issue
4. `list_issues` — List issues with filters
5. `search_issues` — Full-text search
6. `bulk_update_issues` — Update multiple issues
7. `link_issues` — Create dependencies
8. `add_attachment` — Upload file to issue
9. `add_reaction` — Emoji reaction on comment
10. `get_issue_history` — Audit trail

**Project Management:**
11. `create_project` — New project
12. `update_project` — Modify project
13. `list_projects` — List all projects
14. `create_milestone` — Add milestone
15. `update_milestone` — Modify milestone
16. `list_milestones` — View milestones

**Team Management:**
17. `create_team` — New team
18. `update_team` — Modify team
19. `list_teams` — List all teams
20. `list_team_members` — View roster
21. `add_team_member` — Invite user
22. `remove_team_member` — Remove user

**Workflow & Automation:**
23. `create_label` — Custom label
24. `update_label` — Modify label
25. `list_labels` — View labels
26. `create_state` — Custom state
27. `update_state` — Modify state
28. `list_states` — View states

**Cycle Management:**
29. `create_cycle` — New sprint
30. `update_cycle` — Modify cycle
31. `list_cycles` — View cycles
32. `add_issues_to_cycle` — Bulk assign
33. `remove_issues_from_cycle` — Remove from cycle

**Webhooks:**
34. `create_webhook` — Event subscription
35. `list_webhooks` — View webhooks
36. `delete_webhook` — Remove webhook

**Advanced:**
37. `export_audit_log` — Compliance export
38. `create_view` — Saved filter
39. `list_views` — View saved filters

### 7.2 Linear API Documentation

- GraphQL schema: https://studio.apollographql.com/public/Linear-API/variant/current/home
- API key setup: https://linear.app/docs/api-keys
- OAuth2 setup: https://developers.linear.app/docs/oauth/authentication
- Rate limits: https://developers.linear.app/docs/graphql/working-with-the-graphql-api/rate-limiting
- Webhooks: https://developers.linear.app/docs/webhooks

### 7.3 RailCall Documentation

- Module developer guide: https://railcall.ai/docs/marketplace-developer/your-first-module
- Auth patterns: https://railcall.ai/docs/marketplace-developer/modules/#auth-patterns
- Contest brief: https://railcall.ai/contest
