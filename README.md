# RailCall Linear Module

<div align="center">

**Production-grade Linear integration for RailCall with 45 commands**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-287%20unit%20%2B%2057%20live-brightgreen.svg)](./tests/)
[![Coverage](https://img.shields.io/badge/coverage-79%25-yellowgreen.svg)](./tests/)
[![CI](https://github.com/faizalmy/railcall-linear-module/actions/workflows/ci.yml/badge.svg)](https://github.com/faizalmy/railcall-linear-module/actions/workflows/ci.yml)

*Comprehensive Linear integration with automatic retry, rate limiting, caching, and enterprise-grade error handling*

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [Commands Reference](#commands-reference)
- [Advanced Usage](#advanced-usage)
- [Known Limitations](#known-limitations)
- [Architecture](#architecture)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Publishing to the Marketplace](#publishing-to-the-marketplace)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

### The problem it solves

Monday triage is death by a thousand clicks. Thirty issues arrived over the
weekend and each needs an owner, a priority and a state — thirty round trips in
Linear's UI. Scripting it against the API is fast but unreviewable: nobody sees
what is about to change, and nothing records who approved it.

This module stages the whole batch as one command. RailCall renders a preview, a
human approves once, and the run emits a signed receipt naming the approver and
the exact payload. If Linear rate-limits mid-batch it stops and returns
`not_attempted`, so a re-run resumes where it left off instead of redoing work.

**Who it's for:** small engineering teams whose triage, sprint setup and release
bookkeeping live in Linear, and who need an audit trail because someone
eventually asks "who closed those twelve tickets?"

### Scope

45 commands across 11 categories with built-in resilience, caching, and
comprehensive error handling. 18 reads execute immediately; 27 writes are
`write_requires_approval` and gated by the Approval Airlock.

**Key Benefits:**
- ✅ **45 Commands** - Full coverage of Linear's API surface
- ✅ **Automatic Retry** - Capped exponential backoff with jitter, honoring `Retry-After`
- ✅ **Rate Limiting** - Built-in protection against Linear's API limits (50 req/10s)
- ✅ **Caching** - Redis or in-memory, per-workspace scoped, for metadata reads
- ✅ **Input Validation** - Comprehensive validation for all parameters
- ✅ **Error Handling** - Detailed error messages with actionable guidance
- ✅ **Pagination** - Automatic pagination for large result sets
- ✅ **Bulk Operations** - Update multiple issues in a single operation
- ✅ **Issue Linking** - Create relationships between issues (blocks, blocked_by, related)

---

## ✨ Features

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **Issue Management** | Create, update, delete, search, and bulk update issues |
| **Team Management** | List and retrieve team information |
| **Project Management** | List and retrieve project details |
| **User Management** | List and retrieve user information |
| **Workflow States** | Manage custom workflow states |
| **Labels** | Create and manage issue labels |
| **Cycles** | Manage sprint cycles |
| **Comments** | Add, update, and delete comments |
| **Webhooks** | Configure webhook endpoints |
| **Milestones** | Track project milestones |

### Production Features

- **Resilience**: Single-layer retry with capped backoff and `Retry-After` support
- **Performance**: Redis/in-memory metadata caching with 5-minute TTL
- **Observability**: Comprehensive logging and error reporting
- **Security**: API key read from the station vault inside the Studio, never from process environment; never persisted or logged
- **Reliability**: Input validation and error handling

---

## 🚀 Installation

### Prerequisites

- Python 3.9 or higher
- RailCall CLI installed
- Linear API key

### Install via RailCall

```bash
railcall market install agentstack-labs/linear
```

The Studio verifies the bundle's Ed25519 signature and registers its 45 commands
on the next module reload.

### Install from Source

```bash
git clone https://github.com/faizalmy/railcall-linear-module.git
cd railcall-linear-module
pip install -e ".[dev]"
```

Build and install the signed bundle straight into your local station:

```bash
python3 tools/build_bundle.py --install
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LINEAR_API_KEY` | Standalone only | Library use and the test suite only. **The published bundle reads no environment variable at all** — the build replaces the standalone credential sources with constants, since the bundle only ever runs inside the Studio. |
| `REDIS_URL` | ❌ No | Redis connection URL (defaults to in-memory cache). Standalone only: the Redis backend is **stripped from the published bundle**, which always caches in memory. |

> **Inside the Studio the module never reads the process environment.** Env vars
> are visible via `ps auxe` and land in core dumps, so a vault bypass would
> defeat the credential the operator configured. A missing vault entry is
> surfaced as an error rather than silently papered over.

### Getting Your Linear API Key

1. Log in to [Linear](https://linear.app)
2. Go to **Settings** → **API**
3. Click **Create new API key**

Inside the Studio, save it in the **Sends** tab (see
[Configure the credential](#configure-the-credential)) — not as an environment
variable. The environment is only used for standalone/library use and the test
suite:

```bash
export LINEAR_API_KEY="lin_api_..."   # standalone only
```

### Optional: Redis Configuration

For production deployments, configure Redis for better performance:

```bash
export REDIS_URL="redis://localhost:6379/0"
```

---

## 🎬 Quick Start

### How commands are invoked

RailCall has no `railcall run` verb. The Studio server loads installed modules,
registers each command into its local handler table, and executes them from the
Studio UI or over MCP. Command ids are the dotted form:

| Command id | Mode |
|------------|------|
| `linear.list_teams` | read - runs immediately |
| `linear.list_issues` | read - runs immediately |
| `linear.create_issue` | write - Approval Airlock first |
| `linear.delete_issue` | write - Approval Airlock first |

Open the Studio, or wire the station into an AI client:

```bash
railcall studio
```

```bash
railcall mcp config claude
```

### Configure the credential

Commands stay `not_configured` until the `linear` provider has a saved
credential. There is no CLI command for this — `railcall set` only covers
Ollama, Discord and Anthropic settings — so use the Studio:

```bash
railcall studio
```

Open the **Sends** tab, choose **Linear — API key + team**, and fill both fields:

| Field | Where to get it |
|-------|-----------------|
| `api_key` | linear.app/settings/api → Create key (`lin_api_…`, entered masked) |
| `team_id` | The UUID in `linear.app/{workspace}/settings/teams/{team}/general` |

Both are required by the form, and both are used. The saved team becomes the
**default for every team-scoped command**, so `create_issue`, `get_team`,
`create_state`, `create_label`, `list_cycles` and `create_cycle` all work
without repeating the UUID:

```json
{ "command": "linear.create_issue", "inputs": { "title": "Fix login bug" } }
```

Pass `team_id` explicitly to override it, on a multi-team workspace. If neither
is present the command says so plainly rather than failing at the API.

Saving writes `keys.local.json` (owner-only) and marks the provider configured,
which flips the commands from `not_configured` to runnable.

That vault entry is the only credential source inside the Studio; the published
bundle reads no environment variable at all — `tools/build_bundle.py` strips
both the standalone credential fallback and the Redis cache config, and
`tests/unit/test_bundle.py` fails the build if either comes back. Outside the Studio —
library use and the test suite — `LINEAR_API_KEY` is used instead, because
there is no vault to read.

### Read commands

18 of the 45 commands are read-only and execute without approval. Start with
`linear.list_teams` - every other command needs a team UUID:

```json
{ "command": "linear.list_teams", "inputs": { "limit": 50 } }
```

### Write commands

The remaining 27 are `write_requires_approval`: the Studio renders a preview,
you approve, and the run emits a signed receipt.

```json
{ "command": "linear.create_issue",
  "inputs": { "team_id": "<uuid>", "title": "Fix login bug", "priority": 2 } }
```

Inputs are checked against each command's declared schema before a preview is
ever shown, so a payload missing `team_id` is rejected up front.

### Using it as a library

The handlers are ordinary Python and work standalone:

```python
from handlers.handler import list_teams, create_issue

teams = list_teams(limit=50)
```

---

## 📚 Commands Reference

### Issue Management (10 commands)

| Command | Description | Side Effects |
|---------|-------------|--------------|
| `list_issues` | List issues with optional filters | none |
| `get_issue` | Get detailed information about a specific issue | none |
| `create_issue` | Create a new issue | write |
| `update_issue` | Update an existing issue | write |
| `delete_issue` | Delete an issue permanently | write |
| `archive_issue` | Archive an issue (reversible) | write |
| `unarchive_issue` | Restore an archived issue | write |
| `search_issues` | Full-text search across titles, descriptions and comments | none |
| `bulk_update_issues` | Update multiple issues at once | write |
| `link_issues` | Link two issues with a relationship | write |

### Team Management (2 commands)

| Command | Description | Side Effects |
|---------|-------------|--------------|
| `list_teams` | List all teams in the workspace | none |
| `get_team` | Get detailed information about a specific team | none |

### Project Management (4 commands)

| Command | Description | Side Effects |
|---------|-------------|--------------|
| `list_projects` | List all projects in the workspace | none |
| `get_project` | Get detailed information about a specific project | none |
| `create_project` | Create a new project | write |
| `create_project_update` | Post a status update against a project | write |

### User Management (2 commands)

| Command | Description | Side Effects |
|---------|-------------|--------------|
| `list_users` | List all users in the workspace | none |
| `get_user` | Get detailed information about a specific user | none |

### Workflow States (3 commands)

| Command | Description | Side Effects |
|---------|-------------|--------------|
| `list_states` | List workflow states | none |
| `create_state` | Create a new workflow state | write |
| `update_state` | Update an existing workflow state | write |

### Labels (3 commands)

| Command | Description | Side Effects |
|---------|-------------|--------------|
| `list_labels` | List issue labels | none |
| `create_label` | Create a new issue label | write |
| `update_label` | Update an existing issue label | write |

### Cycles (4 commands)

| Command | Description | Side Effects |
|---------|-------------|--------------|
| `list_cycles` | List cycles for a team | none |
| `get_cycle` | Get detailed information about a specific cycle | none |
| `create_cycle` | Create a new cycle | write |
| `update_cycle` | Update an existing cycle | write |

### Comments (4 commands)

| Command | Description | Side Effects |
|---------|-------------|--------------|
| `list_comments` | List comments for an issue | none |
| `create_comment` | Create a new comment on an issue | write |
| `update_comment` | Update an existing comment | write |
| `delete_comment` | Delete a comment | write |

### Webhooks (4 commands)

| Command | Description | Side Effects |
|---------|-------------|--------------|
| `list_webhooks` | List all webhooks | none |
| `create_webhook` | Create a new webhook | write |
| `update_webhook` | Update an existing webhook | write |
| `delete_webhook` | Delete a webhook | write |

### Initiatives — Linear's roadmap (6 commands)

Linear renamed Roadmaps to Initiatives; there is no `roadmap` in the API. An
initiative groups projects under one goal and collects health updates.

| Command | Description | Side Effects |
|---------|-------------|--------------|
| `list_initiatives` | List initiatives, optionally filtered by status | none |
| `get_initiative` | Get one initiative with the projects rolled up under it | none |
| `create_initiative` | Create a new initiative | write |
| `update_initiative` | Update name, description, target date or status | write |
| `link_project_to_initiative` | Roll a project up under an initiative | write |
| `create_initiative_update` | Post a status update (`onTrack`/`atRisk`/`offTrack`) | write |

Statuses: `Proposed`, `Planned`, `Active`, `Completed`, `Canceled`.

### Milestones (3 commands)

| Command | Description | Side Effects |
|---------|-------------|--------------|
| `list_milestones` | List all milestones | none |
| `create_milestone` | Create a new milestone | write |
| `update_milestone` | Update an existing milestone | write |

---

## 🔧 Advanced Usage

### Caching

The module supports both Redis and in-memory caching. **Redis is for standalone
and self-hosted use only** — the published bundle ships without it, so a module
installed from the marketplace always caches in memory and reads no environment
variable:

```bash
# Use Redis (recommended for production)
export REDIS_URL="redis://localhost:6379"

# Use in-memory cache (default)
# No configuration needed
```

**Cache Behavior:**
- **What is cached**: workspace metadata only — `list_teams`, `get_team`,
  `list_projects`, `get_project`, `list_users`, `get_user`, `list_states`,
  `list_labels`. Issue and comment reads are never cached, so they always
  reflect current state.
- **TTL**: 5 minutes (`METADATA_TTL` in `handlers/handler.py`)
- **Invalidation**: `create_state`/`update_state` clear the state list;
  `create_label`/`update_label` clear the label list
- **Isolation**: keys are namespaced by a SHA-256 prefix of `LINEAR_API_KEY`,
  so one shared Redis can serve several workspaces without cross-reads.
  The raw key is never written to the cache.
- **Fallback**: Automatically falls back to in-memory if Redis unavailable
- **Configuration**: `REDIS_URL`, or `REDIS_HOST`/`REDIS_PORT`/`REDIS_DB`

### Rate Limiting

Retries are handled in one place (`LinearClient.execute`), so a single command
never sends more than 4 requests:
- **Max retries**: 3 (4 attempts total)
- **Backoff**: capped exponential with full jitter — `random(0, min(2^n, 60))` seconds
- **Retry-After**: honored when Linear sends it on a 429
- **Retried**: 429 and network failures only. Authentication, validation,
  permission and not-found errors fail immediately.
- **Linear API limit**: 50 requests per 10 seconds

`bulk_update_issues` stops as soon as it hits a rate limit and returns the IDs
it never attempted under `not_attempted`, so a retry can resume exactly where
it left off.

### Error Handling

All errors include:
- Error code
- Human-readable message
- Actionable guidance

**Example Error:**
```
Error: AUTHENTICATION_ERROR
Message: Invalid API key
Action: Check your LINEAR_API_KEY environment variable
```

### Pagination

Large result sets are automatically paginated:
- **Default limit**: 50 items
- **Maximum limit**: 250 items per request
- **Automatic**: Module handles pagination transparently

---

## ⚠️ Known Limitations

Honest scope boundaries, so nothing surprises you after install:

| Limitation | Detail |
|------------|--------|
| **UUIDs for everything but issues** | Issue commands accept `ENG-123` as well as the UUID; states, labels and the rest are UUID-only, and no command accepts a label *name*. The team UUID defaults to the one saved with the credential. |
| **Milestones are project-scoped** | `create_milestone` requires `project_id`. Linear has no workspace-level milestone — the type is `ProjectMilestone`. |
| **`create_webhook` needs a scope** | Exactly one of `team_id` or `all_public_teams`, even though the manifest lists only `url` as required. |
| **`create_state` rejects `triage`** | Triage is a per-team setting in Linear, not a creatable workflow state. Valid types: backlog, unstarted, started, completed, canceled. |
| **State names cap at 30 characters** | Enforced server-side by Linear. |
| **API key auth only** | No OAuth2 in this release. See [ARCHITECTURE.md §0](docs/ARCHITECTURE.md) for what is designed versus shipped. |
| **Caching is metadata-only** | Teams, projects, users, states and labels, 5-minute TTL. Issue and comment reads are never cached so they cannot go stale. |
| **`bulk_update_issues` is serial** | One request per issue. It stops on a rate limit and returns `not_attempted` for a clean resume. |
| **No webhook receiver** | The webhook *commands* manage subscriptions via Linear's API. Receiving and verifying inbound events is not implemented. |

---

## 🏗️ Architecture

```
railcall-linear-module/
├── module.json              # Authoring manifest (45 commands)
├── tools/
│   └── build_bundle.py      # Generates + signs the RailCall bundle
├── dist/                    # Generated bundle (gitignored)
│   └── agentstack-labs-linear/
│       ├── module.json      # Loader-shaped manifest (dotted command ids)
│       ├── handlers/handler.py  # Single flat file, no relative imports
│       └── module.sig       # Ed25519 signature over manifest + handler
├── handlers/
│   ├── handler.py           # Main handler with all commands
│   ├── client.py            # Linear GraphQL client with retry logic
│   ├── credentials.py       # Vault-then-environment key resolution
│   ├── cache.py             # Caching layer (Redis/memory)
│   ├── queries.py           # GraphQL query definitions
│   └── utils/
│       ├── errors.py        # Error handling utilities
│       ├── validation.py    # Input validation
│       └── pagination.py    # Pagination utilities
├── tests/                   # 287 unit + 57 live (package + generated bundle)
├── docs/                    # Documentation
└── .github/workflows/       # CI/CD pipeline
```

### Component Overview

| Component | Responsibility |
|-----------|----------------|
| **handler.py** | Command implementations and business logic |
| **client.py** | GraphQL API client with retry and rate limiting |
| **cache.py** | Caching layer with Redis/in-memory backends |
| **queries.py** | GraphQL query and mutation definitions |
| **utils/** | Shared utilities (errors, validation, pagination) |

---

## 💻 Development

### Prerequisites

- Python 3.9+
- pip or poetry
- Linear API key (for integration tests)

### Setup

```bash
# Clone the repository
git clone https://github.com/faizalmy/railcall-linear-module.git
cd railcall-linear-module

# Install dependencies
pip install -e ".[dev]"

# Set up environment
cp .env.example .env
# Edit .env with your LINEAR_API_KEY
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=handlers --cov-report=html

# Run specific test file
pytest tests/unit/test_handler.py

# Run integration tests
pytest tests/integration/
```

### Code Quality

```bash
# Format code
black handlers/ tests/

# Lint code
flake8 handlers/ tests/

# Type checking
mypy handlers/
```

### Building

```bash
# Build distribution
python -m build

# Install locally
pip install .
```

---

## 🔍 Troubleshooting

### Common Issues

#### Authentication Error

**Error:** `AUTHENTICATION_ERROR: Invalid API key`

**Solution:**
1. Verify your API key is set: `echo $LINEAR_API_KEY`
2. Check the key is valid in Linear Settings → API
3. Ensure the key has the required permissions

#### Rate Limit Exceeded

**Error:** `RATE_LIMIT_EXCEEDED: Too many requests`

**Solution:**
- The module automatically retries with exponential backoff
- If persistent, reduce request frequency
- Consider implementing request batching

#### Cache Connection Failed

**Error:** `CACHE_ERROR: Redis connection failed`

**Solution:**
- Verify Redis is running: `redis-cli ping`
- Check REDIS_URL environment variable
- Module will automatically fall back to in-memory cache

#### Validation Error

**Error:** `VALIDATION_ERROR: Invalid UUID format`

**Solution:**
- Issue arguments take either a UUID or the identifier from the Linear URL
  (`ENG-123`, case-insensitive)
- Every other ID must be a UUID (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
- Use `list_teams`, `list_projects`, etc. to retrieve valid IDs

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
```

### Getting Help

- **GitHub Issues**: [Report a bug](https://github.com/faizalmy/railcall-linear-module/issues)
- **RailCall Discord**: [Join the community](https://discord.gg/Ak62pfcVY)
- **Linear API Docs**: [Official documentation](https://developers.linear.app/docs)

---

## 📦 Publishing to the Marketplace

The repo is the readable source; what gets published is a generated, signed
bundle. Build it, then publish the directory:

```bash
python3 tools/build_bundle.py --minify --out dist-min
```

```bash
railcall market publish dist-min/agentstack-labs-linear --type=module --price=0
```

Three things are worth knowing before you do this yourself:

| | |
|---|---|
| **100 KiB body limit** | The marketplace returns `HTTP 413` above ~102,400 bytes. The unminified bundle is ~125 KB of POST body and does not fit, so `--minify` (which strips docstrings and comments, nothing else) is required. The build prints the projected POST size against the limit. |
| **`id` vs `name`** | The [published spec](https://railcall.ai/docs/marketplace-developer/modules/) documents commands keyed by `name`; the shipped Studio loader reads `id` and silently skips any command without one. The build emits **both**, plus `slug` alongside `id` at the top level. |
| **`market claim` is not a publish step** | The docs list `railcall market claim <slug>` before publishing. In the shipped CLI, `claim` is a *buyer's* post-purchase license claim. Publishing needs only `market publisher init` and `market login`. |

Prerequisites: `railcall market publisher init "<name>"` (once) and
`railcall market login`. The manifest's `publisher_pubkey` must match that
keypair or every install refuses the module.

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `pytest`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Code Standards

- Follow PEP 8 style guide
- Write tests for new features
- Update documentation
- Use type hints
- Keep functions focused and small

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Author

**AgentStack Labs**

- GitHub: [@faizalmy](https://github.com/faizalmy)
- Email: jai.crys@gmail.com

---

## 🏆 Contest

This module is submitted to the **RailCall Community Contest 2026 Q3**.

**Contest Tag**: `contest:2026Q3`

---

## 📊 Project Status

| Metric | Status |
|--------|--------|
| Version | 0.2.7 |
| Commands | 30 |
| Test Coverage | 287 unit (79% lines) + 57 live against a real Linear workspace |
| Python Support | 3.9+ |
| License | MIT |
| Production Ready | ✅ Yes |

---

<div align="center">

**Built with ❤️ for the RailCall community**

[⭐ Star this repo](https://github.com/faizalmy/railcall-linear-module) | [🐛 Report Bug](https://github.com/faizalmy/railcall-linear-module/issues) | [💡 Request Feature](https://github.com/faizalmy/railcall-linear-module/issues)

</div>
