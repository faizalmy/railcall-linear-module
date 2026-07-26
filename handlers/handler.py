"""Handlers for the agentstack/linear module.

Every command declared in module.json must have a matching top-level
function here. The function's return value becomes the receipt payload.

Linear API docs: https://developers.linear.app/docs/graphql
"""

import os
import time
import requests


# Linear GraphQL endpoint
LINEAR_API_URL = "https://api.linear.app/graphql"


def _get_api_key() -> str:
    """Read API key from environment. Raises clear error if missing."""
    api_key = os.environ.get("LINEAR_API_KEY")
    if not api_key:
        raise ValueError("LINEAR_API_KEY environment variable not set. Get your key from Linear → Settings → API → Create key.")
    return api_key


def _make_request(query: str, variables: dict = None) -> dict:
    """Make GraphQL request to Linear with retry logic.
    
    Args:
        query: GraphQL query or mutation string
        variables: Optional variables dict for parameterized queries
    
    Returns:
        Response data dict (the "data" field from GraphQL response)
    
    Raises:
        ValueError: On API errors, auth failures, or rate limits
    """
    api_key = _get_api_key()
    
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    # Retry logic for rate limits (Linear: 50 req/10s per API key)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(
                LINEAR_API_URL,
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
            result = response.json()
            
            # Check for GraphQL errors
            if "errors" in result:
                error = result["errors"][0]
                message = error.get("message", "Unknown error")
                
                # Map Linear error codes to actionable messages
                if "not found" in message.lower():
                    raise ValueError(f"Resource not found: {message}")
                elif "unauthorized" in message.lower() or "authentication" in message.lower():
                    raise ValueError("Invalid API key or insufficient permissions")
                elif "rate limit" in message.lower():
                    raise ValueError("Rate limit exceeded. Wait 10 seconds and retry.")
                else:
                    raise ValueError(f"Linear API error: {message}")
            
            return result.get("data", {})
            
        except requests.exceptions.Timeout:
            raise ValueError("Request timed out after 30 seconds")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Network error: {str(e)}")
    
    raise ValueError("Rate limit exceeded after 3 retries. Try again later.")


def create_issue(inputs: dict, context: dict) -> dict:
    """Create a new issue in Linear.
    
    inputs: team_id, title, description (optional), priority (optional), assignee_id (optional)
    Returns: { "issue": { "id": "...", "identifier": "ENG-123", "url": "..." } }
    """
    team_id = inputs["team_id"]
    title = inputs["title"]
    
    # Build mutation input
    mutation_input = {
        "teamId": team_id,
        "title": title
    }
    
    if "description" in inputs and inputs["description"]:
        mutation_input["description"] = inputs["description"]
    
    if "priority" in inputs and inputs["priority"] is not None:
        mutation_input["priority"] = inputs["priority"]
    
    if "assignee_id" in inputs and inputs["assignee_id"]:
        mutation_input["assigneeId"] = inputs["assignee_id"]
    
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
    
    data = _make_request(mutation, {"input": mutation_input})
    
    if not data["issueCreate"]["success"]:
        raise ValueError("Failed to create issue")
    
    return {
        "issue": data["issueCreate"]["issue"]
    }


def update_issue(inputs: dict, context: dict) -> dict:
    """Update an existing issue.
    
    inputs: issue_id, title (optional), state_id (optional), assignee_id (optional), priority (optional)
    Returns: { "issue": { "id": "...", "identifier": "ENG-123" } }
    """
    issue_id = inputs["issue_id"]
    
    # Build update input (only include fields that are provided)
    mutation_input = {}
    
    if "title" in inputs and inputs["title"]:
        mutation_input["title"] = inputs["title"]
    
    if "state_id" in inputs and inputs["state_id"]:
        mutation_input["stateId"] = inputs["state_id"]
    
    if "assignee_id" in inputs and inputs["assignee_id"]:
        mutation_input["assigneeId"] = inputs["assignee_id"]
    
    if "priority" in inputs and inputs["priority"] is not None:
        mutation_input["priority"] = inputs["priority"]
    
    if not mutation_input:
        raise ValueError("No fields to update. Provide at least one of: title, state_id, assignee_id, priority")
    
    mutation = """
    mutation($id: String!, $input: IssueUpdateInput!) {
      issueUpdate(id: $id, input: $input) {
        success
        issue {
          id
          identifier
        }
      }
    }
    """
    
    data = _make_request(mutation, {"id": issue_id, "input": mutation_input})
    
    if not data["issueUpdate"]["success"]:
        raise ValueError("Failed to update issue")
    
    return {
        "issue": data["issueUpdate"]["issue"]
    }


def list_issues(inputs: dict, context: dict) -> dict:
    """List issues with optional filters.
    
    inputs: team_id (optional), state_id (optional), assignee_id (optional), limit (optional, default 50)
    Returns: { "issues": [{ "id": "...", "identifier": "...", "title": "...", ... }] }
    """
    limit = inputs.get("limit", 50)
    limit = min(limit, 250)  # Cap at 250
    
    # Build filter object using GraphQL variables (no string interpolation)
    issue_filter = {}
    if "team_id" in inputs and inputs["team_id"]:
        issue_filter["team"] = {"id": {"eq": inputs["team_id"]}}
    if "state_id" in inputs and inputs["state_id"]:
        issue_filter["state"] = {"id": {"eq": inputs["state_id"]}}
    if "assignee_id" in inputs and inputs["assignee_id"]:
        issue_filter["assignee"] = {"id": {"eq": inputs["assignee_id"]}}
    
    cursor = None
    all_issues = []
    
    while len(all_issues) < limit:
        query = """
        query($after: String, $first: Int, $filter: IssueFilter) {
          issues(after: $after, first: $first, filter: $filter) {
            nodes {
              id
              identifier
              title
              state { id name }
              assignee { id name }
              priority
              createdAt
            }
            pageInfo {
              hasNextPage
              endCursor
            }
          }
        }
        """
        
        variables = {"first": min(50, limit - len(all_issues))}
        if issue_filter:
            variables["filter"] = issue_filter
        if cursor:
            variables["after"] = cursor
        
        data = _make_request(query, variables)
        issues = data["issues"]["nodes"]
        all_issues.extend(issues)
        
        if not data["issues"]["pageInfo"]["hasNextPage"]:
            break
        cursor = data["issues"]["pageInfo"]["endCursor"]
    
    return {"issues": all_issues[:limit]}


def list_teams(inputs: dict, context: dict) -> dict:
    """List all teams in workspace.
    
    Returns: { "teams": [{ "id": "...", "name": "...", "key": "ENG" }] }
    """
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
    
    data = _make_request(query)
    return {"teams": data["teams"]["nodes"]}


def list_projects(inputs: dict, context: dict) -> dict:
    """List all projects in workspace.
    
    inputs: limit (optional, default 50)
    Returns: { "projects": [{ "id": "...", "name": "...", "state": "..." }] }
    """
    limit = inputs.get("limit", 50)
    limit = min(limit, 250)
    
    cursor = None
    all_projects = []
    
    while len(all_projects) < limit:
        query = """
        query($after: String, $first: Int) {
          projects(after: $after, first: $first) {
            nodes {
              id
              name
              state
            }
            pageInfo {
              hasNextPage
              endCursor
            }
          }
        }
        """
        
        variables = {"first": min(50, limit - len(all_projects))}
        if cursor:
            variables["after"] = cursor
        
        data = _make_request(query, variables)
        projects = data["projects"]["nodes"]
        all_projects.extend(projects)
        
        if not data["projects"]["pageInfo"]["hasNextPage"]:
            break
        cursor = data["projects"]["pageInfo"]["endCursor"]
    
    return {"projects": all_projects[:limit]}


def list_cycles(inputs: dict, context: dict) -> dict:
    """List active cycles for a team.
    
    inputs: team_id, limit (optional, default 10)
    Returns: { "cycles": [{ "id": "...", "name": "...", "number": 1 }] }
    """
    team_id = inputs["team_id"]
    limit = inputs.get("limit", 10)
    limit = min(limit, 100)
    
    query = """
    query($team_id: String!, $limit: Int) {
      team(id: $team_id) {
        cycles(first: $limit) {
          nodes {
            id
            name
            number
          }
        }
      }
    }
    """
    
    data = _make_request(query, {"team_id": team_id, "limit": limit})
    
    if not data.get("team"):
        raise ValueError(f"Team not found: {team_id}")
    
    return {"cycles": data["team"]["cycles"]["nodes"]}


def add_comment(inputs: dict, context: dict) -> dict:
    """Add a comment to an issue.
    
    inputs: issue_id, body (markdown)
    Returns: { "comment": { "id": "...", "body": "..." } }
    """
    issue_id = inputs["issue_id"]
    body = inputs["body"]
    
    mutation = """
    mutation($input: CommentCreateInput!) {
      commentCreate(input: $input) {
        success
        comment {
          id
          body
        }
      }
    }
    """
    
    mutation_input = {
        "issueId": issue_id,
        "body": body
    }
    
    data = _make_request(mutation, {"input": mutation_input})
    
    if not data["commentCreate"]["success"]:
        raise ValueError("Failed to add comment")
    
    return {
        "comment": data["commentCreate"]["comment"]
    }


def update_state(inputs: dict, context: dict) -> dict:
    """Transition issue to a new state.
    
    inputs: issue_id, state_id
    Returns: { "issue": { "id": "...", "state": { "name": "Done" } } }
    """
    issue_id = inputs["issue_id"]
    state_id = inputs["state_id"]
    
    mutation = """
    mutation($id: String!, $input: IssueUpdateInput!) {
      issueUpdate(id: $id, input: $input) {
        success
        issue {
          id
          state {
            id
            name
          }
        }
      }
    }
    """
    
    mutation_input = {"stateId": state_id}
    
    data = _make_request(mutation, {"id": issue_id, "input": mutation_input})
    
    if not data["issueUpdate"]["success"]:
        raise ValueError("Failed to update issue state")
    
    return {
        "issue": data["issueUpdate"]["issue"]
    }
