"""RailCall Linear Module - Production Grade

A comprehensive Linear integration for RailCall with 30 commands covering:
- Issue management (create, update, delete, list, get, search, bulk_update, link)
- Team management (list, get, create, update)
- Project management (list, get, create, update)
- User management (list, get)
- Workflow states (list, create, update)
- Labels (list, create, update)
- Cycles (list, get, create, update)
- Comments (list, create, update, delete)
- Webhooks (list, create, update, delete)
- Milestones (list, create, update)

All commands support:
- Automatic retry with exponential backoff
- Rate limiting protection
- Input validation
- Caching (Redis or memory)
- Comprehensive error handling
"""

from typing import Any, Dict, List, Optional

from .client import execute_query
from .queries import *
from .utils import (
    validate_issue_id,
    validate_team_id,
    validate_project_id,
    validate_user_id,
    validate_state_id,
    validate_label_id,
    validate_cycle_id,
    validate_priority,
    validate_limit,
    paginate_query,
)


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
        validate_team_id(team_id)
        issue_filter["team"] = {"id": {"eq": team_id}}
    if state_id:
        validate_state_id(state_id)
        issue_filter["state"] = {"id": {"eq": state_id}}
    if assignee_id:
        validate_user_id(assignee_id)
        issue_filter["assignee"] = {"id": {"eq": assignee_id}}

    def query_func(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        return execute_query(query, variables)

    issues = paginate_query(
        query_func=query_func,
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
    team_id: str,
    title: str,
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
        team_id: Team ID (required)
        title: Issue title (required)
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
    validate_team_id(team_id)
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
    
    input_data = {
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
    if priority is not None:
        validate_priority(priority)
    if assignee_id:
        validate_user_id(assignee_id)
    if state_id:
        validate_state_id(state_id)
    if label_ids:
        for label_id in label_ids:
            validate_label_id(label_id)
    
    input_data = {}
    
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
    limit: int = 50,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Search issues by text query.
    
    Args:
        query: Search query string
        team_id: Optional team filter
        limit: Maximum results (default: 50)
        context: RailCall context (unused)
    
    Returns:
        Dict with matching issues
    """
    if not query or not query.strip():
        raise ValueError("query cannot be empty")

    limit = validate_limit(limit, max_limit=250)
    if team_id:
        validate_team_id(team_id)

    # Search text travels as a variable value, so it is never parsed as GraphQL
    issue_filter: Dict[str, Any] = {"title": {"containsIgnoreCase": query}}
    if team_id:
        issue_filter["team"] = {"id": {"eq": team_id}}

    variables = {"filter": issue_filter, "first": limit}
    result = execute_query(LIST_ISSUES, variables)

    # Extract issues from the result
    issues = result.get("issues", {}).get("nodes", [])

    return {
        "issues": issues,
        "count": len(issues),
        "query": query,
    }


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
    
    input_data = {}
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
    
    results = []
    errors = []
    
    for issue_id in issue_ids:
        try:
            result = execute_query(UPDATE_ISSUE, {"id": issue_id, "input": input_data})
            if result.get("issueUpdate", {}).get("success"):
                results.append(issue_id)
            else:
                errors.append({"issue_id": issue_id, "error": "Update failed"})
        except Exception as e:
            errors.append({"issue_id": issue_id, "error": str(e)})
    
    return {
        "updated": results,
        "failed": errors,
        "success_count": len(results),
        "failure_count": len(errors),
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

    input_data = {
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

def list_teams(limit: int = 50, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """List all teams in the workspace.
    
    Args:
        limit: Maximum number of results (default: 50)
        context: RailCall context (unused)
    
    Returns:
        Dict with teams list
    """
    validate_limit(limit, max_limit=250)
    
    def query_func(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        return execute_query(query, variables)
    
    teams = paginate_query(
        query_func=query_func,
        query=LIST_TEAMS,
        variables={},
        limit=limit,
        data_key="teams",
    )
    
    return {
        "teams": teams,
        "count": len(teams),
    }


def get_team(team_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get detailed information about a specific team.
    
    Args:
        team_id: Team ID
        context: RailCall context (unused)
    
    Returns:
        Dict with team details
    """
    validate_team_id(team_id)
    
    result = execute_query(GET_TEAM, {"id": team_id})
    
    if not result.get("team"):
        raise ValueError(f"Team not found: {team_id}")
    
    return {"team": result["team"]}


# ============================================================================
# PROJECT COMMANDS (2 commands)
# ============================================================================

def list_projects(limit: int = 50, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """List all projects in the workspace.
    
    Args:
        limit: Maximum number of results (default: 50)
        context: RailCall context (unused)
    
    Returns:
        Dict with projects list
    """
    validate_limit(limit, max_limit=250)
    
    def query_func(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        return execute_query(query, variables)
    
    projects = paginate_query(
        query_func=query_func,
        query=LIST_PROJECTS,
        variables={},
        limit=limit,
        data_key="projects",
    )
    
    return {
        "projects": projects,
        "count": len(projects),
    }


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


# ============================================================================
# USER COMMANDS (2 commands)
# ============================================================================

def list_users(limit: int = 50, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """List all users in the workspace.
    
    Args:
        limit: Maximum number of results (default: 50)
        context: RailCall context (unused)
    
    Returns:
        Dict with users list
    """
    validate_limit(limit, max_limit=250)
    
    def query_func(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        return execute_query(query, variables)
    
    users = paginate_query(
        query_func=query_func,
        query=LIST_USERS,
        variables={},
        limit=limit,
        data_key="users",
    )
    
    return {
        "users": users,
        "count": len(users),
    }


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
        validate_team_id(team_id)
        state_filter["team"] = {"id": {"eq": team_id}}

    def query_func(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        return execute_query(query, variables)

    states = paginate_query(
        query_func=query_func,
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
    team_id: str,
    name: str,
    color: str,
    state_type: str = "triage",
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a new workflow state.
    
    Args:
        team_id: Team ID (required)
        name: State name (required)
        color: Color hex code (required)
        state_type: State type (triage, backlog, unstarted, started, completed, canceled)
        context: RailCall context (unused)
    
    Returns:
        Dict with created state
    """
    validate_team_id(team_id)
    
    if state_type not in ["triage", "backlog", "unstarted", "started", "completed", "canceled"]:
        raise ValueError("state_type must be one of: triage, backlog, unstarted, started, completed, canceled")
    
    input_data = {
        "teamId": team_id,
        "name": name,
        "color": color,
        "type": state_type,
    }
    
    result = execute_query(CREATE_STATE, {"input": input_data})
    
    if not result.get("workflowStateCreate", {}).get("success"):
        raise ValueError("Failed to create state")
    
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
    
    input_data = {}
    if name is not None:
        input_data["name"] = name
    if color is not None:
        input_data["color"] = color
    
    if not input_data:
        raise ValueError("No fields to update")
    
    result = execute_query(UPDATE_STATE, {"id": state_id, "input": input_data})
    
    if not result.get("workflowStateUpdate", {}).get("success"):
        raise ValueError("Failed to update state")
    
    return {"state": result["workflowStateUpdate"]["workflowState"]}


# ============================================================================
# LABEL COMMANDS (3 commands)
# ============================================================================

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
        validate_team_id(team_id)
        label_filter["team"] = {"id": {"eq": team_id}}

    def query_func(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        return execute_query(query, variables)

    labels = paginate_query(
        query_func=query_func,
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
    team_id: str,
    name: str,
    color: str,
    description: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a new issue label.
    
    Args:
        team_id: Team ID (required)
        name: Label name (required)
        color: Color hex code (required)
        description: Label description
        context: RailCall context (unused)
    
    Returns:
        Dict with created label
    """
    validate_team_id(team_id)
    
    input_data = {
        "teamId": team_id,
        "name": name,
        "color": color,
    }
    
    if description is not None:
        input_data["description"] = description
    
    result = execute_query(CREATE_LABEL, {"input": input_data})
    
    if not result.get("issueLabelCreate", {}).get("success"):
        raise ValueError("Failed to create label")
    
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
    
    input_data = {}
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
    
    return {"label": result["issueLabelUpdate"]["issueLabel"]}


# ============================================================================
# CYCLE COMMANDS (4 commands)
# ============================================================================

def list_cycles(
    team_id: str,
    limit: int = 50,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """List cycles for a team.
    
    Args:
        team_id: Team ID (required)
        limit: Maximum number of results (default: 50)
        context: RailCall context (unused)
    
    Returns:
        Dict with cycles list
    """
    validate_team_id(team_id)
    limit = validate_limit(limit, max_limit=250)

    def query_func(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        return execute_query(query, variables)

    cycles = paginate_query(
        query_func=query_func,
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
    team_id: str,
    starts_at: str,
    ends_at: str,
    name: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a new cycle.
    
    Args:
        team_id: Team ID (required)
        starts_at: Start date (ISO 8601)
        ends_at: End date (ISO 8601)
        name: Cycle name
        context: RailCall context (unused)
    
    Returns:
        Dict with created cycle
    """
    validate_team_id(team_id)
    
    input_data = {
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
    
    input_data = {}
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
    validate_limit(limit, max_limit=250)
    
    def query_func(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        return execute_query(query, variables)
    
    comments = paginate_query(
        query_func=query_func,
        query=LIST_COMMENTS,
        variables={"issueId": issue_id},
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
    
    input_data = {
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
    validate_limit(limit, max_limit=250)
    
    def query_func(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        return execute_query(query, variables)
    
    webhooks = paginate_query(
        query_func=query_func,
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
    enabled: bool = True,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a new webhook.
    
    Args:
        url: Webhook URL (required)
        enabled: Whether webhook is enabled (default: True)
        context: RailCall context (unused)
    
    Returns:
        Dict with created webhook
    """
    from .utils import validate_url
    validate_url(url)
    
    input_data = {
        "url": url,
        "enabled": enabled,
    }
    
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
    from .utils import validate_webhook_id, validate_url
    validate_webhook_id(webhook_id)
    
    input_data = {}
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
    from .utils import validate_webhook_id
    validate_webhook_id(webhook_id)
    
    result = execute_query(DELETE_WEBHOOK, {"id": webhook_id})
    
    if not result.get("webhookDelete", {}).get("success"):
        raise ValueError("Failed to delete webhook")
    
    return {"success": True, "deleted_webhook_id": webhook_id}


# ============================================================================
# MILESTONE COMMANDS (3 commands)
# ============================================================================

def list_milestones(limit: int = 50, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """List all milestones.
    
    Args:
        limit: Maximum number of results (default: 50)
        context: RailCall context (unused)
    
    Returns:
        Dict with milestones list
    """
    validate_limit(limit, max_limit=250)
    
    def query_func(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        return execute_query(query, variables)
    
    milestones = paginate_query(
        query_func=query_func,
        query=LIST_MILESTONES,
        variables={},
        limit=limit,
        data_key="milestones",
    )
    
    return {
        "milestones": milestones,
        "count": len(milestones),
    }


def create_milestone(
    name: str,
    target_date: str,
    description: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a new milestone.
    
    Args:
        name: Milestone name (required)
        target_date: Target date (ISO 8601)
        description: Milestone description
        context: RailCall context (unused)
    
    Returns:
        Dict with created milestone
    """
    input_data = {
        "name": name,
        "targetDate": target_date,
    }
    
    if description is not None:
        input_data["description"] = description
    
    result = execute_query(CREATE_MILESTONE, {"input": input_data})
    
    if not result.get("milestoneCreate", {}).get("success"):
        raise ValueError("Failed to create milestone")
    
    return {"milestone": result["milestoneCreate"]["milestone"]}


def update_milestone(
    milestone_id: str,
    name: Optional[str] = None,
    target_date: Optional[str] = None,
    description: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Update an existing milestone.
    
    Args:
        milestone_id: Milestone ID (required)
        name: New name
        target_date: New target date
        description: New description
        context: RailCall context (unused)
    
    Returns:
        Dict with updated milestone
    """
    from .utils import validate_milestone_id
    validate_milestone_id(milestone_id)
    
    input_data = {}
    if name is not None:
        input_data["name"] = name
    if target_date is not None:
        input_data["targetDate"] = target_date
    if description is not None:
        input_data["description"] = description
    
    if not input_data:
        raise ValueError("No fields to update")
    
    result = execute_query(UPDATE_MILESTONE, {"id": milestone_id, "input": input_data})
    
    if not result.get("milestoneUpdate", {}).get("success"):
        raise ValueError("Failed to update milestone")
    
    return {"milestone": result["milestoneUpdate"]["milestone"]}
