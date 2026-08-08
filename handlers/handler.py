"""RailCall Linear Module - Production Grade

A comprehensive Linear integration for RailCall with 45 commands covering:
- Issue management (10): list, get, create, update, delete, archive, unarchive,
  search, bulk_update, link
- Team management (2): list, get
- Project management (4): list, get, create, post update
- User management (2): list, get
- Workflow states (3): list, create, update
- Labels (3): list, create, update
- Cycles (4): list, get, create, update
- Comments (4): list, create, update, delete
- Webhooks (4): list, create, update, delete
- Milestones (3): list, create, update
- Initiatives (6): list, get, create, update, link project, post update

All commands support:
- Automatic retry with capped exponential backoff and Retry-After support
- Input validation
- Comprehensive error handling

Read commands for workspace metadata (teams, projects, users, states, labels)
are cached for METADATA_TTL seconds; issue and comment reads are never cached.
"""

import re
from typing import Any, Dict, List, Optional

from .client import execute_query
from .cache import cached, get_cache, make_cache_key, invalidate_all
from .credentials import resolve_default_team_id
from .queries import (
    LIST_INITIATIVES,
    GET_INITIATIVE,
    CREATE_INITIATIVE,
    UPDATE_INITIATIVE,
    LINK_PROJECT_TO_INITIATIVE,
    CREATE_INITIATIVE_UPDATE,
    LIST_ISSUES,
    GET_ISSUE,
    CREATE_ISSUE,
    UPDATE_ISSUE,
    DELETE_ISSUE,
    CREATE_ISSUE_RELATION,
    ARCHIVE_ISSUE,
    UNARCHIVE_ISSUE,
    SEARCH_ISSUES,
    CREATE_PROJECT_UPDATE,
    LIST_TEAMS,
    GET_TEAM,
    LIST_PROJECTS,
    GET_PROJECT,
    CREATE_PROJECT,
    LIST_USERS,
    GET_USER,
    LIST_STATES,
    CREATE_STATE,
    UPDATE_STATE,
    LIST_LABELS,
    CREATE_LABEL,
    UPDATE_LABEL,
    LIST_CYCLES,
    GET_CYCLE,
    CREATE_CYCLE,
    UPDATE_CYCLE,
    LIST_COMMENTS,
    CREATE_COMMENT,
    UPDATE_COMMENT,
    DELETE_COMMENT,
    LIST_WEBHOOKS,
    CREATE_WEBHOOK,
    UPDATE_WEBHOOK,
    DELETE_WEBHOOK,
    LIST_MILESTONES,
    CREATE_MILESTONE,
    UPDATE_MILESTONE,
    RESOLVE_TEAM_BY_NAME,
    RESOLVE_PROJECT_BY_NAME,
    RESOLVE_CYCLE_BY_NAME,
    RESOLVE_USER_BY_NAME,
)
from .utils import (
    AuthenticationError,
    LinearError,
    RateLimitError,
    validate_issue_id,
    validate_team_id,
    validate_project_id,
    validate_user_id,
    validate_state_id,
    validate_label_id,
    validate_cycle_id,
    validate_comment_id,
    validate_milestone_id,
    validate_initiative_id,
    validate_webhook_id,
    validate_priority,
    validate_limit,
    validate_url,
    validate_color,
    validate_iso_date,
    validate_timeless_date,
    validate_resource_types,
    validate_non_empty,
    paginate_query,
)

# Cache lifetime for workspace metadata that rarely changes between calls.
METADATA_TTL = 300


def _run_query(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    """Adapter matching paginate_query's query_func signature."""
    return execute_query(query, variables)


# ============================================================================
# NAME -> ID RESOLUTION
# ============================================================================

_UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I
)

# resource_type -> (query, the GraphQL field the nodes come back under)
_NAME_LOOKUPS: Dict[str, tuple] = {
    "team": (RESOLVE_TEAM_BY_NAME, "teams"),
    "project": (RESOLVE_PROJECT_BY_NAME, "projects"),
    "cycle": (RESOLVE_CYCLE_BY_NAME, "cycles"),
    "user": (RESOLVE_USER_BY_NAME, "users"),
}


def _lookup_id_by_name(name: str, resource_type: str) -> str:
    """Resolve one human-readable name to its Linear UUID.

    Cached for METADATA_TTL: names map to the same ID for the life of the
    resource, and a bulk command would otherwise re-query for every item.

    Raises:
        ValueError: if nothing matches, or if the name is ambiguous.
    """
    if resource_type not in _NAME_LOOKUPS:
        raise ValueError(f"Cannot resolve names for resource type '{resource_type}'")

    query, data_key = _NAME_LOOKUPS[resource_type]

    cache = get_cache()
    cache_key = make_cache_key("_lookup_id_by_name", (resource_type, name), {})
    hit = cache.get(cache_key)
    if hit is not None:
        return hit

    result = execute_query(query, {"name": name})
    nodes = (result.get(data_key) or {}).get("nodes") or []

    if not nodes:
        raise ValueError(
            f"No {resource_type} named '{name}' found. Pass the UUID, or check "
            f"the name matches exactly (matching is case-sensitive)."
        )
    if len(nodes) > 1:
        raise ValueError(
            f"'{name}' matches {len(nodes)} {resource_type}s. Pass the UUID "
            f"instead: {', '.join(n['id'] for n in nodes)}"
        )

    resolved = nodes[0]["id"]
    cache.set(cache_key, resolved, ttl=METADATA_TTL)
    return resolved


def _resolve_id(
    value: Optional[str],
    resource_type: str,
    context: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """Accept either a UUID or a name, always return a UUID.

    A UUID passes straight through untouched, so this is safe to layer in front
    of the existing validators without changing behaviour for callers that
    already pass IDs.
    """
    if not value:
        return value
    if _UUID_RE.match(value):
        return value
    return _lookup_id_by_name(value, resource_type)


def _resolve_ids(
    values: Optional[List[str]],
    resource_type: str,
    context: Optional[Dict[str, Any]] = None,
) -> Optional[List[str]]:
    """List form of _resolve_id - each entry may be a UUID or a name."""
    if not values:
        return values
    return [_resolve_id(v, resource_type, context) for v in values]


def _team_id_or_default(team_id: Optional[str]) -> str:
    """The caller's team, or the one saved alongside the credential.

    The Studio's credential form requires a team UUID next to the API key, so
    every configured install has one. Using it as the default means the common
    single-team case does not have to paste the same UUID into every command.

    If no team is saved and the workspace has exactly one team, auto-detect it.

    Raises:
        ValueError: if no team was passed, none is saved, and auto-detect fails.
    """
    resolved = team_id or resolve_default_team_id()
    if not resolved:
        # Auto-detect: if workspace has exactly one team, use it
        result = execute_query(
            "{ teams { nodes { id name } } }", {}
        )
        teams = result.get("teams", {}).get("nodes", [])
        if len(teams) == 1:
            resolved = teams[0]["id"]
        else:
            raise ValueError(
                "No team_id given and none saved with the credential. Pass team_id, "
                "or save a default team in Studio → Sends → Linear."
            )

    resolved = _resolve_id(resolved, "team")
    validate_team_id(resolved)
    return resolved


# ============================================================================
# ISSUE COMMANDS (8 commands)
# ============================================================================

def list_issues(
    team_id: Optional[str] = None,
    state_id: Optional[str] = None,
    assignee_id: Optional[str] = None,
    limit: int = 50,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """List issues with optional filters.
    
    Args:
        team_id: Filter by team ID
        state_id: Filter by state ID
        assignee_id: Filter by assignee ID
        limit: Maximum number of results (default: 50)
        context: RailCall context (unused)
    
    Returns:
        Dict with 'issues' list and 'page_info'
    """
    limit = validate_limit(limit, max_limit=250)

    # Build filter as an IssueFilter object (never string interpolation - the
    # GraphQL variable is typed, and raw text would be both invalid and injectable)
    issue_filter: Dict[str, Any] = {}
    if team_id:
        team_id = _resolve_id(team_id, "team", context)
        validate_team_id(team_id)
        issue_filter["team"] = {"id": {"eq": team_id}}
    if state_id:
        validate_state_id(state_id)
        issue_filter["state"] = {"id": {"eq": state_id}}
    if assignee_id:
        assignee_id = _resolve_id(assignee_id, "user", context)
        validate_user_id(assignee_id)
        issue_filter["assignee"] = {"id": {"eq": assignee_id}}

    issues = paginate_query(
        query_func=_run_query,
        query=LIST_ISSUES,
        variables={"filter": issue_filter} if issue_filter else {},
        limit=limit,
        data_key="issues",
    )
    
    return {
        "issues": issues,
        "count": len(issues),
    }


def get_issue(issue_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get detailed information about a specific issue.
    
    Args:
        issue_id: Linear issue ID
        context: RailCall context (unused)
    
    Returns:
        Dict with issue details
    """
    validate_issue_id(issue_id)
    
    result = execute_query(GET_ISSUE, {"id": issue_id})
    
    if not result.get("issue"):
        raise ValueError(f"Issue not found: {issue_id}")
    
    return {"issue": result["issue"]}


def create_issue(
    title: str,
    team_id: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[int] = None,
    assignee_id: Optional[str] = None,
    state_id: Optional[str] = None,
    project_id: Optional[str] = None,
    label_ids: Optional[List[str]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a new issue.
    
    Args:
        title: Issue title (required)
        team_id: Team ID. Defaults to the team saved with the credential.
        description: Issue description (markdown)
        priority: Priority (0=none, 1=urgent, 2=high, 3=medium, 4=low)
        assignee_id: Assignee user ID
        state_id: Initial state ID
        project_id: Project ID
        label_ids: List of label IDs
        context: RailCall context (unused)
    
    Returns:
        Dict with created issue
    """
    team_id = _team_id_or_default(team_id)
    validate_non_empty(title, "title")
    if priority is not None:
        validate_priority(priority)
    if assignee_id:
        validate_user_id(assignee_id)
    if state_id:
        validate_state_id(state_id)
    if project_id:
        validate_project_id(project_id)
    if label_ids:
        for label_id in label_ids:
            validate_label_id(label_id)
    
    input_data: Dict[str, Any] = {
        "teamId": team_id,
        "title": title,
    }
    
    if description is not None:
        input_data["description"] = description
    if priority is not None:
        input_data["priority"] = priority
    if assignee_id:
        input_data["assigneeId"] = assignee_id
    if state_id:
        input_data["stateId"] = state_id
    if project_id:
        input_data["projectId"] = project_id
    if label_ids:
        input_data["labelIds"] = label_ids
    
    result = execute_query(CREATE_ISSUE, {"input": input_data})
    
    if not result.get("issueCreate", {}).get("success"):
        raise ValueError("Failed to create issue")
    
    return {"issue": result["issueCreate"]["issue"]}


def update_issue(
    issue_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[int] = None,
    assignee_id: Optional[str] = None,
    state_id: Optional[str] = None,
    label_ids: Optional[List[str]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Update an existing issue.
    
    Args:
        issue_id: Issue ID (required)
        title: New title
        description: New description
        priority: New priority
        assignee_id: New assignee ID
        state_id: New state ID
        label_ids: New label IDs
        context: RailCall context (unused)
    
    Returns:
        Dict with updated issue
    """
    validate_issue_id(issue_id)
    if title is not None:
        validate_non_empty(title, "title")
    if priority is not None:
        validate_priority(priority)
    if assignee_id:
        validate_user_id(assignee_id)
    if state_id:
        validate_state_id(state_id)
    if label_ids:
        for label_id in label_ids:
            validate_label_id(label_id)

    input_data: Dict[str, Any] = {}

    if title is not None:
        input_data["title"] = title
    if description is not None:
        input_data["description"] = description
    if priority is not None:
        input_data["priority"] = priority
    if assignee_id is not None:
        input_data["assigneeId"] = assignee_id
    if state_id is not None:
        input_data["stateId"] = state_id
    if label_ids is not None:
        input_data["labelIds"] = label_ids
    
    if not input_data:
        raise ValueError("No fields to update")
    
    result = execute_query(UPDATE_ISSUE, {"id": issue_id, "input": input_data})
    
    if not result.get("issueUpdate", {}).get("success"):
        raise ValueError("Failed to update issue")
    
    return {"issue": result["issueUpdate"]["issue"]}


def delete_issue(issue_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Delete an issue.
    
    Args:
        issue_id: Issue ID (required)
        context: RailCall context (unused)
    
    Returns:
        Dict with success status
    """
    validate_issue_id(issue_id)
    
    result = execute_query(DELETE_ISSUE, {"id": issue_id})
    
    if not result.get("issueDelete", {}).get("success"):
        raise ValueError("Failed to delete issue")
    
    return {"success": True, "deleted_issue_id": issue_id}


def search_issues(
    query: str,
    team_id: Optional[str] = None,
    include_comments: bool = True,
    limit: int = 50,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Full-text search across issues.

    Uses Linear's own search engine rather than a title filter, so descriptions
    and (by default) comments are searched too. `issueSearch` is deprecated;
    `searchIssues` is the live entry point.

    Args:
        query: Search term
        team_id: Optional team filter
        include_comments: Search comment bodies as well (default: True)
        limit: Maximum results (default: 50)
        context: RailCall context (unused)

    Returns:
        Dict with matching issues, the query, and Linear's total match count
    """
    if not query or not query.strip():
        raise ValueError("query cannot be empty")

    limit = validate_limit(limit, max_limit=250)

    variables: Dict[str, Any] = {
        "term": query,
        "includeComments": include_comments,
    }
    if team_id:
        team_id = _resolve_id(team_id, "team", context)
        validate_team_id(team_id)
        # searchIssues takes a team natively - no IssueFilter needed
        variables["teamId"] = team_id

    issues = paginate_query(
        query_func=_run_query,
        query=SEARCH_ISSUES,
        variables=variables,
        limit=limit,
        data_key="searchIssues",
    )

    return {
        "issues": issues,
        "count": len(issues),
        "query": query,
    }


def archive_issue(
    issue_id: str,
    trash: bool = False,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Archive an issue.

    The reversible counterpart to delete_issue, and what teams normally want:
    the issue leaves the active list but can be brought back with
    unarchive_issue.

    Args:
        issue_id: Issue ID (required)
        trash: Move to trash rather than archive (default: False)
        context: RailCall context (unused)

    Returns:
        Dict with success status
    """
    validate_issue_id(issue_id)

    result = execute_query(ARCHIVE_ISSUE, {"id": issue_id, "trash": trash})

    if not result.get("issueArchive", {}).get("success"):
        raise ValueError("Failed to archive issue")

    return {"success": True, "archived_issue_id": issue_id, "trashed": trash}


def unarchive_issue(
    issue_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Restore a previously archived issue.

    Args:
        issue_id: Issue ID (required)
        context: RailCall context (unused)

    Returns:
        Dict with success status
    """
    validate_issue_id(issue_id)

    result = execute_query(UNARCHIVE_ISSUE, {"id": issue_id})

    if not result.get("issueUnarchive", {}).get("success"):
        raise ValueError("Failed to unarchive issue")

    return {"success": True, "unarchived_issue_id": issue_id}


def bulk_update_issues(
    issue_ids: List[str],
    state_id: Optional[str] = None,
    assignee_id: Optional[str] = None,
    priority: Optional[int] = None,
    label_ids: Optional[List[str]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Update multiple issues at once.
    
    Args:
        issue_ids: List of issue IDs to update
        state_id: New state ID
        assignee_id: New assignee ID
        priority: New priority
        label_ids: New label IDs
        context: RailCall context (unused)
    
    Returns:
        Dict with update results
    """
    if not issue_ids:
        raise ValueError("issue_ids cannot be empty")
    
    for issue_id in issue_ids:
        validate_issue_id(issue_id)
    
    if priority is not None:
        validate_priority(priority)
    if assignee_id:
        validate_user_id(assignee_id)
    if state_id:
        validate_state_id(state_id)
    if label_ids:
        for label_id in label_ids:
            validate_label_id(label_id)
    
    input_data: Dict[str, Any] = {}
    if state_id is not None:
        input_data["stateId"] = state_id
    if assignee_id is not None:
        input_data["assigneeId"] = assignee_id
    if priority is not None:
        input_data["priority"] = priority
    if label_ids is not None:
        input_data["labelIds"] = label_ids
    
    if not input_data:
        raise ValueError("No fields to update")
    
    results: List[str] = []
    errors: List[Dict[str, Any]] = []

    for index, issue_id in enumerate(issue_ids):
        try:
            result = execute_query(UPDATE_ISSUE, {"id": issue_id, "input": input_data})
            if result.get("issueUpdate", {}).get("success"):
                results.append(issue_id)
            else:
                errors.append({"issue_id": issue_id, "error": "Update failed"})
        except RateLimitError as e:
            # The client already retried this one. Continuing at full speed would
            # burn the rest of the batch against the same closed window, so stop
            # and report exactly which IDs were never attempted.
            remaining = issue_ids[index:]
            errors.extend(
                {"issue_id": pending, "error": "Not attempted - rate limit reached"}
                for pending in remaining
            )
            return {
                "updated": results,
                "failed": errors,
                "success_count": len(results),
                "failure_count": len(errors),
                "rate_limited": True,
                "not_attempted": remaining,
                "message": (
                    f"Stopped after {len(results)} of {len(issue_ids)} updates: {e}. "
                    f"Re-run with the not_attempted IDs once the limit resets."
                ),
            }
        except AuthenticationError:
            raise  # credential problems must surface immediately
        except LinearError as e:
            errors.append({"issue_id": issue_id, "error": str(e)})
        except Exception as e:  # noqa: BLE001 - one bad ID must not abort the batch
            errors.append({"issue_id": issue_id, "error": str(e)})

    return {
        "updated": results,
        "failed": errors,
        "success_count": len(results),
        "failure_count": len(errors),
        "rate_limited": False,
    }


def link_issues(
    issue_id: str,
    related_issue_id: str,
    relationship_type: str = "blocks",
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Link two issues with a relationship.
    
    Args:
        issue_id: Source issue ID
        related_issue_id: Target issue ID
        relationship_type: Relationship type (blocks, blocked_by, related)
        context: RailCall context (unused)
    
    Returns:
        Dict with link status
    """
    validate_issue_id(issue_id)
    validate_issue_id(related_issue_id)

    if issue_id == related_issue_id:
        raise ValueError("Cannot link an issue to itself")

    if relationship_type not in ["blocks", "blocked_by", "related"]:
        raise ValueError("relationship_type must be 'blocks', 'blocked_by', or 'related'")

    # Linear models relations as first-class objects via issueRelationCreate, which
    # adds a link without touching the issue's existing relations. The IssueRelationType
    # enum has no "blocked_by" - it is expressed by inverting the two issues.
    if relationship_type == "blocked_by":
        source_id, target_id, relation_type = related_issue_id, issue_id, "blocks"
    else:
        source_id, target_id, relation_type = issue_id, related_issue_id, relationship_type

    input_data: Dict[str, Any] = {
        "issueId": source_id,
        "relatedIssueId": target_id,
        "type": relation_type,
    }

    result = execute_query(CREATE_ISSUE_RELATION, {"input": input_data})

    if not result.get("issueRelationCreate", {}).get("success"):
        raise ValueError("Failed to link issues")

    return {
        "success": True,
        "issue_id": issue_id,
        "related_issue_id": related_issue_id,
        "relationship": relationship_type,
        "relation": result["issueRelationCreate"].get("issueRelation"),
    }


# ============================================================================
# TEAM COMMANDS (2 commands)
# ============================================================================

@cached(ttl=METADATA_TTL)
def list_teams(limit: int = 50, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """List all teams in the workspace.
    
    Args:
        limit: Maximum number of results (default: 50)
        context: RailCall context (unused)
    
    Returns:
        Dict with teams list
    """
    limit = validate_limit(limit, max_limit=250)

    teams = paginate_query(
        query_func=_run_query,
        query=LIST_TEAMS,
        variables={},
        limit=limit,
        data_key="teams",
    )
    
    return {
        "teams": teams,
        "count": len(teams),
    }


@cached(ttl=METADATA_TTL)
def get_team(
    team_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Get detailed information about a specific team.
    
    Args:
        team_id: Team ID. Defaults to the team saved with the credential.
        context: RailCall context (unused)
    
    Returns:
        Dict with team details
    """
    team_id = _team_id_or_default(team_id)
    
    result = execute_query(GET_TEAM, {"id": team_id})
    
    if not result.get("team"):
        raise ValueError(f"Team not found: {team_id}")
    
    return {"team": result["team"]}


# ============================================================================
# PROJECT COMMANDS (4 commands)
# ============================================================================

@cached(ttl=METADATA_TTL)
def list_projects(limit: int = 50, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """List all projects in the workspace.
    
    Args:
        limit: Maximum number of results (default: 50)
        context: RailCall context (unused)
    
    Returns:
        Dict with projects list
    """
    limit = validate_limit(limit, max_limit=250)

    projects = paginate_query(
        query_func=_run_query,
        query=LIST_PROJECTS,
        variables={},
        limit=limit,
        data_key="projects",
    )
    
    return {
        "projects": projects,
        "count": len(projects),
    }


@cached(ttl=METADATA_TTL)
def get_project(project_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get detailed information about a specific project.
    
    Args:
        project_id: Project ID
        context: RailCall context (unused)
    
    Returns:
        Dict with project details
    """
    validate_project_id(project_id)
    
    result = execute_query(GET_PROJECT, {"id": project_id})
    
    if not result.get("project"):
        raise ValueError(f"Project not found: {project_id}")
    
    return {"project": result["project"]}


def create_project(
    team_ids: List[str],
    name: str,
    description: Optional[str] = None,
    lead_id: Optional[str] = None,
    start_date: Optional[str] = None,
    target_date: Optional[str] = None,
    priority: Optional[int] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a new project.

    Args:
        team_ids: Teams the project belongs to (required, at least one)
        name: Project name (required)
        description: Project description
        lead_id: User ID of the project lead
        start_date: Start date. Stored as a TimelessDate, so an ISO datetime is
            truncated to its date part (YYYY-MM-DD).
        target_date: Target date, same handling as start_date
        priority: Priority (0=none, 1=urgent, 2=high, 3=medium, 4=low)
        context: RailCall context (unused)

    Returns:
        Dict with created project
    """
    if not team_ids:
        raise ValueError("team_ids cannot be empty - a project needs at least one team")

    team_ids = _resolve_ids(team_ids, "team", context)
    for team_id in team_ids:
        validate_team_id(team_id)

    validate_non_empty(name, "name")

    if lead_id:
        lead_id = _resolve_id(lead_id, "user", context)
        validate_user_id(lead_id)
    if priority is not None:
        validate_priority(priority)

    input_data: Dict[str, Any] = {
        "teamIds": team_ids,
        "name": name,
    }

    if description is not None:
        input_data["description"] = description
    if lead_id:
        input_data["leadId"] = lead_id
    if start_date is not None:
        input_data["startDate"] = validate_timeless_date(start_date, "start_date")
    if target_date is not None:
        input_data["targetDate"] = validate_timeless_date(target_date, "target_date")
    if priority is not None:
        input_data["priority"] = priority

    result = execute_query(CREATE_PROJECT, {"input": input_data})

    if not result.get("projectCreate", {}).get("success"):
        raise ValueError("Failed to create project")

    invalidate_all("list_projects")

    return {"project": result["projectCreate"]["project"]}


def create_project_update(
    project_id: str,
    body: str,
    health: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Post a status update against a project.

    The project-level counterpart to create_initiative_update; Linear uses the
    same health vocabulary for both.

    Args:
        project_id: Project ID (required)
        body: Update text, markdown (required)
        health: onTrack, atRisk or offTrack
        context: RailCall context (unused)

    Returns:
        Dict with the created update
    """
    validate_project_id(project_id)
    validate_non_empty(body, "body")

    if health is not None and health not in HEALTH_STATES:
        raise ValueError("health must be one of: " + ", ".join(HEALTH_STATES))

    input_data: Dict[str, Any] = {
        "projectId": project_id,
        "body": body,
    }
    if health is not None:
        input_data["health"] = health

    result = execute_query(CREATE_PROJECT_UPDATE, {"input": input_data})

    if not result.get("projectUpdateCreate", {}).get("success"):
        raise ValueError("Failed to create project update")

    return {"update": result["projectUpdateCreate"]["projectUpdate"]}


# ============================================================================
# USER COMMANDS (2 commands)
# ============================================================================

@cached(ttl=METADATA_TTL)
def list_users(limit: int = 50, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """List all users in the workspace.
    
    Args:
        limit: Maximum number of results (default: 50)
        context: RailCall context (unused)
    
    Returns:
        Dict with users list
    """
    limit = validate_limit(limit, max_limit=250)

    users = paginate_query(
        query_func=_run_query,
        query=LIST_USERS,
        variables={},
        limit=limit,
        data_key="users",
    )
    
    return {
        "users": users,
        "count": len(users),
    }


@cached(ttl=METADATA_TTL)
def get_user(user_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get detailed information about a specific user.
    
    Args:
        user_id: User ID
        context: RailCall context (unused)
    
    Returns:
        Dict with user details
    """
    validate_user_id(user_id)
    
    result = execute_query(GET_USER, {"id": user_id})
    
    if not result.get("user"):
        raise ValueError(f"User not found: {user_id}")
    
    return {"user": result["user"]}


# ============================================================================
# STATE COMMANDS (3 commands)
# ============================================================================

@cached(ttl=METADATA_TTL)
def list_states(
    team_id: Optional[str] = None,
    limit: int = 50,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """List workflow states.
    
    Args:
        team_id: Optional team filter
        limit: Maximum number of results (default: 50)
        context: RailCall context (unused)
    
    Returns:
        Dict with states list
    """
    limit = validate_limit(limit, max_limit=250)

    state_filter: Dict[str, Any] = {}
    if team_id:
        team_id = _resolve_id(team_id, "team", context)
        validate_team_id(team_id)
        state_filter["team"] = {"id": {"eq": team_id}}

    states = paginate_query(
        query_func=_run_query,
        query=LIST_STATES,
        variables={"filter": state_filter} if state_filter else {},
        limit=limit,
        data_key="workflowStates",
    )

    return {
        "states": states,
        "count": len(states),
    }


def create_state(
    name: str,
    color: str,
    team_id: Optional[str] = None,
    state_type: str = "backlog",
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a new workflow state.
    
    Args:
        name: State name (required)
        color: Color hex code (required)
        team_id: Team ID. Defaults to the team saved with the credential.
        state_type: State type (backlog, unstarted, started, completed, canceled).
            Linear does not accept 'triage' here - triage is a per-team singleton
            enabled in team settings, not a state you create.
        context: RailCall context (unused)
    
    Returns:
        Dict with created state
    """
    team_id = _team_id_or_default(team_id)
    validate_non_empty(name, "name")
    validate_color(color)

    if state_type not in ["backlog", "unstarted", "started", "completed", "canceled"]:
        raise ValueError(
            "state_type must be one of: backlog, unstarted, started, completed, canceled. "
            "Linear rejects 'triage' - it is enabled in team settings, not created as a state."
        )
    
    input_data: Dict[str, Any] = {
        "teamId": team_id,
        "name": name,
        "color": color,
        "type": state_type,
    }
    
    result = execute_query(CREATE_STATE, {"input": input_data})
    
    if not result.get("workflowStateCreate", {}).get("success"):
        raise ValueError("Failed to create state")

    invalidate_all("list_states")

    return {"state": result["workflowStateCreate"]["workflowState"]}


def update_state(
    state_id: str,
    name: Optional[str] = None,
    color: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Update an existing workflow state.
    
    Args:
        state_id: State ID (required)
        name: New name
        color: New color
        context: RailCall context (unused)
    
    Returns:
        Dict with updated state
    """
    validate_state_id(state_id)
    if name is not None:
        validate_non_empty(name, "name")
    if color is not None:
        validate_color(color)

    input_data: Dict[str, Any] = {}
    if name is not None:
        input_data["name"] = name
    if color is not None:
        input_data["color"] = color
    
    if not input_data:
        raise ValueError("No fields to update")
    
    result = execute_query(UPDATE_STATE, {"id": state_id, "input": input_data})
    
    if not result.get("workflowStateUpdate", {}).get("success"):
        raise ValueError("Failed to update state")

    invalidate_all("list_states")

    return {"state": result["workflowStateUpdate"]["workflowState"]}


# ============================================================================
# LABEL COMMANDS (3 commands)
# ============================================================================

@cached(ttl=METADATA_TTL)
def list_labels(
    team_id: Optional[str] = None,
    limit: int = 50,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """List issue labels.
    
    Args:
        team_id: Optional team filter
        limit: Maximum number of results (default: 50)
        context: RailCall context (unused)
    
    Returns:
        Dict with labels list
    """
    limit = validate_limit(limit, max_limit=250)

    label_filter: Dict[str, Any] = {}
    if team_id:
        team_id = _resolve_id(team_id, "team", context)
        validate_team_id(team_id)
        label_filter["team"] = {"id": {"eq": team_id}}

    labels = paginate_query(
        query_func=_run_query,
        query=LIST_LABELS,
        variables={"filter": label_filter} if label_filter else {},
        limit=limit,
        data_key="issueLabels",
    )

    return {
        "labels": labels,
        "count": len(labels),
    }


def create_label(
    name: str,
    color: str,
    team_id: Optional[str] = None,
    description: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a new issue label.
    
    Args:
        name: Label name (required)
        color: Color hex code (required)
        team_id: Team ID. Defaults to the team saved with the credential.
        description: Label description
        context: RailCall context (unused)
    
    Returns:
        Dict with created label
    """
    team_id = _team_id_or_default(team_id)
    validate_non_empty(name, "name")
    validate_color(color)

    input_data: Dict[str, Any] = {
        "teamId": team_id,
        "name": name,
        "color": color,
    }
    
    if description is not None:
        input_data["description"] = description
    
    result = execute_query(CREATE_LABEL, {"input": input_data})
    
    if not result.get("issueLabelCreate", {}).get("success"):
        raise ValueError("Failed to create label")

    invalidate_all("list_labels")

    return {"label": result["issueLabelCreate"]["issueLabel"]}


def update_label(
    label_id: str,
    name: Optional[str] = None,
    color: Optional[str] = None,
    description: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Update an existing issue label.
    
    Args:
        label_id: Label ID (required)
        name: New name
        color: New color
        description: New description
        context: RailCall context (unused)
    
    Returns:
        Dict with updated label
    """
    validate_label_id(label_id)
    if name is not None:
        validate_non_empty(name, "name")
    if color is not None:
        validate_color(color)

    input_data: Dict[str, Any] = {}
    if name is not None:
        input_data["name"] = name
    if color is not None:
        input_data["color"] = color
    if description is not None:
        input_data["description"] = description
    
    if not input_data:
        raise ValueError("No fields to update")
    
    result = execute_query(UPDATE_LABEL, {"id": label_id, "input": input_data})
    
    if not result.get("issueLabelUpdate", {}).get("success"):
        raise ValueError("Failed to update label")

    invalidate_all("list_labels")

    return {"label": result["issueLabelUpdate"]["issueLabel"]}


# ============================================================================
# CYCLE COMMANDS (4 commands)
# ============================================================================

def list_cycles(
    team_id: Optional[str] = None,
    limit: int = 50,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """List cycles for a team.
    
    Args:
        team_id: Team ID. Defaults to the team saved with the credential.
        limit: Maximum number of results (default: 50)
        context: RailCall context (unused)
    
    Returns:
        Dict with cycles list
    """
    team_id = _team_id_or_default(team_id)
    limit = validate_limit(limit, max_limit=250)

    cycles = paginate_query(
        query_func=_run_query,
        query=LIST_CYCLES,
        variables={"filter": {"team": {"id": {"eq": team_id}}}},
        limit=limit,
        data_key="cycles",
    )

    return {
        "cycles": cycles,
        "count": len(cycles),
    }


def get_cycle(cycle_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get detailed information about a specific cycle.
    
    Args:
        cycle_id: Cycle ID
        context: RailCall context (unused)
    
    Returns:
        Dict with cycle details
    """
    validate_cycle_id(cycle_id)
    
    result = execute_query(GET_CYCLE, {"id": cycle_id})
    
    if not result.get("cycle"):
        raise ValueError(f"Cycle not found: {cycle_id}")
    
    return {"cycle": result["cycle"]}


def create_cycle(
    starts_at: str,
    ends_at: str,
    team_id: Optional[str] = None,
    name: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a new cycle.
    
    Args:
        starts_at: Start date (ISO 8601)
        ends_at: End date (ISO 8601)
        team_id: Team ID. Defaults to the team saved with the credential.
        name: Cycle name
        context: RailCall context (unused)
    
    Returns:
        Dict with created cycle
    """
    team_id = _team_id_or_default(team_id)
    validate_iso_date(starts_at, "starts_at")
    validate_iso_date(ends_at, "ends_at")
    if starts_at >= ends_at:
        raise ValueError("starts_at must be earlier than ends_at")

    input_data: Dict[str, Any] = {
        "teamId": team_id,
        "startsAt": starts_at,
        "endsAt": ends_at,
    }
    
    if name is not None:
        input_data["name"] = name
    
    result = execute_query(CREATE_CYCLE, {"input": input_data})
    
    if not result.get("cycleCreate", {}).get("success"):
        raise ValueError("Failed to create cycle")
    
    return {"cycle": result["cycleCreate"]["cycle"]}


def update_cycle(
    cycle_id: str,
    name: Optional[str] = None,
    starts_at: Optional[str] = None,
    ends_at: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Update an existing cycle.
    
    Args:
        cycle_id: Cycle ID (required)
        name: New name
        starts_at: New start date
        ends_at: New end date
        context: RailCall context (unused)
    
    Returns:
        Dict with updated cycle
    """
    validate_cycle_id(cycle_id)
    if name is not None:
        validate_non_empty(name, "name")
    if starts_at is not None:
        validate_iso_date(starts_at, "starts_at")
    if ends_at is not None:
        validate_iso_date(ends_at, "ends_at")
    if starts_at is not None and ends_at is not None and starts_at >= ends_at:
        raise ValueError("starts_at must be earlier than ends_at")

    input_data: Dict[str, Any] = {}
    if name is not None:
        input_data["name"] = name
    if starts_at is not None:
        input_data["startsAt"] = starts_at
    if ends_at is not None:
        input_data["endsAt"] = ends_at
    
    if not input_data:
        raise ValueError("No fields to update")
    
    result = execute_query(UPDATE_CYCLE, {"id": cycle_id, "input": input_data})
    
    if not result.get("cycleUpdate", {}).get("success"):
        raise ValueError("Failed to update cycle")
    
    return {"cycle": result["cycleUpdate"]["cycle"]}


# ============================================================================
# COMMENT COMMANDS (4 commands)
# ============================================================================

def list_comments(
    issue_id: str,
    limit: int = 50,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """List comments for an issue.
    
    Args:
        issue_id: Issue ID (required)
        limit: Maximum number of results (default: 50)
        context: RailCall context (unused)
    
    Returns:
        Dict with comments list
    """
    validate_issue_id(issue_id)
    limit = validate_limit(limit, max_limit=250)

    comments = paginate_query(
        query_func=_run_query,
        query=LIST_COMMENTS,
        variables={"filter": {"issue": {"id": {"eq": issue_id}}}},
        limit=limit,
        data_key="comments",
    )
    
    return {
        "comments": comments,
        "count": len(comments),
    }


def create_comment(
    issue_id: str,
    body: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a new comment on an issue.
    
    Args:
        issue_id: Issue ID (required)
        body: Comment body (markdown)
        context: RailCall context (unused)
    
    Returns:
        Dict with created comment
    """
    validate_issue_id(issue_id)
    validate_non_empty(body, "body")

    input_data: Dict[str, Any] = {
        "issueId": issue_id,
        "body": body,
    }
    
    result = execute_query(CREATE_COMMENT, {"input": input_data})
    
    if not result.get("commentCreate", {}).get("success"):
        raise ValueError("Failed to create comment")
    
    return {"comment": result["commentCreate"]["comment"]}


def update_comment(
    comment_id: str,
    body: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Update an existing comment.
    
    Args:
        comment_id: Comment ID (required)
        body: New comment body
        context: RailCall context (unused)
    
    Returns:
        Dict with updated comment
    """
    validate_comment_id(comment_id)
    validate_non_empty(body, "body")

    input_data = {"body": body}

    result = execute_query(UPDATE_COMMENT, {"id": comment_id, "input": input_data})
    
    if not result.get("commentUpdate", {}).get("success"):
        raise ValueError("Failed to update comment")
    
    return {"comment": result["commentUpdate"]["comment"]}


def delete_comment(
    comment_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Delete a comment.
    
    Args:
        comment_id: Comment ID (required)
        context: RailCall context (unused)
    
    Returns:
        Dict with success status
    """
    validate_comment_id(comment_id)

    result = execute_query(DELETE_COMMENT, {"id": comment_id})
    
    if not result.get("commentDelete", {}).get("success"):
        raise ValueError("Failed to delete comment")
    
    return {"success": True, "deleted_comment_id": comment_id}


# ============================================================================
# WEBHOOK COMMANDS (4 commands)
# ============================================================================

def list_webhooks(limit: int = 50, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """List all webhooks.
    
    Args:
        limit: Maximum number of results (default: 50)
        context: RailCall context (unused)
    
    Returns:
        Dict with webhooks list
    """
    limit = validate_limit(limit, max_limit=250)

    webhooks = paginate_query(
        query_func=_run_query,
        query=LIST_WEBHOOKS,
        variables={},
        limit=limit,
        data_key="webhooks",
    )
    
    return {
        "webhooks": webhooks,
        "count": len(webhooks),
    }


def create_webhook(
    url: str,
    resource_types: Optional[List[str]] = None,
    enabled: bool = True,
    label: Optional[str] = None,
    team_id: Optional[str] = None,
    all_public_teams: bool = False,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a new webhook.

    Args:
        url: Webhook URL (required)
        resource_types: Resources to subscribe to (required by Linear).
            Defaults to ["Issue", "Comment"]. Other values include IssueLabel,
            Project, ProjectUpdate, Cycle, Reaction, Document, Initiative.
        enabled: Whether webhook is enabled (default: True)
        label: Optional human-readable name shown in Linear settings
        team_id: Scope the webhook to a single team
        all_public_teams: Subscribe to every public team instead of one team.
            Linear requires exactly one of team_id or all_public_teams.
        context: RailCall context (unused)

    Returns:
        Dict with created webhook
    """
    validate_url(url)

    if resource_types is None:
        resource_types = ["Issue", "Comment"]
    validate_resource_types(resource_types)

    if team_id:
        team_id = _resolve_id(team_id, "team", context)
        validate_team_id(team_id)

    # Linear requires a scope and offers no default: a webhook is either bound to
    # one team or to all public teams.
    if bool(team_id) == all_public_teams:
        raise ValueError(
            "Provide exactly one of team_id or all_public_teams=True - "
            "Linear needs to know which teams the webhook covers."
        )

    input_data: Dict[str, Any] = {
        "url": url,
        "resourceTypes": resource_types,
        "enabled": enabled,
    }

    if label is not None:
        validate_non_empty(label, "label")
        input_data["label"] = label
    if team_id:
        input_data["teamId"] = team_id
    if all_public_teams:
        input_data["allPublicTeams"] = True
    
    result = execute_query(CREATE_WEBHOOK, {"input": input_data})
    
    if not result.get("webhookCreate", {}).get("success"):
        raise ValueError("Failed to create webhook")
    
    return {"webhook": result["webhookCreate"]["webhook"]}


def update_webhook(
    webhook_id: str,
    url: Optional[str] = None,
    enabled: Optional[bool] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Update an existing webhook.
    
    Args:
        webhook_id: Webhook ID (required)
        url: New URL
        enabled: New enabled status
        context: RailCall context (unused)
    
    Returns:
        Dict with updated webhook
    """
    validate_webhook_id(webhook_id)
    
    input_data: Dict[str, Any] = {}
    if url is not None:
        validate_url(url)
        input_data["url"] = url
    if enabled is not None:
        input_data["enabled"] = enabled
    
    if not input_data:
        raise ValueError("No fields to update")
    
    result = execute_query(UPDATE_WEBHOOK, {"id": webhook_id, "input": input_data})
    
    if not result.get("webhookUpdate", {}).get("success"):
        raise ValueError("Failed to update webhook")
    
    return {"webhook": result["webhookUpdate"]["webhook"]}


def delete_webhook(
    webhook_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Delete a webhook.
    
    Args:
        webhook_id: Webhook ID (required)
        context: RailCall context (unused)
    
    Returns:
        Dict with success status
    """
    validate_webhook_id(webhook_id)
    
    result = execute_query(DELETE_WEBHOOK, {"id": webhook_id})
    
    if not result.get("webhookDelete", {}).get("success"):
        raise ValueError("Failed to delete webhook")
    
    return {"success": True, "deleted_webhook_id": webhook_id}


# ============================================================================
# MILESTONE COMMANDS (3 commands)
# ============================================================================

def list_milestones(
    project_id: Optional[str] = None,
    limit: int = 50,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """List project milestones.

    Linear has no workspace-wide milestone concept - every milestone belongs to
    a project. Omit project_id to list milestones across all projects.

    Args:
        project_id: Optional project filter
        limit: Maximum number of results (default: 50)
        context: RailCall context (unused)

    Returns:
        Dict with milestones list
    """
    limit = validate_limit(limit, max_limit=250)

    milestone_filter: Dict[str, Any] = {}
    if project_id:
        validate_project_id(project_id)
        milestone_filter["project"] = {"id": {"eq": project_id}}

    milestones = paginate_query(
        query_func=_run_query,
        query=LIST_MILESTONES,
        variables={"filter": milestone_filter} if milestone_filter else {},
        limit=limit,
        data_key="projectMilestones",
    )

    return {
        "milestones": milestones,
        "count": len(milestones),
    }


def create_milestone(
    project_id: str,
    name: str,
    target_date: Optional[str] = None,
    description: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a new project milestone.

    Args:
        project_id: Project the milestone belongs to (required by Linear)
        name: Milestone name (required)
        target_date: Target date. Linear stores this as a TimelessDate, so an
            ISO datetime is truncated to its date part (YYYY-MM-DD).
        description: Milestone description
        context: RailCall context (unused)

    Returns:
        Dict with created milestone
    """
    validate_project_id(project_id)
    validate_non_empty(name, "name")

    input_data: Dict[str, Any] = {
        "projectId": project_id,
        "name": name,
    }

    if target_date is not None:
        input_data["targetDate"] = validate_timeless_date(target_date, "target_date")
    if description is not None:
        input_data["description"] = description

    result = execute_query(CREATE_MILESTONE, {"input": input_data})

    if not result.get("projectMilestoneCreate", {}).get("success"):
        raise ValueError("Failed to create milestone")

    return {"milestone": result["projectMilestoneCreate"]["projectMilestone"]}


def update_milestone(
    milestone_id: str,
    name: Optional[str] = None,
    target_date: Optional[str] = None,
    description: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Update an existing project milestone.

    Args:
        milestone_id: Milestone ID (required)
        name: New name
        target_date: New target date (truncated to YYYY-MM-DD)
        description: New description
        context: RailCall context (unused)

    Returns:
        Dict with updated milestone
    """
    validate_milestone_id(milestone_id)
    if name is not None:
        validate_non_empty(name, "name")

    input_data: Dict[str, Any] = {}
    if name is not None:
        input_data["name"] = name
    if target_date is not None:
        input_data["targetDate"] = validate_timeless_date(target_date, "target_date")
    if description is not None:
        input_data["description"] = description

    if not input_data:
        raise ValueError("No fields to update")

    result = execute_query(UPDATE_MILESTONE, {"id": milestone_id, "input": input_data})

    if not result.get("projectMilestoneUpdate", {}).get("success"):
        raise ValueError("Failed to update milestone")

    return {"milestone": result["projectMilestoneUpdate"]["projectMilestone"]}


# ============================================================================
# INITIATIVE COMMANDS (6 commands)
# ============================================================================
# Linear renamed Roadmaps to Initiatives - there is no `roadmap` in the schema.
# An initiative groups projects under one goal, carries a status, and collects
# health updates over time.

INITIATIVE_STATUSES = ["Proposed", "Planned", "Active", "Completed", "Canceled"]
# Linear uses the same health vocabulary for initiative and project updates.
HEALTH_STATES = ["onTrack", "atRisk", "offTrack"]


def list_initiatives(
    status: Optional[str] = None,
    limit: int = 50,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """List initiatives (Linear's roadmap objects).

    Args:
        status: Optional status filter (Proposed, Planned, Active, Completed, Canceled)
        limit: Maximum number of results (default: 50)
        context: RailCall context (unused)

    Returns:
        Dict with initiatives list
    """
    limit = validate_limit(limit, max_limit=250)

    initiative_filter: Dict[str, Any] = {}
    if status:
        if status not in INITIATIVE_STATUSES:
            raise ValueError(
                "status must be one of: " + ", ".join(INITIATIVE_STATUSES)
            )
        initiative_filter["status"] = {"eq": status}

    initiatives = paginate_query(
        query_func=_run_query,
        query=LIST_INITIATIVES,
        variables={"filter": initiative_filter} if initiative_filter else {},
        limit=limit,
        data_key="initiatives",
    )

    return {
        "initiatives": initiatives,
        "count": len(initiatives),
    }


def get_initiative(
    initiative_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Get one initiative, including the projects rolled up under it.

    Args:
        initiative_id: Initiative ID
        context: RailCall context (unused)

    Returns:
        Dict with initiative details
    """
    validate_initiative_id(initiative_id)

    result = execute_query(GET_INITIATIVE, {"id": initiative_id})

    if not result.get("initiative"):
        raise ValueError(f"Initiative not found: {initiative_id}")

    return {"initiative": result["initiative"]}


def create_initiative(
    name: str,
    description: Optional[str] = None,
    target_date: Optional[str] = None,
    status: Optional[str] = None,
    owner_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a new initiative.

    Args:
        name: Initiative name (required)
        description: Initiative description
        target_date: Target date. Stored as a TimelessDate, so an ISO datetime
            is truncated to its date part (YYYY-MM-DD).
        status: Proposed, Planned, Active, Completed or Canceled
        owner_id: User ID of the initiative owner
        context: RailCall context (unused)

    Returns:
        Dict with created initiative
    """
    validate_non_empty(name, "name")

    if status is not None and status not in INITIATIVE_STATUSES:
        raise ValueError("status must be one of: " + ", ".join(INITIATIVE_STATUSES))
    if owner_id:
        validate_user_id(owner_id)

    input_data: Dict[str, Any] = {"name": name}

    if description is not None:
        input_data["description"] = description
    if target_date is not None:
        input_data["targetDate"] = validate_timeless_date(target_date, "target_date")
    if status is not None:
        input_data["status"] = status
    if owner_id:
        input_data["ownerId"] = owner_id

    result = execute_query(CREATE_INITIATIVE, {"input": input_data})

    if not result.get("initiativeCreate", {}).get("success"):
        raise ValueError("Failed to create initiative")

    return {"initiative": result["initiativeCreate"]["initiative"]}


def update_initiative(
    initiative_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    target_date: Optional[str] = None,
    status: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Update an existing initiative.

    Args:
        initiative_id: Initiative ID (required)
        name: New name
        description: New description
        target_date: New target date (truncated to YYYY-MM-DD)
        status: New status
        context: RailCall context (unused)

    Returns:
        Dict with updated initiative
    """
    validate_initiative_id(initiative_id)

    if name is not None:
        validate_non_empty(name, "name")
    if status is not None and status not in INITIATIVE_STATUSES:
        raise ValueError("status must be one of: " + ", ".join(INITIATIVE_STATUSES))

    input_data: Dict[str, Any] = {}
    if name is not None:
        input_data["name"] = name
    if description is not None:
        input_data["description"] = description
    if target_date is not None:
        input_data["targetDate"] = validate_timeless_date(target_date, "target_date")
    if status is not None:
        input_data["status"] = status

    if not input_data:
        raise ValueError("No fields to update")

    result = execute_query(
        UPDATE_INITIATIVE, {"id": initiative_id, "input": input_data}
    )

    if not result.get("initiativeUpdate", {}).get("success"):
        raise ValueError("Failed to update initiative")

    return {"initiative": result["initiativeUpdate"]["initiative"]}


def link_project_to_initiative(
    initiative_id: str,
    project_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Roll a project up under an initiative.

    This is what makes an initiative a roadmap rather than a label: the projects
    attached to it are the work it tracks.

    Args:
        initiative_id: Initiative ID (required)
        project_id: Project ID (required)
        context: RailCall context (unused)

    Returns:
        Dict with the created link
    """
    validate_initiative_id(initiative_id)
    validate_project_id(project_id)

    input_data: Dict[str, Any] = {
        "initiativeId": initiative_id,
        "projectId": project_id,
    }

    result = execute_query(LINK_PROJECT_TO_INITIATIVE, {"input": input_data})

    if not result.get("initiativeToProjectCreate", {}).get("success"):
        raise ValueError("Failed to link project to initiative")

    return {
        "success": True,
        "initiative_id": initiative_id,
        "project_id": project_id,
        "link": result["initiativeToProjectCreate"].get("initiativeToProject"),
    }


def create_initiative_update(
    initiative_id: str,
    body: str,
    health: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Post a status update against an initiative.

    Args:
        initiative_id: Initiative ID (required)
        body: Update text, markdown (required)
        health: onTrack, atRisk or offTrack
        context: RailCall context (unused)

    Returns:
        Dict with the created update
    """
    validate_initiative_id(initiative_id)
    validate_non_empty(body, "body")

    if health is not None and health not in HEALTH_STATES:
        raise ValueError("health must be one of: " + ", ".join(HEALTH_STATES))

    input_data: Dict[str, Any] = {
        "initiativeId": initiative_id,
        "body": body,
    }
    if health is not None:
        input_data["health"] = health

    result = execute_query(CREATE_INITIATIVE_UPDATE, {"input": input_data})

    if not result.get("initiativeUpdateCreate", {}).get("success"):
        raise ValueError("Failed to create initiative update")

    return {"update": result["initiativeUpdateCreate"]["initiativeUpdate"]}
