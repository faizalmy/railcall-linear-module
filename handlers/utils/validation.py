"""Input validation utilities for Linear API operations."""

import re
from typing import Any, Optional

from .errors import ValidationError


def validate_uuid(value: str, field_name: str) -> None:
    """Validate UUID format.
    
    Args:
        value: UUID string to validate
        field_name: Name of the field for error messages
        
    Raises:
        ValidationError: If UUID format is invalid
    """
    uuid_pattern = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
    if not re.match(uuid_pattern, value):
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


def validate_issue_id(issue_id: str) -> None:
    """Validate Linear issue ID format.
    
    Args:
        issue_id: Issue ID to validate
        
    Raises:
        ValidationError: If issue ID format is invalid
    """
    validate_uuid(issue_id, "issue_id")


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


def validate_webhook_events(events: list) -> None:
    """Validate webhook event types.
    
    Args:
        events: List of event types to validate
        
    Raises:
        ValidationError: If event types are invalid
    """
    valid_events = {
        "issue.created",
        "issue.updated",
        "issue.deleted",
        "issue.archived",
        "project.created",
        "project.updated",
        "project.deleted",
        "team.created",
        "team.updated",
        "team.deleted",
        "comment.created",
        "comment.updated",
        "comment.deleted",
    }
    
    for event in events:
        if event not in valid_events:
            raise ValidationError(f"Invalid webhook event type: {event}")
