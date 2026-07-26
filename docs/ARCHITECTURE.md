# Architecture Document: RailCall Linear Module

**Version:** 1.0.0  
**Status:** Draft  
**Author:** AgentStack Labs  
**Date:** 2026-07-26  
**Contest:** RailCall Community Contest 2026 Q3 — Track A (Best Module)

---

## 1. System Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     RailCall Runtime                         │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Airlock    │───▶│   Validator  │───▶│   Executor   │  │
│  │  (preview →  │    │(input_schema)│    │(handler.py)  │  │
│  │   approve →  │    └──────────────┘    └──────┬───────┘  │
│  │   execute)   │                                │          │
│  └──────────────┘                                │          │
│                                                  │          │
│  ┌──────────────┐                                │          │
│  │   Receipt    │◀───────────────────────────────┘          │
│  │   (signed)   │                                           │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ HTTPS
                          ▼
              ┌───────────────────────┐
              │  Linear GraphQL API   │
              │  api.linear.app/      │
              │  graphql              │
              └───────────────────────┘
```

### 1.2 Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **RailCall Runtime** | Manages airlock flow, input validation, receipt signing |
| **Airlock** | Gates write operations: preview → approve → execute |
| **Validator** | Validates inputs against `input_schema` in `module.json` |
| **Executor** | Runs handler functions from `handlers/handler.py` |
| **Receipt** | Ed25519-signed record of command execution |
| **handler.py** | Implements 8 commands, calls Linear GraphQL API |
| **Linear API** | External service providing project management data |

### 1.3 Data Flow

**Read Operation (e.g., `list_teams`):**
1. User runs `railcall run agentstack/linear.list_teams`
2. RailCall validates inputs against schema
3. Handler executes GraphQL query
4. Response returned to user
5. Signed receipt emitted

**Write Operation (e.g., `create_issue`):**
1. User runs `railcall run agentstack/linear.create_issue --team=ENG --title="Fix bug"`
2. RailCall validates inputs against schema
3. Airlock generates preview (shows team, title, priority)
4. User approves in terminal
5. Handler executes GraphQL mutation
6. Response returned to user
7. Signed receipt emitted

---

## 2. Module Structure

### 2.1 Directory Layout

```
railcall-linear-module/
├── module.json              # Manifest: 8 commands, auth, side_effects
├── handlers/
│   └── handler.py           # 8 functions, one per command
└── .env.example             # LINEAR_API_KEY=lin_api_xxxxx
```

**Contest submission requires TWO URLs:**
1. Marketplace listing URL (after `railcall market publish .`)
2. README URL (hosted on GitHub repo, gist, or blog — ≤500 words)

The README is NOT bundled in the module directory. It's hosted separately and linked in the Freelancer contest entry.

### 2.2 File Responsibilities

| File | Purpose | Size |
|------|---------|------|
| `module.json` | Declares commands, auth pattern, side_effects | ~150 lines |
| `handlers/handler.py` | Implements 8 functions, GraphQL queries | ~300 lines |
| `.env.example` | Template for env var | 1 line |
| `README.md` (separate repo) | Contest submission doc, hosted on GitHub | ≤500 words |

---

## 3. Module Manifest (module.json)

### 3.1 Structure

```json
{
  "slug": "agentstack/linear",
  "version": "0.1.0",
  "description": "Linear project management — create/update issues, list teams/projects/cycles, add comments. contest:2026Q3",
  "auth": {
    "type": "api_key",
    "env_var": "LINEAR_API_KEY"
  },
  "commands": [
    {
      "name": "create_issue",
      "description": "Create a new issue in a Linear team",
      "input_schema": {
        "type": "object",
        "properties": {
          "team_id": { "type": "string", "description": "Team ID (e.g., ENG)" },
          "title": { "type": "string", "description": "Issue title" },
          "description": { "type": "string", "description": "Issue description (optional)" },
          "priority": { "type": "integer", "description": "Priority 0-4 (none, urgent, high, medium, low)" },
          "assignee_id": { "type": "string", "description": "Assignee user ID (optional)" }
        },
        "required": ["team_id", "title"]
      },
      "side_effects": "external"
    },
    {
      "name": "update_issue",
      "description": "Update an existing Linear issue",
      "input_schema": {
        "type": "object",
        "properties": {
          "issue_id": { "type": "string", "description": "Issue ID (e.g., ENG-123)" },
          "title": { "type": "string", "description": "New title (optional)" },
          "state_id": { "type": "string", "description": "New state ID (optional)" },
          "assignee_id": { "type": "string", "description": "New assignee ID (optional)" },
          "priority": { "type": "integer", "description": "New priority 0-4 (optional)" }
        },
        "required": ["issue_id"]
      },
      "side_effects": "external"
    },
    {
      "name": "list_issues",
      "description": "List issues with optional filters",
      "input_schema": {
        "type": "object",
        "properties": {
          "team_id": { "type": "string", "description": "Filter by team ID (optional)" },
          "state_id": { "type": "string", "description": "Filter by state ID (optional)" },
          "assignee_id": { "type": "string", "description": "Filter by assignee ID (optional)" },
          "limit": { "type": "integer", "description": "Max results (default 50)" }
        },
        "required": []
      },
      "side_effects": "none"
    },
    {
      "name": "list_teams",
      "description": "List all teams in workspace",
      "input_schema": {
        "type": "object",
        "properties": {},
        "required": []
      },
      "side_effects": "none"
    },
    {
      "name": "list_projects",
      "description": "List all projects in workspace",
      "input_schema": {
        "type": "object",
        "properties": {
          "limit": { "type": "integer", "description": "Max results (default 50)" }
        },
        "required": []
      },
      "side_effects": "none"
    },
    {
      "name": "list_cycles",
      "description": "List active cycles for a team",
      "input_schema": {
        "type": "object",
        "properties": {
          "team_id": { "type": "string", "description": "Team ID" },
          "limit": { "type": "integer", "description": "Max results (default 10)" }
        },
        "required": ["team_id"]
      },
      "side_effects": "none"
    },
    {
      "name": "add_comment",
      "description": "Add a comment to an issue",
      "input_schema": {
        "type": "object",
        "properties": {
          "issue_id": { "type": "string", "description": "Issue ID" },
          "body": { "type": "string", "description": "Comment body (markdown)" }
        },
        "required": ["issue_id", "body"]
      },
      "side_effects": "external"
    },
    {
      "name": "update_state",
      "description": "Transition issue to a new state",
      "input_schema": {
        "type": "object",
        "properties": {
          "issue_id": { "type": "string", "description": "Issue ID" },
          "state_id": { "type": "string", "description": "Target state ID" }
        },
        "required": ["issue_id", "state_id"]
      },
      "side_effects": "external"
    }
  ],
  "license_required": false
}
```

### 3.2 Auth Pattern

**Type:** `api_key`  
**Env var:** `LINEAR_API_KEY`  
**Header:** `Authorization: <api_key>` (Linear uses direct API key, no Bearer prefix)

**Why API key over OAuth2:**
- Linear doesn't support OAuth2 for third-party apps (API keys only)
- Simpler for contest (no OAuth flow setup)
- Can add OAuth2 post-contest if needed

---

## 4. Handler Implementation (handlers/handler.py)

### 4.1 Function Signatures

```python
def create_issue(inputs: dict, context: dict) -> dict:
    """Create a new issue in Linear."""
    # GraphQL mutation: issueCreate
    # Returns: { "issue": { "id": "...", "identifier": "ENG-123", "url": "..." } }

def update_issue(inputs: dict, context: dict) -> dict:
    """Update an existing issue."""
    # GraphQL mutation: issueUpdate
    # Returns: { "issue": { "id": "...", "identifier": "ENG-123" } }

def list_issues(inputs: dict, context: dict) -> dict:
    """List issues with optional filters."""
    # GraphQL query: issues
    # Returns: { "issues": [{ "id": "...", "title": "...", "state": {...} }] }

def list_teams(inputs: dict, context: dict) -> dict:
    """List all teams in workspace."""
    # GraphQL query: teams
    # Returns: { "teams": [{ "id": "...", "name": "...", "key": "ENG" }] }

def list_projects(inputs: dict, context: dict) -> dict:
    """List all projects in workspace."""
    # GraphQL query: projects
    # Returns: { "projects": [{ "id": "...", "name": "...", "state": "..." }] }

def list_cycles(inputs: dict, context: dict) -> dict:
    """List active cycles for a team."""
    # GraphQL query: cycles
    # Returns: { "cycles": [{ "id": "...", "name": "...", "number": 1 }] }

def add_comment(inputs: dict, context: dict) -> dict:
    """Add a comment to an issue."""
    # GraphQL mutation: commentCreate
    # Returns: { "comment": { "id": "...", "body": "..." } }

def update_state(inputs: dict, context: dict) -> dict:
    """Transition issue to a new state."""
    # GraphQL mutation: issueUpdate (state field)
    # Returns: { "issue": { "id": "...", "state": { "name": "Done" } } }
```

### 4.2 GraphQL Query Patterns

**Minimal field selection (no over-fetching):**

```python
# list_teams query
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

# create_issue mutation
mutation = """
mutation($input: IssueCreateInput!) {
  issueCreate(input: $input) {
    success
    issue {
      id
      identifier
      url
    }
  }
}
"""
```

### 4.3 Error Handling

```python
def _handle_graphql_response(response: dict) -> dict:
    """Check for GraphQL errors and raise with actionable messages."""
    if "errors" in response:
        error = response["errors"][0]
        message = error.get("message", "Unknown error")
        
        # Map Linear error codes to actionable messages
        if "not found" in message.lower():
            raise ValueError(f"Resource not found: {message}")
        elif "unauthorized" in message.lower():
            raise ValueError("Invalid API key or insufficient permissions")
        elif "rate limit" in message.lower():
            raise ValueError("Rate limit exceeded. Wait 10 seconds and retry.")
        else:
            raise ValueError(f"Linear API error: {message}")
    
    return response["data"]
```

### 4.4 Rate Limit Handling

```python
import time
import requests

def _make_request(query: str, variables: dict = None) -> dict:
    """Make GraphQL request with retry logic."""
    api_key = os.environ.get("LINEAR_API_KEY")
    if not api_key:
        raise ValueError("LINEAR_API_KEY environment variable not set")
    
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    max_retries = 3
    for attempt in range(max_retries):
        response = requests.post(
            "https://api.linear.app/graphql",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 429:
            # Rate limited — wait and retry
            wait_time = 10 * (attempt + 1)  # 10s, 20s, 30s
            time.sleep(wait_time)
            continue
        
        response.raise_for_status()
        return response.json()
    
    raise ValueError("Rate limit exceeded after 3 retries")
```

### 4.5 Pagination

```python
def list_issues(inputs: dict, context: dict) -> dict:
    """List issues with cursor-based pagination."""
    limit = inputs.get("limit", 50)
    cursor = None
    all_issues = []
    
    while len(all_issues) < limit:
        query = """
        query($after: String, $first: Int) {
          issues(after: $after, first: $first) {
            nodes {
              id
              identifier
              title
              state { id name }
              assignee { id name }
              priority
            }
            pageInfo {
              hasNextPage
              endCursor
            }
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

---

## 5. Security Considerations

### 5.1 Secret Management

| Secret | Storage | Access |
|--------|---------|--------|
| `LINEAR_API_KEY` | Environment variable | Read-only in handler |
| Publisher private key | `~/.railcall/publisher_key.json` (0600) | CLI only, never in handler |

**Rules:**
- No `print(api_key)` or `logging.info(api_key)` anywhere
- No secrets in error messages
- No secrets in receipt payloads
- No secrets in GraphQL queries/mutations

### 5.2 Input Validation

- All inputs validated against `input_schema` in `module.json`
- GraphQL variables used (no string interpolation in queries)
- Type checking on all inputs (string, integer, etc.)
- Required fields enforced by schema

### 5.3 Side Effects

| Command | side_effects | Rationale |
|---------|--------------|-----------|
| `create_issue` | external | Creates resource in external system |
| `update_issue` | external | Mutates external resource |
| `add_comment` | external | Writes to external system |
| `update_state` | external | Mutates external resource |
| `list_issues` | none | Read-only |
| `list_teams` | none | Read-only |
| `list_projects` | none | Read-only |
| `list_cycles` | none | Read-only |

---

## 6. Testing Strategy

### 6.1 Local Testing

```bash
# 1. Install module locally
railcall module install --from-path ~/Sites/freelance/railcall-linear-module

# 2. Set API key
export LINEAR_API_KEY=lin_api_xxxxx

# 3. Test read operation (no approval needed)
railcall run agentstack/linear.list_teams

# 4. Test write operation (approval required)
railcall run agentstack/linear.create_issue --team_id=ENG --title="Test issue"
```

### 6.2 Fresh Install Test

```bash
# From a fresh directory
cd /tmp
railcall market install agentstack/linear
railcall run agentstack/linear.list_teams
```

### 6.3 Edge Cases

| Case | Expected Behavior |
|------|-------------------|
| Missing API key | Clear error: "LINEAR_API_KEY not set" |
| Invalid API key | Clear error: "Invalid API key or insufficient permissions" |
| Rate limit hit | Retry 3x with exponential backoff, then error |
| Team not found | Clear error: "Team not found: ENG" |
| Issue not found | Clear error: "Issue not found: ENG-999" |
| Empty result set | Return `{ "issues": [] }` (not error) |

---

## 7. Deployment

### 7.1 Publish Flow

```bash
# 1. Ensure description includes contest tag
# module.json: "description": "... contest:2026Q3"

# 2. Publish
cd ~/Sites/freelance/railcall-linear-module
railcall market publish .

# 3. Wait for review (same-day during contest)
# 4. Verify listing is ACTIVE on marketplace
# 5. Post listing URL as contest entry on Freelancer
```

### 7.2 Post-Publish Verification

```bash
# Install as buyer would
railcall market install agentstack/linear
railcall run agentstack/linear.list_teams
```

---

## 8. Future Enhancements (Post-Contest)

| Enhancement | Priority | Effort |
|-------------|----------|--------|
| OAuth2 support | P2 | High (Linear doesn't support OAuth2 for third-party apps — requires partnership) |
| File attachments | P2 | Medium |
| Webhook triggers | P2 | High |
| Paid tier | P1 | Low (flip `license_required: true`, set price) |
| Additional commands (e.g., `delete_issue`, `list_users`) | P1 | Low |

---

## 9. Appendix

### 9.1 Linear GraphQL Schema

- Playground: https://studio.apollographql.com/public/Linear-API/variant/current/home
- Docs: https://developers.linear.app/docs/graphql/working-with-the-graphql-api

### 9.2 Reference Modules

- `sami666/hubspot` — Free, 2 commands, Bearer token
- `sami666/salesforce` — $199/mo, 20 commands, OAuth2

### 9.3 RailCall Docs

- Module developer guide: https://railcall.ai/docs/marketplace-developer/your-first-module
- Auth patterns: https://railcall.ai/docs/marketplace-developer/modules/#auth-patterns
