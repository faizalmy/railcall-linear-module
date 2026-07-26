# RailCall Linear Module

<div align="center">

**Production-grade Linear integration for RailCall with 30 commands**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-40%20passed-brightgreen.svg)](./tests/)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

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
- [Architecture](#architecture)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

The RailCall Linear Module provides a complete, production-ready integration with Linear's project management platform. Built for enterprise use, it offers 30 commands across 7 categories with built-in resilience, caching, and comprehensive error handling.

**Key Benefits:**
- ✅ **30 Commands** - Full coverage of Linear's API surface
- ✅ **Automatic Retry** - Exponential backoff with jitter for transient failures
- ✅ **Rate Limiting** - Built-in protection against Linear's API limits (50 req/10s)
- ✅ **Caching** - Redis or in-memory caching for improved performance
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

- **Resilience**: Automatic retry with exponential backoff
- **Performance**: Redis/in-memory caching with 5-minute TTL
- **Observability**: Comprehensive logging and error reporting
- **Security**: API key authentication with secure storage
- **Reliability**: Input validation and error handling

---

## 🚀 Installation

### Prerequisites

- Python 3.9 or higher
- RailCall CLI installed
- Linear API key

### Install via RailCall

```bash
railcall module install agentstack-labs/linear
```

### Install from Source

```bash
git clone https://github.com/faizalmy/railcall-linear-module.git
cd railcall-linear-module
pip install -e .
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LINEAR_API_KEY` | ✅ Yes | Your Linear API key |
| `REDIS_URL` | ❌ No | Redis connection URL (defaults to in-memory cache) |

### Getting Your Linear API Key

1. Log in to [Linear](https://linear.app)
2. Go to **Settings** → **API**
3. Click **Create new API key**
4. Copy the key and set it as an environment variable:

```bash
export LINEAR_API_KEY="lin_api_..."
```

### Optional: Redis Configuration

For production deployments, configure Redis for better performance:

```bash
export REDIS_URL="redis://localhost:6379/0"
```

---

## 🎬 Quick Start

### List Issues

```bash
railcall run agentstack-labs/linear.list_issues \
  --team_id="team-uuid" \
  --state_id="state-uuid" \
  --limit=50
```

### Create an Issue

```bash
railcall run agentstack-labs/linear.create_issue \
  --team_id="team-uuid" \
  --title="Fix login bug" \
  --description="Users cannot login with SSO" \
  --priority=2 \
  --assignee_id="user-uuid"
```

### Bulk Update Issues

```bash
railcall run agentstack-labs/linear.bulk_update_issues \
  --issue_ids='["issue-1", "issue-2", "issue-3"]' \
  --state_id="state-uuid" \
  --priority=3
```

### Link Issues

```bash
railcall run agentstack-labs/linear.link_issues \
  --issue_id="issue-1" \
  --related_issue_id="issue-2" \
  --relationship_type="blocks"
```

---

## 📚 Commands Reference

### Issue Management (8 commands)

| Command | Description | Side Effects |
|---------|-------------|--------------|
| `list_issues` | List issues with optional filters | none |
| `get_issue` | Get detailed information about a specific issue | none |
| `create_issue` | Create a new issue | write |
| `update_issue` | Update an existing issue | write |
| `delete_issue` | Delete an issue | write |
| `search_issues` | Search issues by text query | none |
| `bulk_update_issues` | Update multiple issues at once | write |
| `link_issues` | Link two issues with a relationship | write |

### Team Management (2 commands)

| Command | Description | Side Effects |
|---------|-------------|--------------|
| `list_teams` | List all teams in the workspace | none |
| `get_team` | Get detailed information about a specific team | none |

### Project Management (2 commands)

| Command | Description | Side Effects |
|---------|-------------|--------------|
| `list_projects` | List all projects in the workspace | none |
| `get_project` | Get detailed information about a specific project | none |

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

### Milestones (3 commands)

| Command | Description | Side Effects |
|---------|-------------|--------------|
| `list_milestones` | List all milestones | none |
| `create_milestone` | Create a new milestone | write |
| `update_milestone` | Update an existing milestone | write |

---

## 🔧 Advanced Usage

### Caching

The module supports both Redis and in-memory caching:

```bash
# Use Redis (recommended for production)
export REDIS_URL="redis://localhost:6379"

# Use in-memory cache (default)
# No configuration needed
```

**Cache Behavior:**
- **TTL**: 5 minutes (configurable in code)
- **Invalidation**: Automatic on write operations
- **Fallback**: Automatically falls back to in-memory if Redis unavailable

### Rate Limiting

Automatic rate limiting with exponential backoff:
- **Max retries**: 3
- **Backoff factor**: 2 seconds
- **Jitter**: ±1 second
- **Linear API limit**: 50 requests per 10 seconds

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

## 🏗️ Architecture

```
railcall-linear-module/
├── module.json              # Module manifest with 30 commands
├── handlers/
│   ├── handler.py           # Main handler with all commands
│   ├── client.py            # Linear GraphQL client with retry logic
│   ├── cache.py             # Caching layer (Redis/memory)
│   ├── queries.py           # GraphQL query definitions
│   └── utils/
│       ├── errors.py        # Error handling utilities
│       ├── validation.py    # Input validation
│       └── pagination.py    # Pagination utilities
├── tests/                   # Test suite (40 tests)
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
- Ensure all IDs are valid UUIDs (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
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
| Version | 2.0.0 |
| Commands | 30 |
| Test Coverage | 40 tests passing |
| Python Support | 3.9+ |
| License | MIT |
| Production Ready | ✅ Yes |

---

<div align="center">

**Built with ❤️ for the RailCall community**

[⭐ Star this repo](https://github.com/faizalmy/railcall-linear-module) | [🐛 Report Bug](https://github.com/faizalmy/railcall-linear-module/issues) | [💡 Request Feature](https://github.com/faizalmy/railcall-linear-module/issues)

</div>
