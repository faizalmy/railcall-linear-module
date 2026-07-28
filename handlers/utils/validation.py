"""Input validation utilities for Linear API operations."""

import re
from datetime import datetime
from typing import Optional

from .errors import ValidationError

UUID_PATTERN = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'


def validate_uuid(value: str, field_name: str) -> None:
    """Validate UUID format.

    Args:
        value: UUID string to validate
        field_name: Name of the field for error messages

    Raises:
        ValidationError: If UUID format is invalid
    """
    if not re.match(UUID_PATTERN, value):
        raise ValidationError(f"Invalid {field_name} format: {value}. Expected UUID format.")


def validate_priority(priority: int) -> None:
    """Validate priority value (0-4).
    
    Args:
        priority: Priority value to validate
        
    Raises:
        ValidationError: If priority is not 0-4
    """
    if priority not in [0, 1, 2, 3, 4]:
        raise ValidationError(f"Priority must be 0-4 (none, urgent, high, medium, low), got {priority}")


# Linear's human-readable issue key: team key, a dash, then a number - ENG-123.
# Team keys are alphanumeric and start with a letter; Linear matches them
# case-insensitively, so `eng-123` resolves the same issue as `ENG-123`.
ISSUE_IDENTIFIER_PATTERN = r'^[A-Za-z][A-Za-z0-9]*-\d+$'


def validate_issue_id(issue_id: str) -> None:
    """Validate an issue reference: either a UUID or an ENG-123 identifier.

    Linear's `issue(id:)` argument and every issue mutation accept both forms -
    verified live against issueUpdate, issueArchive, commentCreate and
    issueRelationCreate. Requiring the UUID was this module's own restriction,
    not the API's, and it forced operators to go hunting for a UUID when the
    identifier was already in front of them in the Linear URL.

    Args:
        issue_id: Issue UUID or team identifier (e.g. "ENG-123")

    Raises:
        ValidationError: If the value is neither form
    """
    if not issue_id or not isinstance(issue_id, str):
        raise ValidationError(
            "Invalid issue_id: expected a UUID or an identifier like 'ENG-123'."
        )

    if re.match(ISSUE_IDENTIFIER_PATTERN, issue_id):
        return

    if not re.match(UUID_PATTERN, issue_id):
        raise ValidationError(
            f"Invalid issue_id format: {issue_id}. Expected a UUID or an "
            f"identifier like 'ENG-123'."
        )


def validate_team_id(team_id: str) -> None:
    """Validate team ID format.
    
    Args:
        team_id: Team ID to validate
        
    Raises:
        ValidationError: If team ID format is invalid
    """
    validate_uuid(team_id, "team_id")


def validate_project_id(project_id: str) -> None:
    """Validate project ID format.
    
    Args:
        project_id: Project ID to validate
        
    Raises:
        ValidationError: If project ID format is invalid
    """
    validate_uuid(project_id, "project_id")


def validate_user_id(user_id: str) -> None:
    """Validate user ID format.
    
    Args:
        user_id: User ID to validate
        
    Raises:
        ValidationError: If user ID format is invalid
    """
    validate_uuid(user_id, "user_id")


def validate_state_id(state_id: str) -> None:
    """Validate state ID format.
    
    Args:
        state_id: State ID to validate
        
    Raises:
        ValidationError: If state ID format is invalid
    """
    validate_uuid(state_id, "state_id")


def validate_label_id(label_id: str) -> None:
    """Validate label ID format.
    
    Args:
        label_id: Label ID to validate
        
    Raises:
        ValidationError: If label ID format is invalid
    """
    validate_uuid(label_id, "label_id")


def validate_cycle_id(cycle_id: str) -> None:
    """Validate cycle ID format.
    
    Args:
        cycle_id: Cycle ID to validate
        
    Raises:
        ValidationError: If cycle ID format is invalid
    """
    validate_uuid(cycle_id, "cycle_id")


def validate_milestone_id(milestone_id: str) -> None:
    """Validate milestone ID format.
    
    Args:
        milestone_id: Milestone ID to validate
        
    Raises:
        ValidationError: If milestone ID format is invalid
    """
    validate_uuid(milestone_id, "milestone_id")


def validate_initiative_id(initiative_id: str) -> None:
    """Validate initiative ID format.

    Args:
        initiative_id: Initiative ID to validate

    Raises:
        ValidationError: If initiative ID format is invalid
    """
    validate_uuid(initiative_id, "initiative_id")


def validate_webhook_id(webhook_id: str) -> None:
    """Validate webhook ID format.
    
    Args:
        webhook_id: Webhook ID to validate
        
    Raises:
        ValidationError: If webhook ID format is invalid
    """
    validate_uuid(webhook_id, "webhook_id")


def validate_limit(limit: Optional[int], default: int = 50, max_limit: int = 250) -> int:
    """Validate and normalize limit parameter.
    
    Args:
        limit: Limit value to validate
        default: Default value if limit is None
        max_limit: Maximum allowed limit
        
    Returns:
        Validated limit value
        
    Raises:
        ValidationError: If limit is out of range
    """
    if limit is None:
        return default
    
    if not isinstance(limit, int) or limit < 1:
        raise ValidationError(f"Limit must be a positive integer, got {limit}")
    
    if limit > max_limit:
        raise ValidationError(f"Limit cannot exceed {max_limit}, got {limit}")
    
    return limit


def validate_url(url: str, field_name: str = "url") -> None:
    """Validate URL format.
    
    Args:
        url: URL to validate
        field_name: Name of the field for error messages
        
    Raises:
        ValidationError: If URL format is invalid
    """
    url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    if not re.match(url_pattern, url, re.IGNORECASE):
        raise ValidationError(f"Invalid {field_name} format: {url}")


def validate_comment_id(comment_id: str) -> None:
    """Validate comment ID format.

    Args:
        comment_id: Comment ID to validate

    Raises:
        ValidationError: If comment ID format is invalid
    """
    validate_uuid(comment_id, "comment_id")


def validate_color(color: str, field_name: str = "color") -> None:
    """Validate a hex color code as Linear expects it (#RGB or #RRGGBB).

    Args:
        color: Color string to validate
        field_name: Name of the field for error messages

    Raises:
        ValidationError: If the color is not a hex code
    """
    if not re.match(r'^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$', color or ""):
        raise ValidationError(
            f"Invalid {field_name}: {color}. Expected a hex code such as '#FF0000'."
        )


def validate_iso_date(value: str, field_name: str) -> None:
    """Validate an ISO 8601 date or datetime string.

    Args:
        value: Date string to validate
        field_name: Name of the field for error messages

    Raises:
        ValidationError: If the value is not ISO 8601
    """
    candidate = (value or "").strip()
    if not candidate:
        raise ValidationError(f"{field_name} cannot be empty")

    # datetime.fromisoformat below Python 3.11 does not accept a trailing 'Z'
    normalized = candidate[:-1] + "+00:00" if candidate.endswith("Z") else candidate

    try:
        datetime.fromisoformat(normalized)
    except ValueError:
        raise ValidationError(
            f"Invalid {field_name}: {value}. Expected ISO 8601, "
            f"e.g. '2026-01-31' or '2026-01-31T00:00:00Z'."
        )


def validate_non_empty(value: str, field_name: str) -> None:
    """Validate that a required string carries actual content.

    Args:
        value: String to validate
        field_name: Name of the field for error messages

    Raises:
        ValidationError: If the value is empty or whitespace only
    """
    if not value or not value.strip():
        raise ValidationError(f"{field_name} cannot be empty")


def validate_timeless_date(value: str, field_name: str) -> str:
    """Validate a date and normalize it to Linear's TimelessDate (YYYY-MM-DD).

    ProjectMilestone.targetDate is a TimelessDate, not a datetime. An ISO
    datetime is accepted and truncated to its date part.

    Args:
        value: Date string to validate
        field_name: Name of the field for error messages

    Returns:
        The date as YYYY-MM-DD

    Raises:
        ValidationError: If the value is not a valid ISO date or datetime
    """
    validate_iso_date(value, field_name)

    candidate = value.strip()
    normalized = candidate[:-1] + "+00:00" if candidate.endswith("Z") else candidate
    return datetime.fromisoformat(normalized).date().isoformat()


def validate_resource_types(resource_types: list) -> None:
    """Validate a webhook's resourceTypes list.

    Linear requires at least one; unknown names are rejected server-side, so
    this checks shape rather than pinning a list that drifts with the API.
    Common values: Issue, Comment, IssueLabel, Project, ProjectUpdate, Cycle,
    Reaction, Document, Initiative.

    Args:
        resource_types: List of resource type names

    Raises:
        ValidationError: If the list is empty or holds non-strings
    """
    if not resource_types:
        raise ValidationError(
            "resource_types cannot be empty - Linear requires at least one, "
            "e.g. ['Issue', 'Comment']."
        )

    for item in resource_types:
        if not isinstance(item, str) or not item.strip():
            raise ValidationError(f"Invalid resource type: {item!r}. Expected a non-empty string.")
