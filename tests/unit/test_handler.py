"""Tests for main handler functions."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from handlers.handler import (
    list_issues,
    get_issue,
    create_issue,
    update_issue,
    delete_issue,
    search_issues,
    bulk_update_issues,
    link_issues,
    list_teams,
    get_team,
    list_projects,
    get_project,
    list_users,
    get_user,
    list_states,
    create_state,
    update_state,
    list_labels,
    create_label,
    update_label,
    list_cycles,
    get_cycle,
    create_cycle,
    update_cycle,
    list_comments,
    create_comment,
    update_comment,
    delete_comment,
    list_webhooks,
    create_webhook,
    update_webhook,
    delete_webhook,
    list_milestones,
    create_milestone,
    update_milestone,
)
from handlers.utils.errors import ValidationError


class TestIssueCommands:
    """Test issue-related commands."""
    
    @patch('handlers.handler.execute_query')
    def test_list_issues_success(self, mock_query):
        """Should list issues successfully."""
        mock_query.return_value = {
            "issues": {
                "nodes": [{"id": "issue-1", "title": "Test"}],
                "pageInfo": {"hasNextPage": False, "endCursor": None}
            }
        }
        
        result = list_issues()
        assert "issues" in result
        assert len(result["issues"]) == 1
    
    @patch('handlers.handler.execute_query')
    def test_get_issue_success(self, mock_query):
        """Should get issue details successfully."""
        mock_query.return_value = {
            "issue": {"id": "123e4567-e89b-12d3-a456-426614174000", "title": "Test Issue"}
        }
        
        result = get_issue(issue_id="123e4567-e89b-12d3-a456-426614174000")
        assert result["issue"]["id"] == "123e4567-e89b-12d3-a456-426614174000"
    
    @patch('handlers.handler.execute_query')
    def test_create_issue_success(self, mock_query):
        """Should create issue successfully."""
        mock_query.return_value = {
            "issueCreate": {
                "success": True,
                "issue": {"id": "123e4567-e89b-12d3-a456-426614174000", "title": "New Issue"}
            }
        }
        
        result = create_issue(
            team_id="123e4567-e89b-12d3-a456-426614174001",
            title="New Issue",
            description="Test description"
        )
        assert result["issue"]["title"] == "New Issue"
    
    @patch('handlers.handler.execute_query')
    def test_update_issue_success(self, mock_query):
        """Should update issue successfully."""
        mock_query.return_value = {
            "issueUpdate": {
                "success": True,
                "issue": {"id": "123e4567-e89b-12d3-a456-426614174000", "title": "Updated"}
            }
        }
        
        result = update_issue(issue_id="123e4567-e89b-12d3-a456-426614174000", title="Updated")
        assert result["issue"]["title"] == "Updated"
    
    @patch('handlers.handler.execute_query')
    def test_delete_issue_success(self, mock_query):
        """Should delete issue successfully."""
        mock_query.return_value = {
            "issueDelete": {"success": True}
        }
        
        result = delete_issue(issue_id="123e4567-e89b-12d3-a456-426614174000")
        assert result["success"] is True
    
    @patch('handlers.handler.execute_query')
    def test_search_issues_success(self, mock_query):
        """Should search issues successfully."""
        mock_query.return_value = {
            "issues": {
                "nodes": [{"id": "issue-1", "title": "Search Result"}],
                "pageInfo": {"hasNextPage": False, "endCursor": None}
            }
        }
        
        result = search_issues(query="test")
        assert "issues" in result
        assert len(result["issues"]) == 1
    
    @patch('handlers.handler.execute_query')
    def test_bulk_update_issues_success(self, mock_query):
        """Should bulk update issues successfully."""
        mock_query.return_value = {
            "issueUpdate": {"success": True, "issue": {"id": "123e4567-e89b-12d3-a456-426614174000"}}
        }
        
        result = bulk_update_issues(
            issue_ids=["123e4567-e89b-12d3-a456-426614174000", "123e4567-e89b-12d3-a456-426614174001"],
            state_id="123e4567-e89b-12d3-a456-426614174002"
        )
        assert result["success_count"] == 2


class TestTeamCommands:
    """Test team-related commands."""
    
    @patch('handlers.handler.execute_query')
    def test_list_teams_success(self, mock_query):
        """Should list teams successfully."""
        mock_query.return_value = {
            "teams": {
                "nodes": [{"id": "team-1", "name": "Engineering"}],
                "pageInfo": {"hasNextPage": False, "endCursor": None}
            }
        }
        
        result = list_teams()
        assert "teams" in result
        assert len(result["teams"]) == 1
    
    @patch('handlers.handler.execute_query')
    def test_get_team_success(self, mock_query):
        """Should get team details successfully."""
        mock_query.return_value = {
            "team": {"id": "123e4567-e89b-12d3-a456-426614174000", "name": "Engineering"}
        }
        
        result = get_team(team_id="123e4567-e89b-12d3-a456-426614174000")
        assert result["team"]["name"] == "Engineering"


class TestProjectCommands:
    """Test project-related commands."""
    
    @patch('handlers.handler.execute_query')
    def test_list_projects_success(self, mock_query):
        """Should list projects successfully."""
        mock_query.return_value = {
            "projects": {
                "nodes": [{"id": "project-1", "name": "Test Project"}],
                "pageInfo": {"hasNextPage": False, "endCursor": None}
            }
        }
        
        result = list_projects()
        assert "projects" in result
        assert len(result["projects"]) == 1
    
    @patch('handlers.handler.execute_query')
    def test_get_project_success(self, mock_query):
        """Should get project details successfully."""
        mock_query.return_value = {
            "project": {"id": "123e4567-e89b-12d3-a456-426614174000", "name": "Test Project"}
        }
        
        result = get_project(project_id="123e4567-e89b-12d3-a456-426614174000")
        assert result["project"]["name"] == "Test Project"


class TestUserCommands:
    """Test user-related commands."""
    
    @patch('handlers.handler.execute_query')
    def test_list_users_success(self, mock_query):
        """Should list users successfully."""
        mock_query.return_value = {
            "users": {
                "nodes": [{"id": "user-1", "name": "John Doe"}],
                "pageInfo": {"hasNextPage": False, "endCursor": None}
            }
        }
        
        result = list_users()
        assert "users" in result
        assert len(result["users"]) == 1
    
    @patch('handlers.handler.execute_query')
    def test_get_user_success(self, mock_query):
        """Should get user details successfully."""
        mock_query.return_value = {
            "user": {"id": "123e4567-e89b-12d3-a456-426614174000", "name": "John Doe"}
        }
        
        result = get_user(user_id="123e4567-e89b-12d3-a456-426614174000")
        assert result["user"]["name"] == "John Doe"


class TestStateCommands:
    """Test state-related commands."""
    
    @patch('handlers.handler.execute_query')
    def test_list_states_success(self, mock_query):
        """Should list states successfully."""
        mock_query.return_value = {
            "workflowStates": {
                "nodes": [{"id": "state-1", "name": "Todo"}],
                "pageInfo": {"hasNextPage": False, "endCursor": None}
            }
        }
        
        result = list_states()
        assert "states" in result
        assert len(result["states"]) == 1
    
    @patch('handlers.handler.execute_query')
    def test_create_state_success(self, mock_query):
        """Should create state successfully."""
        mock_query.return_value = {
            "workflowStateCreate": {
                "success": True,
                "workflowState": {"id": "state-1", "name": "New State"}
            }
        }
        
        result = create_state(
            team_id="123e4567-e89b-12d3-a456-426614174000",
            name="New State",
            color="#FF0000"
        )
        assert result["state"]["name"] == "New State"


class TestLabelCommands:
    """Test label-related commands."""
    
    @patch('handlers.handler.execute_query')
    def test_list_labels_success(self, mock_query):
        """Should list labels successfully."""
        mock_query.return_value = {
            "issueLabels": {
                "nodes": [{"id": "label-1", "name": "Bug"}],
                "pageInfo": {"hasNextPage": False, "endCursor": None}
            }
        }
        
        result = list_labels()
        assert "labels" in result
        assert len(result["labels"]) == 1
    
    @patch('handlers.handler.execute_query')
    def test_create_label_success(self, mock_query):
        """Should create label successfully."""
        mock_query.return_value = {
            "issueLabelCreate": {
                "success": True,
                "issueLabel": {"id": "label-1", "name": "New Label"}
            }
        }
        
        result = create_label(
            team_id="123e4567-e89b-12d3-a456-426614174000",
            name="New Label",
            color="#00FF00"
        )
        assert result["label"]["name"] == "New Label"


class TestCycleCommands:
    """Test cycle-related commands."""
    
    @patch('handlers.handler.execute_query')
    def test_list_cycles_success(self, mock_query):
        """Should list cycles successfully."""
        mock_query.return_value = {
            "cycles": {
                "nodes": [{"id": "cycle-1", "name": "Sprint 1"}],
                "pageInfo": {"hasNextPage": False, "endCursor": None}
            }
        }
        
        result = list_cycles(team_id="123e4567-e89b-12d3-a456-426614174000")
        assert "cycles" in result
        assert len(result["cycles"]) == 1
    
    @patch('handlers.handler.execute_query')
    def test_create_cycle_success(self, mock_query):
        """Should create cycle successfully."""
        mock_query.return_value = {
            "cycleCreate": {
                "success": True,
                "cycle": {"id": "cycle-1", "name": "New Cycle"}
            }
        }
        
        result = create_cycle(
            team_id="123e4567-e89b-12d3-a456-426614174000",
            name="New Cycle",
            starts_at="2026-01-01T00:00:00Z",
            ends_at="2026-01-14T00:00:00Z"
        )
        assert result["cycle"]["name"] == "New Cycle"


class TestCommentCommands:
    """Test comment-related commands."""
    
    @patch('handlers.handler.execute_query')
    def test_list_comments_success(self, mock_query):
        """Should list comments successfully."""
        mock_query.return_value = {
            "comments": {
                "nodes": [{"id": "123e4567-e89b-12d3-a456-426614174000", "body": "Test comment"}],
                "pageInfo": {"hasNextPage": False, "endCursor": None}
            }
        }
        
        result = list_comments(issue_id="123e4567-e89b-12d3-a456-426614174000")
        assert "comments" in result
        assert len(result["comments"]) == 1
    
    @patch('handlers.handler.execute_query')
    def test_create_comment_success(self, mock_query):
        """Should create comment successfully."""
        mock_query.return_value = {
            "commentCreate": {
                "success": True,
                "comment": {"id": "123e4567-e89b-12d3-a456-426614174000", "body": "New comment"}
            }
        }
        
        result = create_comment(
            issue_id="123e4567-e89b-12d3-a456-426614174000",
            body="New comment"
        )
        assert result["comment"]["body"] == "New comment"


class TestWebhookCommands:
    """Test webhook-related commands."""
    
    @patch('handlers.handler.execute_query')
    def test_list_webhooks_success(self, mock_query):
        """Should list webhooks successfully."""
        mock_query.return_value = {
            "webhooks": {
                "nodes": [{"id": "webhook-1", "url": "https://example.com"}],
                "pageInfo": {"hasNextPage": False, "endCursor": None}
            }
        }
        
        result = list_webhooks()
        assert "webhooks" in result
        assert len(result["webhooks"]) == 1
    
    @patch('handlers.handler.execute_query')
    def test_create_webhook_success(self, mock_query):
        """Should create webhook successfully."""
        mock_query.return_value = {
            "webhookCreate": {
                "success": True,
                "webhook": {"id": "webhook-1", "url": "https://example.com"}
            }
        }
        
        result = create_webhook(url="https://example.com")
        assert result["webhook"]["url"] == "https://example.com"


class TestMilestoneCommands:
    """Test milestone-related commands."""
    
    @patch('handlers.handler.execute_query')
    def test_list_milestones_success(self, mock_query):
        """Should list milestones successfully."""
        mock_query.return_value = {
            "milestones": {
                "nodes": [{"id": "milestone-1", "name": "v1.0"}],
                "pageInfo": {"hasNextPage": False, "endCursor": None}
            }
        }
        
        result = list_milestones()
        assert "milestones" in result
        assert len(result["milestones"]) == 1
    
    @patch('handlers.handler.execute_query')
    def test_create_milestone_success(self, mock_query):
        """Should create milestone successfully."""
        mock_query.return_value = {
            "milestoneCreate": {
                "success": True,
                "milestone": {"id": "milestone-1", "name": "v2.0"}
            }
        }
        
        result = create_milestone(
            name="v2.0",
            target_date="2026-12-31T00:00:00Z"
        )
        assert result["milestone"]["name"] == "v2.0"
