# agentstack-labs/linear

Linear project management integration for RailCall. Create/update issues, list teams/projects/cycles, add comments — all governed by the RailCall airlock (preview → approve → execute → signed receipt).

## Who it's for

Dev teams using Linear who want governed automation with full audit trails. Engineering managers tracking issue state changes, product managers automating triage, DevOps engineers managing incident workflows — anyone who needs human-in-the-loop control before mutating Linear data.

## Install

```bash
railcall market install agentstack-labs/linear
```

## Setup

1. **Get API key**: Linear → Settings → API → Create key (personal or team-scoped)
2. **Set env var**: `export LINEAR_API_KEY=lin_api_xxxxx`

RailCall prompts for the env var on install. Keys are stored locally (127.0.0.1 only) — the marketplace never sees your credentials.

## Usage

**Read operations** (no approval required):

```bash
# List all teams
railcall run agentstack-labs/linear.list_teams

# List issues for a team
railcall run agentstack-labs/linear.list_issues --team_id=abc123

# List active cycles
railcall run agentstack-labs/linear.list_cycles --team_id=abc123 --limit=5
```

**Write operations** (approval required):

```bash
# Create issue (preview shows team, title, priority before approval)
railcall run agentstack-labs/linear.create_issue --team_id=abc123 --title="Fix login bug" --priority=2

# Update issue state (preview shows current → new state)
railcall run agentstack-labs/linear.update_state --issue_id=def456 --state_id=ghi789

# Add comment (preview shows comment body + target issue)
railcall run agentstack-labs/linear.add_comment --issue_id=def456 --body="Deployed to staging"
```

Every command emits a signed receipt at `~/.railcall/receipts/` — hash-chained, Ed25519-signed, tamper-evident.

## Commands

| Command | Type | Description |
|---------|------|-------------|
| `create_issue` | Write | Create new issue (team_id, title, priority, assignee) |
| `update_issue` | Write | Update issue fields (title, state, assignee, priority) |
| `list_issues` | Read | List issues with filters (team, state, assignee) |
| `list_teams` | Read | List all workspace teams |
| `list_projects` | Read | List all workspace projects |
| `list_cycles` | Read | List active cycles for a team |
| `add_comment` | Write | Add comment to issue (markdown) |
| `update_state` | Write | Transition issue to new state |

## Limitations

- **API key auth only** — Linear doesn't support OAuth2 for third-party apps. API keys are workspace-scoped but lack fine-grained permissions.
- **No file attachments** — Linear API supports them but out of scope for v0.1.0.
- **No webhook triggers** — Module is command-driven, not event-driven. Use RailCall workflows for event-based automation.
- **Rate limits** — Linear enforces 50 requests per 10 seconds per API key. Module includes retry logic with exponential backoff.

## Security

- API key read from env var only — never logged, never in receipts, never in error messages
- All GraphQL queries use parameterized variables (no string interpolation)
- Write operations gated by airlock — preview shows exactly what will change before approval
- Signed receipts provide tamper-evident audit trail

## Support

Open an issue on GitHub or ping @agentstack in the [RailCall Discord](https://discord.gg/Ak62pfcVY).
