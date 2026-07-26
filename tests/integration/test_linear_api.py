"""Integration tests for Linear module (requires API key)."""

import os
import pytest
from handlers.handler import (
    list_issues,
    get_issue,
    create_issue,
    update_issue,
    delete_issue,
    list_teams,
    get_team,
    list_projects,
    get_project,
    list_users,
    get_user,
)


# Skip all tests if no API key is available
pytestmark = pytest.mark.skipif(
    not os.environ.get("LINEAR_API_KEY"),
    reason="LINEAR_API_KEY environment variable not set"
)


class TestIssueIntegration:
    """Integration tests for issue operations."""
    
    def test_list_issues_integration(self):
        """Should list issues from real Linear workspace."""
        result = list_issues(limit=5)
        assert "issues" in result
        assert isinstance(result["issues"], list)
    
    def test_create_and_delete_issue_integration(self):
        """Should create and delete an issue."""
        # First, get a team ID
        teams_result = list_teams()
        assert len(teams_result["teams"]) > 0
        team_id = teams_result["teams"][0]["id"]
        
        # Create an issue
        create_result = create_issue(
            team_id=team_id,
            title="Integration Test Issue",
            description="This is a test issue created by integration tests"
        )
        assert "issue" in create_result
        issue_id = create_result["issue"]["id"]
        
        # Get the issue
        get_result = get_issue(issue_id=issue_id)
        assert get_result["issue"]["id"] == issue_id
        assert get_result["issue"]["title"] == "Integration Test Issue"
        
        # Update the issue
        update_result = update_issue(
            issue_id=issue_id,
            title="Updated Integration Test Issue"
        )
        assert update_result["issue"]["title"] == "Updated Integration Test Issue"
        
        # Delete the issue
        delete_result = delete_issue(issue_id=issue_id)
        assert delete_result["success"] is True


class TestTeamIntegration:
    """Integration tests for team operations."""
    
    def test_list_teams_integration(self):
        """Should list teams from real Linear workspace."""
        result = list_teams()
        assert "teams" in result
        assert isinstance(result["teams"], list)
        if len(result["teams"]) > 0:
            team = result["teams"][0]
            assert "id" in team
            assert "name" in team
    
    def test_get_team_integration(self):
        """Should get team details from real Linear workspace."""
        # First, list teams to get a valid team ID
        teams_result = list_teams()
        if len(teams_result["teams"]) > 0:
            team_id = teams_result["teams"][0]["id"]
            result = get_team(team_id=team_id)
            assert "team" in result
            assert result["team"]["id"] == team_id


class TestProjectIntegration:
    """Integration tests for project operations."""
    
    def test_list_projects_integration(self):
        """Should list projects from real Linear workspace."""
        result = list_projects()
        assert "projects" in result
        assert isinstance(result["projects"], list)
    
    def test_get_project_integration(self):
        """Should get project details from real Linear workspace."""
        # First, list projects to get a valid project ID
        projects_result = list_projects()
        if len(projects_result["projects"]) > 0:
            project_id = projects_result["projects"][0]["id"]
            result = get_project(project_id=project_id)
            assert "project" in result
            assert result["project"]["id"] == project_id


class TestUserIntegration:
    """Integration tests for user operations."""
    
    def test_list_users_integration(self):
        """Should list users from real Linear workspace."""
        result = list_users()
        assert "users" in result
        assert isinstance(result["users"], list)
    
    def test_get_user_integration(self):
        """Should get user details from real Linear workspace."""
        # First, list users to get a valid user ID
        users_result = list_users()
        if len(users_result["users"]) > 0:
            user_id = users_result["users"][0]["id"]
            result = get_user(user_id=user_id)
            assert "user" in result
            assert result["user"]["id"] == user_id
