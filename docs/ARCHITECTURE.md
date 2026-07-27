# Architecture Document: RailCall Linear Module (Production)

**Version:** 0.2.4  
**Status:** Planning — this document describes the target design, not all of which ships in 0.2.4  
**Author:** AgentStack Labs  
**Date:** 2026-07-26  
**Contest:** RailCall Community Contest 2026 Q3 — Track A (Best Module)

---

## 0. Implementation Status

What this document describes versus what version 0.2.4 actually ships:

| Area | Designed here | Shipped in 0.2.4 |
|------|---------------|------------------|
| 36 commands | ✅ | ✅ |
| Signed module bundle the Studio loader accepts | ✅ | ✅ — built by `tools/build_bundle.py`, Ed25519-signed, all 36 commands register |
| Credential from the station vault (`linear` provider) | ✅ | ✅ — vault is the **only** source inside the Studio; `LINEAR_API_KEY` applies to standalone use |
| Mutations never auto-retried (Linear has no idempotency key) | ✅ | ✅ |
| Stdlib-only transport (no third-party dependencies) | ✅ | ✅ |
| OAuth2 flow, `handlers/auth.py`, encrypted token file | ✅ | ❌ Not implemented — sections 3.3 and 3.4 are forward-looking |
| Retry with capped backoff + `Retry-After` | ✅ | ✅ |
| Metadata caching (Redis / in-memory) | ✅ | ✅ — applied to team, project, user, state and label reads only |
| Webhook **commands** (list/create/update/delete via the Linear API) | ✅ | ✅ |
| Webhook **receiver** (inbound signature verification, event dispatch) | ✅ | ❌ Not implemented |
| CI (pytest matrix + flake8 + mypy) | ✅ | ✅ |

Anything marked ❌ is a v2.1 target. No code in this repository depends on it.

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
              │   Linear GraphQL API  │
              │   api.linear.app/     │
              │   graphql             │
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
| **handler.py** | Implements 36 commands, calls Linear GraphQL API |
| **Linear API** | External service providing project management data |

### 1.3 Data Flow

**Read Operation (e.g., `list_teams`):**
1. Operator invokes `linear.list_teams` from the Studio (or over MCP)
2. RailCall validates inputs against schema
3. Handler checks cache → cache hit → return cached data
4. Cache miss → execute GraphQL query → cache result → return
5. Signed receipt emitted

**Write Operation (e.g., `create_issue`):**
1. Operator invokes `linear.create_issue` with `{team_id, title}` from the Studio
2. RailCall validates inputs against schema
3. Airlock generates preview (shows team, title, priority)
4. User approves in terminal
5. Handler executes GraphQL mutation
6. Invalidate cache for affected resources
7. Signed receipt emitted

---

## 2. Module Structure

### 2.1 Directory Layout

Actual tree as shipped. (An earlier draft of this document listed `auth.py`,
`webhooks.py` and a `queries/` package — none of those exist; see §0.)

```
railcall-linear-module/
├── module.json              # Authoring manifest: 36 commands, auth, side_effects
├── handlers/
│   ├── __init__.py
│   ├── handler.py           # All 36 command implementations
│   ├── client.py            # Linear GraphQL client (stdlib urllib, retry, no mutation replay)
│   ├── credentials.py       # Vault-inside-Studio / environment-standalone resolution
│   ├── cache.py             # Redis/in-memory metadata cache, tenant-scoped keys
│   ├── queries.py           # GraphQL documents (19 mutations, 15 queries)
│   └── utils/
│       ├── errors.py        # Error taxonomy + GraphQL error mapping
│       ├── validation.py    # Input validation
│       └── pagination.py    # Cursor-based pagination
├── tools/
│   └── build_bundle.py      # Generates + Ed25519-signs the Studio bundle
├── dist/, dist-min/         # Generated bundles (gitignored)
├── tests/
│   ├── unit/                # 214 tests, mocked API
│   ├── integration/         # 49 tests against a real Linear workspace
│   └── conftest.py
├── .github/workflows/ci.yml # pytest matrix + flake8 + mypy + bundle check
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md      # This document
│   └── DECISIONS.md         # Decision log
├── .env.example             # Standalone/test credentials only
├── pyproject.toml           # No runtime dependencies
├── CONTEST_README.md        # ≤500-word submission README
├── README.md
└── LICENSE
```

### 2.2 File Responsibilities

| File | Purpose | Lines |
|------|---------|-------|
| `module.json` | Authoring manifest: 36 commands, auth, side_effects | 929 |
| `handlers/handler.py` | All 36 command implementations | 1564 |
| `handlers/client.py` | GraphQL client: stdlib urllib, capped retry, mutations never replayed | 295 |
| `handlers/credentials.py` | Vault inside the Studio, environment standalone | 123 |
| `handlers/cache.py` | Metadata cache, tenant-scoped keys, Redis optional | 283 |
| `handlers/queries.py` | GraphQL documents (19 mutations, 15 queries) | 679 |
| `handlers/utils/*.py` | Error taxonomy, input validation, pagination | — |
| `tools/build_bundle.py` | Generates + Ed25519-signs the Studio bundle | 494 |
| `tests/unit/*.py` | 214 tests, mocked API | — |
| `tests/integration/*.py` | 49 tests against a real Linear workspace | — |
| `.github/workflows/ci.yml` | pytest matrix + flake8 + mypy + bundle size check | 56 |
| `CONTEST_README.md` | ≤500-word submission README | 79 |
| `README.md` | Full reference documentation | 695 |

---

## 3. Authentication Architecture

### 3.1 Dual Auth Strategy

The module supports two authentication methods:

| Method | Use Case | Security | Complexity |
|--------|----------|----------|------------|
| **API Key** | Simple automation, personal use | Medium (key in env var) | Low |
| **OAuth2** | Enterprise, team use, SSO | High (token rotation, scopes) | Medium |

### 3.2 API Key Authentication

```python
# handlers/auth.py

class APIKeyAuth:
    """API key authentication for simple use cases."""
    
    def __init__(self):
        self.api_key = os.environ.get("LINEAR_API_KEY")
        if not self.api_key:
            raise ValueError("LINEAR_API_KEY environment variable not set")
    
    def get_headers(self) -> dict:
        return {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }
```

**Security considerations:**
- API key stored in env var (never logged, never in receipts)
- Key scoped to workspace (no fine-grained permissions)
- No token rotation (manual key management)

### 3.3 OAuth2 Authentication

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
    
    def refresh_token(self) -> dict:
        """Refresh expired access token."""
        response = requests.post(self.TOKEN_URL, data={
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.token["refresh_token"]
        })
        token_data = response.json()
        self._save_token(token_data)
        return token_data
    
    def get_headers(self) -> dict:
        """Get authorization headers, refreshing token if needed."""
        if self._token_expired():
            self.refresh_token()
        return {
            "Authorization": f"Bearer {self.token['access_token']}",
            "Content-Type": "application/json"
        }
    
    def _token_expired(self) -> bool:
        """Check if access token is expired."""
        expires_at = self.token.get("expires_at", 0)
        return time.time() >= (expires_at - 60)  # 60s buffer
    
    def _save_token(self, token_data: dict):
        """Save token to encrypted storage."""
        # Encrypt token before saving
        encrypted = self._encrypt_token(token_data)
        token_path = os.path.expanduser("~/.railcall/linear_oauth_token.enc")
        with open(token_path, "w") as f:
            f.write(encrypted)
    
    def _load_token(self) -> dict:
        """Load token from encrypted storage."""
        token_path = os.path.expanduser("~/.railcall/linear_oauth_token.enc")
        if not os.path.exists(token_path):
            raise ValueError("OAuth2 token not found. Run `railcall connect linear` first.")
        with open(token_path, "r") as f:
            encrypted = f.read()
        return self._decrypt_token(encrypted)
    
    def _encrypt_token(self, token_data: dict) -> str:
        """Encrypt token using AES-256."""
        from cryptography.fernet import Fernet
        key = self._get_encryption_key()
        f = Fernet(key)
        return f.encrypt(json.dumps(token_data).encode()).decode()
    
    def _decrypt_token(self, encrypted: str) -> dict:
        """Decrypt token using AES-256."""
        from cryptography.fernet import Fernet
        key = self._get_encryption_key()
        f = Fernet(key)
        return json.loads(f.decrypt(encrypted.encode()).decode())
    
    def _get_encryption_key(self) -> bytes:
        """Derive encryption key from machine-specific data."""
        # Use machine ID + user ID as key material
        import platform
        import getpass
        key_material = f"{platform.node()}-{getpass.getuser()}-linear-oauth"
        return base64.urlsafe_b64encode(hashlib.sha256(key_material.encode()).digest())
```

**Security considerations:**
- Tokens encrypted at rest (AES-256)
- Automatic token refresh before expiry
- Scopes limit permissions (read, write, issues:create, issues:update)
- State parameter prevents CSRF attacks
- Machine-specific encryption key (no cross-machine token theft)

### 3.4 Auth Pattern Declaration

```json
// module.json
{
  "auth": {
    "type": "oauth2",
    "provider": "linear",
    "fallback": "api_key",
    "env_var": "LINEAR_API_KEY"
  }
}
```

---

## 4. Caching Architecture

### 4.1 Cache Strategy

| Operation | Cache TTL | Invalidation |
|-----------|-----------|--------------|
| `list_teams` | 5 minutes | On team create/update/delete |
| `list_projects` | 5 minutes | On project create/update/delete |
| `list_issues` | 2 minutes | On issue create/update/delete |
| `list_labels` | 10 minutes | On label create/update/delete |
| `list_states` | 10 minutes | On state create/update/delete |
| `list_cycles` | 5 minutes | On cycle create/update/delete |
| `list_webhooks` | 5 minutes | On webhook create/delete |

### 4.2 Cache Implementation

```python
# handlers/cache.py

import redis
import json
import hashlib
from typing import Optional, Any

class CacheManager:
    """Redis-backed cache with in-memory fallback."""
    
    def __init__(self, backend: str = "auto"):
        """Initialize cache backend.
        
        Args:
            backend: "redis", "memory", or "auto" (try redis, fallback to memory)
        """
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
            # TODO: Implement TTL for memory cache
    
    def invalidate(self, pattern: str):
        """Invalidate cache entries matching pattern."""
        if self.backend == "redis":
            keys = self.redis_client.keys(f"*{pattern}*")
            if keys:
                self.redis_client.delete(*keys)
        else:
            keys_to_delete = [k for k in self.memory_cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self.memory_cache[key]
    
    def _make_key(self, key: str) -> str:
        """Create cache key with module prefix."""
        return f"agentstack-labs/linear:{key}"
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        if self.backend == "redis":
            info = self.redis_client.info()
            return {
                "backend": "redis",
                "hit_rate": info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1), 1),
                "memory_used": info.get("used_memory_human", "0B")
            }
        else:
            return {
                "backend": "memory",
                "entries": len(self.memory_cache)
            }
```

### 4.3 Cache Usage Pattern

```python
# handlers/handler.py

def list_teams(inputs: dict, context: dict) -> dict:
    """List all teams in workspace."""
    cache_key = "teams:all"
    
    # Check cache
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # Cache miss → execute query
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
    
    data = client.execute(query)
    result = {"teams": data["teams"]["nodes"]}
    
    # Cache result
    cache.set(cache_key, result, ttl=300)
    
    return result

def create_issue(inputs: dict, context: dict) -> dict:
    """Create a new issue in Linear."""
    # ... execute mutation ...
    
    # Invalidate cache for affected resources
    cache.invalidate("issues:")
    cache.invalidate(f"team:{inputs['team_id']}:issues")
    
    return result
```

---

## 5. Error Handling Architecture

### 5.1 Error Categories

| Category | Example | User Action |
|----------|---------|-------------|
| **Authentication** | Invalid API key, expired OAuth token | Re-authenticate |
| **Authorization** | Insufficient permissions | Request access from admin |
| **Validation** | Invalid input, missing required field | Fix input parameters |
| **Rate Limit** | 429 Too Many Requests | Wait and retry (automatic) |
| **Not Found** | Team/issue/project doesn't exist | Check ID, verify resource exists |
| **Network** | Timeout, connection refused | Retry (automatic) or check connectivity |
| **GraphQL** | Query syntax error, field doesn't exist | Report bug to module maintainer |

### 5.2 Error Handling Implementation

```python
# handlers/utils/errors.py

class LinearError(Exception):
    """Base exception for Linear API errors."""
    
    def __init__(self, message: str, code: str = None, details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

class AuthenticationError(LinearError):
    """Raised when authentication fails."""
    pass

class AuthorizationError(LinearError):
    """Raised when user lacks permissions."""
    pass

class ValidationError(LinearError):
    """Raised when input validation fails."""
    pass

class RateLimitError(LinearError):
    """Raised when rate limit is hit."""
    pass

class NotFoundError(LinearError):
    """Raised when resource doesn't exist."""
    pass

class NetworkError(LinearError):
    """Raised when network request fails."""
    pass

def handle_graphql_errors(response: dict):
    """Parse GraphQL errors and raise appropriate exceptions."""
    if "errors" not in response:
        return
    
    error = response["errors"][0]
    message = error.get("message", "Unknown error")
    extensions = error.get("extensions", {})
    code = extensions.get("code")
    
    # Map Linear error codes to exceptions
    if code == "AUTHENTICATION_ERROR":
        raise AuthenticationError(
            "Invalid API key or expired OAuth token. Run `railcall connect linear` to re-authenticate.",
            code=code,
            details=extensions
        )
    elif code == "AUTHORIZATION_ERROR":
        raise AuthorizationError(
            "Insufficient permissions. Contact your Linear admin to request access.",
            code=code,
            details=extensions
        )
    elif code == "VALIDATION_ERROR":
        raise ValidationError(
            f"Invalid input: {message}",
            code=code,
            details=extensions
        )
    elif code == "NOT_FOUND":
        raise NotFoundError(
            f"Resource not found: {message}",
            code=code,
            details=extensions
        )
    elif code == "RATE_LIMITED":
        raise RateLimitError(
            "Rate limit exceeded. Retrying automatically...",
            code=code,
            details=extensions
        )
    else:
        raise LinearError(
            f"Linear API error: {message}",
            code=code,
            details=extensions
        )
```

### 5.3 Retry Logic

```python
# handlers/client.py

import time
import random
from typing import Callable

def execute_with_retry(
    operation: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0
) -> dict:
    """Execute operation with exponential backoff + jitter.
    
    Args:
        operation: Callable that performs the operation
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
    
    Returns:
        Operation result
    
    Raises:
        LinearError: If all retries fail
    """
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            return operation()
        except RateLimitError as e:
            last_error = e
            if attempt < max_retries:
                # Exponential backoff with jitter
                delay = min(base_delay * (2 ** attempt), max_delay)
                jitter = random.uniform(0, delay * 0.1)
                time.sleep(delay + jitter)
        except NetworkError as e:
            last_error = e
            if attempt < max_retries:
                delay = min(base_delay * (2 ** attempt), max_delay)
                time.sleep(delay)
    
    raise last_error
```

---

## 6. Webhook Architecture

### 6.1 Webhook Registration

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
```

### 6.2 Webhook Signature Verification

```python
# handlers/webhooks.py

import hmac
import hashlib

def verify_webhook_signature(payload: bytes, signature: str, webhook_id: str) -> bool:
    """Verify webhook signature using HMAC-SHA256.
    
    Args:
        payload: Raw request body
        signature: Signature from X-Linear-Signature header
        webhook_id: Webhook ID for secret lookup
    
    Returns:
        True if signature is valid
    """
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

---

## 7. Testing Architecture

### 7.1 Test Strategy

| Test Type | Coverage | Execution | Purpose |
|-----------|----------|-----------|---------|
| **Unit Tests** | >80% code coverage | Every commit | Test individual functions in isolation |
| **Integration Tests** | All 36 commands | Every commit | Test against Linear sandbox API |
| **End-to-End Tests** | Critical workflows | Nightly | Test full airlock flow |
| **Performance Tests** | Read/write latency | Weekly | Ensure SLA compliance |

### 7.2 Unit Test Example

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

def test_list_teams_cache_hit(mock_client):
    """Test cache hit returns cached data."""
    # Pre-populate cache
    from handlers.cache import cache
    cache.set("teams:all", {"teams": [{"id": "cached"}]}, ttl=300)
    
    # Execute
    result = list_teams({}, {})
    
    # Assert
    assert result["teams"][0]["id"] == "cached"
    mock_client.execute.assert_not_called()

def test_list_teams_auth_error(mock_client):
    """Test authentication error handling."""
    from handlers.utils.errors import AuthenticationError
    mock_client.execute.side_effect = AuthenticationError("Invalid API key")
    
    with pytest.raises(AuthenticationError):
        list_teams({}, {})
```

### 7.3 Integration Test Example

```python
# tests/integration/test_create_issue.py

import pytest
import os
from handlers.handler import create_issue, list_teams

@pytest.fixture
def team_id():
    """Get a real team ID from Linear sandbox."""
    result = list_teams({}, {})
    return result["teams"][0]["id"]

def test_create_issue_real_api(team_id):
    """Test issue creation against real Linear API."""
    # Skip if no API key configured
    if not os.environ.get("LINEAR_API_KEY"):
        pytest.skip("LINEAR_API_KEY not set")
    
    # Create issue
    result = create_issue({
        "team_id": team_id,
        "title": "Integration test issue",
        "description": "This is a test issue created by integration tests",
        "priority": 3
    }, {})
    
    # Assert
    assert "issue" in result
    assert result["issue"]["title"] == "Integration test issue"
    assert "id" in result["issue"]
    
    # Cleanup: delete the issue
    # (Linear doesn't have a delete mutation, so we just leave it)
```

### 7.4 CI/CD Pipeline

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

---

## 8. Security Considerations

### 8.1 Secret Management

| Secret | Storage | Access | Rotation |
|--------|---------|--------|----------|
| `LINEAR_API_KEY` | Environment variable | Read-only in handler | Manual |
| OAuth2 tokens | Encrypted file (~/.railcall/linear_oauth_token.enc) | Read/write by auth module | Automatic |
| Webhook secrets | Encrypted file (~/.railcall/linear_webhook_secrets.enc) | Read/write by webhook module | Manual |
| Publisher private key | ~/.railcall/publisher_key.json (0600) | CLI only, never in handler | Manual |

### 8.2 Input Validation

```python
# handlers/utils/validation.py

def validate_issue_id(issue_id: str):
    """Validate Linear issue ID format."""
    # Linear issue IDs are UUIDs
    import re
    if not re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', issue_id):
        raise ValidationError(f"Invalid issue ID format: {issue_id}")

def validate_priority(priority: int):
    """Validate priority value (0-4)."""
    if priority not in [0, 1, 2, 3, 4]:
        raise ValidationError(f"Priority must be 0-4, got {priority}")

def validate_team_id(team_id: str):
    """Validate team ID format."""
    validate_issue_id(team_id)  # Same UUID format
```

### 8.3 Rate Limiting

```python
# handlers/client.py

class RateLimiter:
    """Token bucket rate limiter for Linear API."""
    
    def __init__(self, max_requests: int = 50, window_seconds: int = 10):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.tokens = max_requests
        self.last_refill = time.time()
    
    def acquire(self):
        """Acquire a token, blocking if necessary."""
        while True:
            self._refill()
            if self.tokens > 0:
                self.tokens -= 1
                return
            time.sleep(0.1)
    
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        refill_amount = (elapsed / self.window_seconds) * self.max_requests
        self.tokens = min(self.max_requests, self.tokens + refill_amount)
        self.last_refill = now
```

---

## 9. Performance Optimization

### 9.1 Query Optimization

```python
# handlers/queries/issues.py

# BAD: Over-fetching
query = """
query {
  issues {
    nodes {
      id
      title
      description
      state { id name color }
      assignee { id name email avatarUrl }
      priority
      createdAt
      updatedAt
      # ... 20 more fields
    }
  }
}
"""

# GOOD: Minimal field selection
query = """
query {
  issues {
    nodes {
      id
      identifier
      title
      state { id name }
      priority
    }
  }
}
"""
```

### 9.2 Pagination

```python
# handlers/utils/pagination.py

def paginate_query(query: str, variables: dict, limit: int) -> list:
    """Execute paginated GraphQL query.
    
    Args:
        query: GraphQL query with pagination support
        variables: Query variables
        limit: Maximum number of results
    
    Returns:
        List of all results
    """
    all_results = []
    cursor = None
    
    while len(all_results) < limit:
        variables["first"] = min(50, limit - len(all_results))
        if cursor:
            variables["after"] = cursor
        
        data = client.execute(query, variables)
        
        # Extract results from response (structure varies by query)
        results = data.get("issues", data.get("teams", data.get("projects", {})))
        nodes = results.get("nodes", [])
        all_results.extend(nodes)
        
        # Check for more pages
        page_info = results.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break
        
        cursor = page_info.get("endCursor")
    
    return all_results[:limit]
```

---

## 10. Deployment Architecture

### 10.1 Module Publishing

```bash
# 1. Run tests
pytest tests/ --cov=handlers --cov-report=term-missing

# 2. Lint code
black handlers/ tests/
flake8 handlers/ tests/
mypy handlers/

# 3. Sign module
railcall market publisher init agentstack-labs  # First time only
railcall market publisher register              # First time only

# 4. Publish
railcall market publish . --type=module --id=agentstack-labs/linear

# 5. Verify installation
railcall market install agentstack-labs/linear
# Studio → Commands → linear.list_teams   (there is no `railcall run` verb)
```

### 10.2 Version Management

```json
// module.json
{
  "slug": "agentstack-labs/linear",
  "version": "0.2.4",
  "changelog": "https://github.com/faizalmy/railcall-linear-module/blob/main/CHANGELOG.md"
}
```

### 10.3 Monitoring

```python
# handlers/utils/metrics.py

class Metrics:
    """Simple metrics collector."""
    
    def __init__(self):
        self.counters = {}
        self.histograms = {}
    
    def increment(self, name: str, value: int = 1):
        """Increment counter."""
        self.counters[name] = self.counters.get(name, 0) + value
    
    def observe(self, name: str, value: float):
        """Observe histogram value."""
        if name not in self.histograms:
            self.histograms[name] = []
        self.histograms[name].append(value)
    
    def get_stats(self) -> dict:
        """Get all metrics."""
        return {
            "counters": self.counters,
            "histograms": {
                name: {
                    "count": len(values),
                    "avg": sum(values) / len(values) if values else 0,
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0
                }
                for name, values in self.histograms.items()
            }
        }

# Usage
metrics = Metrics()

def list_teams(inputs: dict, context: dict) -> dict:
    start_time = time.time()
    
    # Check cache
    cached = cache.get("teams:all")
    if cached:
        metrics.increment("cache.hit")
        return cached
    
    metrics.increment("cache.miss")
    
    # Execute query
    data = client.execute(query)
    
    # Record latency
    latency = time.time() - start_time
    metrics.observe("list_teams.latency", latency)
    
    return result
```

---

## 11. Migration Guide (v1.0 → v2.0)

### 11.1 Breaking Changes

| Change | Impact | Migration |
|--------|--------|-----------|
| OAuth2 support added | None (backward compatible) | Optional: configure OAuth2 for enterprise use |
| Caching layer added | Improved performance | Optional: configure Redis for production |
| 22 new commands | Expanded functionality | No migration needed |
| Error handling improved | Better error messages | No migration needed |

### 11.2 Upgrade Steps

```bash
# 1. Uninstall v1.0
railcall market uninstall agentstack-labs/linear

# 2. Install v2.0
railcall market install agentstack-labs/linear

# 3. Verify installation
# Studio → Commands → linear.list_teams   (there is no `railcall run` verb)

# 4. (Optional) Configure OAuth2
railcall connect linear

# 5. (Optional) Configure Redis caching
export REDIS_HOST=localhost
export REDIS_PORT=6379
```

---

## 12. Appendix

### 12.1 Linear API Documentation

- GraphQL schema: https://studio.apollographql.com/public/Linear-API/variant/current/home
- API key setup: https://linear.app/docs/api-keys
- OAuth2 setup: https://developers.linear.app/docs/oauth/authentication
- Rate limits: https://developers.linear.app/docs/graphql/working-with-the-graphql-api/rate-limiting
- Webhooks: https://developers.linear.app/docs/webhooks

### 12.2 RailCall Documentation

- Module developer guide: https://railcall.ai/docs/marketplace-developer/your-first-module
- Auth patterns: https://railcall.ai/docs/marketplace-developer/modules/#auth-patterns
- Contest brief: https://railcall.ai/contest

### 12.3 Reference Modules

- `sami666/hubspot` — Free, 2 commands, Bearer token auth
- `sami666/salesforce` — $199/mo, 20 commands, OAuth2
