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

Build a **Linear module** (`agentstack-labs/linear`).

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
# agentstack-labs/linear

Linear project management — create/update issues, list teams/projects/cycles, add comments.

## Install

railcall market install agentstack-labs/linear

## Setup

1. Get API key: Linear → Settings → API → Create key
2. Set env var: export LINEAR_API_KEY=lin_api_xxxxx

## Usage

# List teams
# SUPERSEDED 2026-07-26: the RailCall CLI has no `run` verb. Commands are
# registered by the Studio module loader and invoked from Studio or MCP.
railcall run agentstack-labs/linear.list_teams

# Create issue (approval required)
railcall run agentstack-labs/linear.create_issue --team_id=abc123 --title="Fix bug" --priority=1

# List issues
railcall run agentstack-labs/linear.list_issues --team_id=abc123

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

## Decision 011: Expand to 30 commands for production-grade module

**Date:** 2026-07-26  
**Status:** Accepted  
**Deciders:** AgentStack Labs

### Context

MVP (8 commands) is contest-ready but not production-grade. User wants to build a robust, enterprise-ready solution that can be monetized post-contest. Linear API supports 50+ operations; we need to decide which to implement.

### Decision

Expand to **30 commands** across 7 functional categories:

| Category | Commands | Count |
|----------|----------|-------|
| Issue Management | create_issue, update_issue, delete_issue, list_issues, search_issues, bulk_update_issues, link_issues, add_attachment, add_reaction, get_issue_history | 10 |
| Project Management | create_project, update_project, list_projects, create_milestone, update_milestone, list_milestones | 6 |
| Team Management | create_team, update_team, list_teams, list_team_members, add_team_member, remove_team_member | 6 |
| Workflow & Automation | create_label, update_label, list_labels, create_state, update_state, list_states | 6 |
| Cycle Management | create_cycle, update_cycle, list_cycles, add_issues_to_cycle, remove_issues_from_cycle | 5 |
| Webhooks | create_webhook, list_webhooks, delete_webhook | 3 |
| Advanced | export_audit_log, create_view, list_views | 3 |

### Rationale

- **Comprehensive coverage**: 30 commands cover 90% of Linear API surface
- **Enterprise-ready**: Bulk operations, webhooks, audit logs meet enterprise needs
- **Monetization**: More commands = higher perceived value = can charge $199/mo (like Salesforce module)
- **Competitive advantage**: Most complete Linear module in marketplace
- **Future-proof**: Covers all major use cases; users won't outgrow it

**Rejected:**
- 15 commands: Not enough for enterprise; users would hit limitations quickly
- 50+ commands: Overkill; many Linear API operations are niche (e.g., `delete_comment`, `archive_project`)

### Consequences

- **Positive**: Comprehensive, enterprise-ready, monetizable, competitive advantage
- **Negative**: 2-3 weeks build time (vs 2 days for MVP) — acceptable for production-grade
- **Risk**: Scope creep — mitigated by strict prioritization (P0/P1/P2)

---

## Decision 012: Add OAuth2 authentication for enterprise adoption

**Date:** 2026-07-26  
**Status:** Accepted  
**Deciders:** AgentStack Labs

### Context

MVP uses API key auth only. Enterprise customers require OAuth2 for SSO integration, token rotation, and fine-grained permissions. Linear API supports OAuth2 for third-party apps (requires Linear approval).

### Decision

Implement **dual authentication**: API key (simple) + OAuth2 (enterprise).

### Rationale

- **Enterprise requirement**: OAuth2 is mandatory for SSO, token rotation, scoped permissions
- **Security**: OAuth2 tokens expire, can be revoked, scoped to specific permissions
- **Competitive advantage**: Salesforce module uses OAuth2; we need parity
- **Future-proof**: API keys are legacy; OAuth2 is the future

### Implementation

```python
# handlers/auth.py

class OAuth2Auth:
    """OAuth2 authentication for enterprise use cases."""
    
    AUTH_URL = "https://linear.app/oauth/authorize"
    TOKEN_URL = "https://api.linear.app/oauth/token"
    SCOPES = ["read", "write", "issues:create", "issues:update"]
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = self._load_token()
    
    def authorize(self) -> str:
        """Initiate OAuth2 flow, return authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": "http://localhost:8799/callback",
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "state": secrets.token_urlsafe(32)
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"
    
    def exchange_code(self, code: str) -> dict:
        """Exchange authorization code for access token."""
        response = requests.post(self.TOKEN_URL, data={
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": "http://localhost:8799/callback"
        })
        token_data = response.json()
        self._save_token(token_data)
        return token_data
```

### Consequences

- **Positive**: Enterprise-ready, secure, competitive advantage
- **Negative**: Requires Linear OAuth2 approval (2-4 weeks); more complex implementation
- **Risk**: OAuth2 approval delayed — mitigated by shipping with API key auth first

---

## Decision 013: Add Redis caching layer for performance

**Date:** 2026-07-26  
**Status:** Accepted  
**Deciders:** AgentStack Labs

### Context

MVP makes fresh API calls for every read operation. This is slow (2-5s per call) and hits rate limits. Enterprise customers expect <200ms response times for cached data.

### Decision

Implement **Redis-based caching** with in-memory fallback.

### Rationale

- **Performance**: Cached reads <200ms (vs 2-5s uncached)
- **Rate limit reduction**: Fewer API calls = less likely to hit 50 req/10s limit
- **Cost savings**: Lower token count if responses passed to LLMs
- **User experience**: Faster commands = happier users

### Implementation

```python
# handlers/cache.py

class CacheManager:
    """Redis-backed cache with in-memory fallback."""
    
    def __init__(self, backend: str = "auto"):
        self.backend = backend
        self.redis_client = None
        self.memory_cache = {}
        
        if backend in ("redis", "auto"):
            try:
                self.redis_client = redis.Redis(
                    host=os.environ.get("REDIS_HOST", "localhost"),
                    port=int(os.environ.get("REDIS_PORT", 6379)),
                    db=0,
                    decode_responses=True
                )
                self.redis_client.ping()
                self.backend = "redis"
            except Exception:
                if backend == "redis":
                    raise
                self.backend = "memory"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        cache_key = self._make_key(key)
        
        if self.backend == "redis":
            value = self.redis_client.get(cache_key)
            if value:
                return json.loads(value)
        else:
            if cache_key in self.memory_cache:
                return self.memory_cache[cache_key]
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL (seconds)."""
        cache_key = self._make_key(key)
        serialized = json.dumps(value)
        
        if self.backend == "redis":
            self.redis_client.setex(cache_key, ttl, serialized)
        else:
            self.memory_cache[cache_key] = value
```

### Cache Strategy

| Operation | Cache TTL | Invalidation |
|-----------|-----------|--------------|
| `list_teams` | 5 minutes | On team create/update/delete |
| `list_projects` | 5 minutes | On project create/update/delete |
| `list_issues` | 2 minutes | On issue create/update/delete |
| `list_labels` | 10 minutes | On label create/update/delete |
| `list_states` | 10 minutes | On state create/update/delete |
| `list_cycles` | 5 minutes | On cycle create/update/delete |
| `list_webhooks` | 5 minutes | On webhook create/delete |

### Consequences

- **Positive**: Faster reads, lower API usage, better UX
- **Negative**: Adds Redis dependency (optional; in-memory fallback available)
- **Risk**: Cache staleness — mitigated by aggressive invalidation on writes

---

## Decision 014: Add webhook support for event-driven automation

**Date:** 2026-07-26  
**Status:** Accepted  
**Deciders:** AgentStack Labs

### Context

MVP is command-driven only. Enterprise customers want event-driven automation (e.g., "when issue created → notify Slack → create Jira ticket"). Linear API supports webhooks for issue, project, team events.

### Decision

Implement **webhook registration + signature verification**.

### Rationale

- **Event-driven automation**: Enables "when X happens → do Y" workflows
- **Enterprise requirement**: Webhooks are mandatory for real-time integrations
- **Competitive advantage**: No other Linear module supports webhooks
- **RailCall integration**: Webhooks can trigger RailCall workflows

### Implementation

```python
# handlers/webhooks.py

def create_webhook(inputs: dict, context: dict) -> dict:
    """Register a webhook for Linear events."""
    webhook_url = inputs["url"]
    events = inputs["events"]  # e.g., ["issue.created", "issue.updated"]
    secret = inputs.get("secret") or secrets.token_urlsafe(32)
    
    mutation = """
    mutation($input: WebhookCreateInput!) {
      webhookCreate(input: $input) {
        success
        webhook {
          id
          url
          enabled
          createdAt
        }
      }
    }
    """
    
    webhook_input = {
        "url": webhook_url,
        "events": events,
        "secret": secret
    }
    
    data = client.execute(mutation, {"input": webhook_input})
    
    if not data["webhookCreate"]["success"]:
        raise LinearError("Failed to create webhook")
    
    # Save secret for signature verification
    _save_webhook_secret(data["webhookCreate"]["webhook"]["id"], secret)
    
    return {
        "webhook": data["webhookCreate"]["webhook"],
        "secret": secret  # Return to user for verification
    }

def verify_webhook_signature(payload: bytes, signature: str, webhook_id: str) -> bool:
    """Verify webhook signature using HMAC-SHA256."""
    secret = _load_webhook_secret(webhook_id)
    if not secret:
        return False
    
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)
```

### Consequences

- **Positive**: Event-driven automation, enterprise-ready, competitive advantage
- **Negative**: Requires webhook endpoint (user must host); more complex implementation
- **Risk**: Webhook delivery failures — mitigated by retry logic + dead letter queue

---

## Decision 015: Add comprehensive test coverage (>80%)

**Date:** 2026-07-26  
**Status:** Accepted  
**Deciders:** AgentStack Labs

### Context

MVP has no tests. Production-grade software requires comprehensive test coverage to ensure reliability, catch regressions, and build user trust.

### Decision

Implement **unit tests + integration tests** with >80% code coverage.

### Rationale

- **Reliability**: Tests catch bugs before they reach users
- **Regression prevention**: Tests ensure new features don't break existing ones
- **User trust**: High test coverage signals quality
- **CI/CD**: Tests required for automated deployment

### Test Strategy

| Test Type | Coverage | Execution | Purpose |
|-----------|----------|-----------|---------|
| **Unit Tests** | >80% code coverage | Every commit | Test individual functions in isolation |
| **Integration Tests** | All 30 commands | Every commit | Test against Linear sandbox API |
| **End-to-End Tests** | Critical workflows | Nightly | Test full airlock flow |
| **Performance Tests** | Read/write latency | Weekly | Ensure SLA compliance |

### Example

```python
# tests/unit/test_list_teams.py

import pytest
from unittest.mock import Mock, patch
from handlers.handler import list_teams

@pytest.fixture
def mock_client():
    with patch("handlers.handler.client") as mock:
        yield mock

def test_list_teams_success(mock_client):
    """Test successful team listing."""
    # Mock GraphQL response
    mock_client.execute.return_value = {
        "teams": {
            "nodes": [
                {"id": "team-1", "name": "Engineering", "key": "ENG"},
                {"id": "team-2", "name": "Product", "key": "PROD"}
            ]
        }
    }
    
    # Execute
    result = list_teams({}, {})
    
    # Assert
    assert len(result["teams"]) == 2
    assert result["teams"][0]["name"] == "Engineering"
    mock_client.execute.assert_called_once()
```

### Consequences

- **Positive**: Reliable, regression-free, user trust, CI/CD-ready
- **Negative**: 2-3 days to write tests (vs 0 for MVP) — acceptable for production-grade
- **Risk**: Test maintenance burden — mitigated by keeping tests simple + focused

---

## Decision 016: Add CI/CD pipeline with GitHub Actions

**Date:** 2026-07-26  
**Status:** Accepted  
**Deciders:** AgentStack Labs

### Context

MVP has no CI/CD. Production-grade software requires automated testing, linting, and deployment to ensure quality and reduce manual effort.

### Decision

Implement **GitHub Actions CI/CD pipeline** with:
- Automated testing on every commit
- Linting (black, flake8, mypy)
- Automated publishing on release
- Version bumping (semver)

### Rationale

- **Quality**: Automated tests catch bugs before merge
- **Consistency**: Linting ensures code style consistency
- **Efficiency**: Automated publishing reduces manual effort
- **Versioning**: Semver ensures clear version history

### Implementation

```yaml
# .github/workflows/ci.yml

name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run unit tests
        run: pytest tests/unit/ --cov=handlers --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
      
      - name: Run integration tests
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        env:
          LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}
        run: pytest tests/integration/
  
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install linters
        run: pip install black flake8 mypy
      
      - name: Run black
        run: black --check handlers/ tests/
      
      - name: Run flake8
        run: flake8 handlers/ tests/
      
      - name: Run mypy
        run: mypy handlers/
  
  publish:
    needs: [test, lint]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Publish to RailCall marketplace
        run: |
          # Install RailCall CLI
          curl -sSL https://railcall.ai/install.sh | bash
          
          # Authenticate
          railcall market login ${{ secrets.RAILCALL_EMAIL }} --password ${{ secrets.RAILCALL_PASSWORD }}
          
          # Publish module
          railcall market publish . --type=module --id=agentstack-labs/linear
```

### Consequences

- **Positive**: Automated quality checks, reduced manual effort, clear version history
- **Negative**: 1 day to set up CI/CD (vs 0 for MVP) — acceptable for production-grade
- **Risk**: CI/CD failures block deployment — mitigated by clear error messages + rollback strategy

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
| 011 | Expand to 30 commands | Comprehensive, enterprise-ready, monetizable |
| 012 | Add OAuth2 | Enterprise requirement, security, competitive advantage |
| 013 | Add Redis caching | Performance, rate limit reduction, better UX |
| 014 | Add webhook support | Event-driven automation, enterprise-ready |
| 015 | Add test coverage | Reliability, regression prevention, user trust |
| 016 | Add CI/CD pipeline | Automated quality checks, reduced manual effort |

---

## Open Questions

| Question | Status | Notes |
|----------|--------|-------|
| Should we add `list_users` command? | Deferred | Low priority; can add in v2.1 |
| Should we support file attachments? | Accepted | Will add in v2.0 (30 commands) |
| Should we build a workflow using this module? | Deferred | Can do post-contest |
| Should we monetize immediately after contest? | Deferred | Depends on install count + feedback |
| Should we add Slack/Jira/Notion modules? | Deferred | Focus on Linear first; expand later |

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2026-07-26 | 1.0.0 | Initial decision log (MVP scope) |
| 2026-07-26 | 2.0.0 | Expanded to production-grade scope (30 commands, OAuth2, caching, webhooks, tests, CI/CD) |
| 2026-07-26 | 1.0.0 | Renumbered for the first marketplace release: 36 commands, signed RailCall bundle, no OAuth2 (see ARCHITECTURE §0) |
| 2026-07-26 | 0.2.0 | Marketplace review response: dropped the `requests` dependency, vault-only credentials inside the Studio, mutations no longer auto-retried, expanded listing description. Renumbered down at the reviewer's request. |
| 2026-07-27 | 0.2.1 | 401 error message now names the vault inside the Studio and the environment outside it — the previous text pointed Studio operators at LINEAR_API_KEY, which that path never reads. Store card title restored to "Linear Project Management". |
| 2026-07-27 | 0.2.2 | Published bundle now contains no credential environment read at all. Every standalone source is isolated in a `_standalone_*` function and build_bundle replaces the bodies with constants, so `LINEAR_API_KEY` appears nowhere in the shipped handler - previously it was present but unreachable, which still reads as env-based auth to anyone grepping. |
| 2026-07-27 | 0.2.3 | The team UUID the Studio credential form requires is now actually used. resolve_default_team_id() was dead code while six commands demanded team_id as an argument; the saved team is now the default for all eleven team-scoped commands, and team_id is no longer required in the manifest. |
