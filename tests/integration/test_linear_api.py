"""Comprehensive integration tests for Linear module - creates visible test data."""

import os
import pytest
from datetime import datetime, timedelta
from handlers.handler import (
    # Issues
    list_issues, get_issue, create_issue, update_issue, delete_issue,
    search_issues, bulk_update_issues, link_issues,
    # Teams
    list_teams, get_team,
    # Projects
    list_projects, get_project,
    # Users
    list_users, get_user,
    # States
    list_states, create_state, update_state,
    # Labels
    list_labels, create_label, update_label,
    # Cycles
    list_cycles, get_cycle, create_cycle, update_cycle,
    # Comments
    list_comments, create_comment, update_comment, delete_comment,
    # Webhooks
    list_webhooks, create_webhook, update_webhook, delete_webhook,
    # Milestones
    list_milestones, create_milestone, update_milestone,
)


# Skip all tests if no API key is available
pytestmark = pytest.mark.skipif(
    not os.environ.get("LINEAR_API_KEY"),
    reason="LINEAR_API_KEY environment variable not set"
)


# Test data prefix for easy identification in Linear
TEST_PREFIX = "[RailCall Test]"


class TestIssueManagement:
    """Integration tests for issue operations - creates visible test data."""
    
    def test_01_list_issues(self):
        """Should list issues from Linear workspace."""
        result = list_issues(limit=10)
        assert "issues" in result
        assert isinstance(result["issues"], list)
        print(f"✓ Listed {len(result['issues'])} issues")
    
    def test_02_create_test_issue(self):
        """Should create a test issue that remains visible in Linear."""
        teams = list_teams()
        assert len(teams["teams"]) > 0
        team_id = teams["teams"][0]["id"]
        
        result = create_issue(
            team_id=team_id,
            title=f"{TEST_PREFIX} Integration Test Issue",
            description="This issue was created by integration tests to verify the Linear API is working correctly.",
            priority=2  # High
        )
        
        assert "issue" in result
        assert result["issue"]["title"] == f"{TEST_PREFIX} Integration Test Issue"
        print(f"✓ Created issue: {result['issue']['identifier']}")
    
    def test_03_create_multiple_issues_for_bulk_test(self):
        """Should create multiple issues for bulk operations testing."""
        teams = list_teams()
        team_id = teams["teams"][0]["id"]
        
        created_issues = []
        for i in range(1, 4):
            result = create_issue(
                team_id=team_id,
                title=f"{TEST_PREFIX} Bulk Test Issue #{i}",
                description=f"This is test issue #{i} for bulk operations.",
                priority=3  # Medium
            )
            created_issues.append(result["issue"]["id"])
        
        assert len(created_issues) == 3
        print("✓ Created 3 issues for bulk testing")
    
    def test_04_search_issues(self):
        """Should search for test issues."""
        result = search_issues(query="RailCall Test", limit=10)
        assert "issues" in result
        assert len(result["issues"]) > 0
        print(f"✓ Found {len(result['issues'])} test issues via search")
    
    def test_05_bulk_update_issues(self):
        """Should bulk update test issues."""
        # Get issues created in previous tests
        issues = list_issues(limit=50)
        test_issue_ids = [
            issue["id"] for issue in issues["issues"]
            if issue["title"].startswith(TEST_PREFIX) and "Bulk Test" in issue["title"]
        ]
        
        if len(test_issue_ids) >= 3:
            # Update priority for all test issues
            result = bulk_update_issues(
                issue_ids=test_issue_ids[:3],
                priority=1  # Urgent
            )
            
            assert result["success_count"] == 3
            print(f"✓ Bulk updated {result['success_count']} issues to priority=1")
    
    def test_06_link_issues(self):
        """Should create relationships between test issues."""
        issues = list_issues(limit=50)
        test_issues = [
            issue for issue in issues["issues"]
            if issue["title"].startswith(TEST_PREFIX)
        ]
        
        if len(test_issues) >= 2:
            result = link_issues(
                issue_id=test_issues[0]["id"],
                related_issue_id=test_issues[1]["id"],
                relationship_type="blocks"
            )
            
            assert result["success"] is True
            print(f"✓ Linked issues: {test_issues[0]['identifier']} blocks {test_issues[1]['identifier']}")
    
    def test_07_get_issue_details(self):
        """Should retrieve detailed issue information."""
        issues = list_issues(limit=10)
        test_issue = next(
            (issue for issue in issues["issues"] 
             if issue["title"].startswith(TEST_PREFIX)),
            None
        )
        
        if test_issue:
            result = get_issue(issue_id=test_issue["id"])
            assert result["issue"]["id"] == test_issue["id"]
            assert result["issue"]["title"] == test_issue["title"]
            print(f"✓ Retrieved issue details: {result['issue']['identifier']}")
    
    def test_08_update_issue(self):
        """Should update a test issue."""
        issues = list_issues(limit=10)
        test_issue = next(
            (issue for issue in issues["issues"]
             if issue["title"] == f"{TEST_PREFIX} Integration Test Issue"),
            None
        )
        
        if test_issue:
            result = update_issue(
                issue_id=test_issue["id"],
                title=f"{TEST_PREFIX} Integration Test Issue (Updated)",
                description="This issue has been updated by integration tests."
            )
            
            assert result["issue"]["title"] == f"{TEST_PREFIX} Integration Test Issue (Updated)"
            print(f"✓ Updated issue: {test_issue['identifier']}")


class TestTeamManagement:
    """Integration tests for team operations."""
    
    def test_01_list_teams(self):
        """Should list all teams in workspace."""
        result = list_teams()
        assert "teams" in result
        assert len(result["teams"]) > 0
        print(f"✓ Listed {len(result['teams'])} teams")
        for team in result["teams"]:
            print(f"  - {team['name']} ({team['key']})")
    
    def test_02_get_team_details(self):
        """Should get detailed team information."""
        teams = list_teams()
        team_id = teams["teams"][0]["id"]
        
        result = get_team(team_id=team_id)
        assert "team" in result
        assert result["team"]["id"] == team_id
        print(f"✓ Retrieved team: {result['team']['name']}")


class TestProjectManagement:
    """Integration tests for project operations."""
    
    def test_01_list_projects(self):
        """Should list all projects in workspace."""
        result = list_projects()
        assert "projects" in result
        print(f"✓ Listed {len(result['projects'])} projects")
        for project in result["projects"][:5]:  # Show first 5
            print(f"  - {project['name']}")
    
    def test_02_get_project_details(self):
        """Should get detailed project information."""
        projects = list_projects()
        if len(projects["projects"]) > 0:
            project_id = projects["projects"][0]["id"]
            result = get_project(project_id=project_id)
            assert "project" in result
            print(f"✓ Retrieved project: {result['project']['name']}")


class TestUserManagement:
    """Integration tests for user operations."""
    
    def test_01_list_users(self):
        """Should list all users in workspace."""
        result = list_users()
        assert "users" in result
        print(f"✓ Listed {len(result['users'])} users")
        for user in result["users"][:5]:  # Show first 5
            print(f"  - {user['name']} ({user['email']})")
    
    def test_02_get_user_details(self):
        """Should get detailed user information."""
        users = list_users()
        if len(users["users"]) > 0:
            user_id = users["users"][0]["id"]
            result = get_user(user_id=user_id)
            assert "user" in result
            print(f"✓ Retrieved user: {result['user']['name']}")


class TestWorkflowStates:
    """Integration tests for workflow state operations - creates visible test data."""
    
    def test_01_list_states(self):
        """Should list all workflow states."""
        teams = list_teams()
        team_id = teams["teams"][0]["id"]
        
        result = list_states(team_id=team_id)
        assert "states" in result
        print(f"✓ Listed {len(result['states'])} workflow states")
        for state in result["states"]:
            print(f"  - {state['name']} ({state['type']})")
    
    def test_02_create_test_state(self):
        """Should create a test workflow state."""
        teams = list_teams()
        team_id = teams["teams"][0]["id"]
        
        result = create_state(
            team_id=team_id,
            name=f"{TEST_PREFIX} Test State",
            color="#FF6B6B",
            state_type="triage"
        )
        
        assert "state" in result
        assert result["state"]["name"] == f"{TEST_PREFIX} Test State"
        print(f"✓ Created workflow state: {result['state']['name']}")
    
    def test_03_update_test_state(self):
        """Should update the test workflow state."""
        teams = list_teams()
        team_id = teams["teams"][0]["id"]
        
        states = list_states(team_id=team_id)
        test_state = next(
            (state for state in states["states"]
             if state["name"] == f"{TEST_PREFIX} Test State"),
            None
        )
        
        if test_state:
            result = update_state(
                state_id=test_state["id"],
                name=f"{TEST_PREFIX} Test State (Updated)",
                color="#4ECDC4"
            )
            
            assert result["state"]["name"] == f"{TEST_PREFIX} Test State (Updated)"
            print(f"✓ Updated workflow state: {result['state']['name']}")


class TestLabels:
    """Integration tests for label operations - creates visible test data."""
    
    def test_01_list_labels(self):
        """Should list all labels."""
        teams = list_teams()
        team_id = teams["teams"][0]["id"]
        
        result = list_labels(team_id=team_id)
        assert "labels" in result
        print(f"✓ Listed {len(result['labels'])} labels")
    
    def test_02_create_test_labels(self):
        """Should create test labels."""
        teams = list_teams()
        team_id = teams["teams"][0]["id"]
        
        labels_created = []
        for i, color in enumerate(["#FF6B6B", "#4ECDC4", "#45B7D1"], 1):
            result = create_label(
                team_id=team_id,
                name=f"{TEST_PREFIX} Test Label {i}",
                color=color,
                description=f"Test label {i} created by integration tests"
            )
            labels_created.append(result["label"]["id"])
        
        assert len(labels_created) == 3
        print("✓ Created 3 test labels")
    
    def test_03_update_test_label(self):
        """Should update a test label."""
        teams = list_teams()
        team_id = teams["teams"][0]["id"]
        
        labels = list_labels(team_id=team_id)
        test_label = next(
            (label for label in labels["labels"]
             if label["name"] == f"{TEST_PREFIX} Test Label 1"),
            None
        )
        
        if test_label:
            result = update_label(
                label_id=test_label["id"],
                name=f"{TEST_PREFIX} Test Label 1 (Updated)",
                color="#96CEB4"
            )
            
            assert result["label"]["name"] == f"{TEST_PREFIX} Test Label 1 (Updated)"
            print(f"✓ Updated label: {result['label']['name']}")


class TestCycles:
    """Integration tests for cycle operations - creates visible test data."""
    
    def test_01_list_cycles(self):
        """Should list cycles for a team."""
        teams = list_teams()
        team_id = teams["teams"][0]["id"]
        
        result = list_cycles(team_id=team_id)
        assert "cycles" in result
        print(f"✓ Listed {len(result['cycles'])} cycles")
    
    def test_02_create_test_cycle(self):
        """Should create a test cycle (sprint)."""
        teams = list_teams()
        team_id = teams["teams"][0]["id"]
        
        # Create a cycle for next week
        starts_at = datetime.now() + timedelta(days=7)
        ends_at = starts_at + timedelta(days=14)
        
        result = create_cycle(
            team_id=team_id,
            name=f"{TEST_PREFIX} Test Sprint",
            starts_at=starts_at.isoformat(),
            ends_at=ends_at.isoformat()
        )
        
        assert "cycle" in result
        assert result["cycle"]["name"] == f"{TEST_PREFIX} Test Sprint"
        print(f"✓ Created cycle: {result['cycle']['name']}")
    
    def test_03_get_cycle_details(self):
        """Should get detailed cycle information."""
        teams = list_teams()
        team_id = teams["teams"][0]["id"]
        
        cycles = list_cycles(team_id=team_id)
        test_cycle = next(
            (cycle for cycle in cycles["cycles"]
             if cycle["name"] == f"{TEST_PREFIX} Test Sprint"),
            None
        )
        
        if test_cycle:
            result = get_cycle(cycle_id=test_cycle["id"])
            assert result["cycle"]["id"] == test_cycle["id"]
            print(f"✓ Retrieved cycle: {result['cycle']['name']}")
    
    def test_04_update_cycle(self):
        """Should update a test cycle."""
        teams = list_teams()
        team_id = teams["teams"][0]["id"]
        
        cycles = list_cycles(team_id=team_id)
        test_cycle = next(
            (cycle for cycle in cycles["cycles"]
             if cycle["name"] == f"{TEST_PREFIX} Test Sprint"),
            None
        )
        
        if test_cycle:
            result = update_cycle(
                cycle_id=test_cycle["id"],
                name=f"{TEST_PREFIX} Test Sprint (Updated)"
            )
            
            assert result["cycle"]["name"] == f"{TEST_PREFIX} Test Sprint (Updated)"
            print(f"✓ Updated cycle: {result['cycle']['name']}")


class TestComments:
    """Integration tests for comment operations - creates visible test data."""
    
    def test_01_create_test_comment(self):
        """Should create a test comment on an issue."""
        issues = list_issues(limit=10)
        test_issue = next(
            (issue for issue in issues["issues"]
             if issue["title"].startswith(TEST_PREFIX)),
            None
        )
        
        if test_issue:
            result = create_comment(
                issue_id=test_issue["id"],
                body=(
                    f"{TEST_PREFIX} This is a test comment created by integration tests."
                    f"\n\n**Timestamp:** {datetime.now().isoformat()}"
                )
            )
            
            assert "comment" in result
            print(f"✓ Created comment on issue: {test_issue['identifier']}")
    
    def test_02_list_comments(self):
        """Should list comments on an issue."""
        issues = list_issues(limit=10)
        test_issue = next(
            (issue for issue in issues["issues"]
             if issue["title"].startswith(TEST_PREFIX)),
            None
        )
        
        if test_issue:
            result = list_comments(issue_id=test_issue["id"])
            assert "comments" in result
            print(f"✓ Listed {len(result['comments'])} comments on issue: {test_issue['identifier']}")
    
    def test_03_update_comment(self):
        """Should update a test comment."""
        issues = list_issues(limit=10)
        test_issue = next(
            (issue for issue in issues["issues"]
             if issue["title"].startswith(TEST_PREFIX)),
            None
        )
        
        if test_issue:
            comments = list_comments(issue_id=test_issue["id"])
            test_comment = next(
                (comment for comment in comments["comments"]
                 if TEST_PREFIX in comment["body"]),
                None
            )
            
            if test_comment:
                result = update_comment(
                    comment_id=test_comment["id"],
                    body=(
                        f"{TEST_PREFIX} This comment has been updated by integration tests."
                        f"\n\n**Updated:** {datetime.now().isoformat()}"
                    )
                )
                
                assert "comment" in result
                print(f"✓ Updated comment on issue: {test_issue['identifier']}")


class TestWebhooks:
    """Integration tests for webhook operations - creates visible test data."""
    
    def test_01_list_webhooks(self):
        """Should list all webhooks."""
        result = list_webhooks()
        assert "webhooks" in result
        print(f"✓ Listed {len(result['webhooks'])} webhooks")
    
    def test_02_create_test_webhook(self):
        """Should create a test webhook."""
        result = create_webhook(
            url="https://webhook.site/test-railcall-integration",
            enabled=True
        )
        
        assert "webhook" in result
        print(f"✓ Created webhook: {result['webhook']['url']}")
    
    def test_03_update_webhook(self):
        """Should update a test webhook."""
        webhooks = list_webhooks()
        test_webhook = next(
            (webhook for webhook in webhooks["webhooks"]
             if "railcall" in webhook["url"]),
            None
        )
        
        if test_webhook:
            result = update_webhook(
                webhook_id=test_webhook["id"],
                enabled=False
            )
            
            assert result["webhook"]["enabled"] is False
            print(f"✓ Disabled webhook: {test_webhook['url']}")


class TestMilestones:
    """Integration tests for milestone operations - creates visible test data."""
    
    def test_01_list_milestones(self):
        """Should list all milestones."""
        result = list_milestones()
        assert "milestones" in result
        print(f"✓ Listed {len(result['milestones'])} milestones")
    
    def test_02_create_test_milestone(self):
        """Should create a test milestone."""
        target_date = datetime.now() + timedelta(days=90)
        
        result = create_milestone(
            name=f"{TEST_PREFIX} Q4 2026 Release",
            description="Test milestone created by integration tests for Q4 2026 release planning.",
            target_date=target_date.strftime("%Y-%m-%d")
        )
        
        assert "milestone" in result
        assert result["milestone"]["name"] == f"{TEST_PREFIX} Q4 2026 Release"
        print(f"✓ Created milestone: {result['milestone']['name']}")
    
    def test_03_update_milestone(self):
        """Should update a test milestone."""
        milestones = list_milestones()
        test_milestone = next(
            (milestone for milestone in milestones["milestones"]
             if milestone["name"] == f"{TEST_PREFIX} Q4 2026 Release"),
            None
        )
        
        if test_milestone:
            result = update_milestone(
                milestone_id=test_milestone["id"],
                description=(
                    f"{TEST_PREFIX} Updated milestone description for Q4 2026 release."
                    f"\n\n**Updated:** {datetime.now().isoformat()}"
                )
            )
            
            assert "milestone" in result
            print(f"✓ Updated milestone: {test_milestone['name']}")


class TestCleanup:
    """Optional cleanup tests - run these manually if you want to remove test data."""
    
    @pytest.mark.skip(reason="Manual cleanup - uncomment to run")
    def test_cleanup_test_issues(self):
        """Delete all test issues."""
        issues = list_issues(limit=100)
        test_issues = [
            issue for issue in issues["issues"]
            if issue["title"].startswith(TEST_PREFIX)
        ]
        
        deleted_count = 0
        for issue in test_issues:
            try:
                delete_issue(issue_id=issue["id"])
                deleted_count += 1
            except Exception:
                pass
        
        print(f"✓ Deleted {deleted_count} test issues")
    
    @pytest.mark.skip(reason="Manual cleanup - uncomment to run")
    def test_cleanup_test_webhooks(self):
        """Delete all test webhooks."""
        webhooks = list_webhooks()
        test_webhooks = [
            webhook for webhook in webhooks["webhooks"]
            if "railcall" in webhook["url"]
        ]
        
        deleted_count = 0
        for webhook in test_webhooks:
            try:
                delete_webhook(webhook_id=webhook["id"])
                deleted_count += 1
            except Exception:
                pass
        
        print(f"✓ Deleted {deleted_count} test webhooks")
