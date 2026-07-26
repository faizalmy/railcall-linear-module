"""Comprehensive integration tests for Linear module - creates visible test data."""

import os
import pytest
from datetime import datetime, timedelta

# These tests have state dependencies (test_03 depends on test_02's created resource)
# so random ordering would break them. Disable pytest-randomly for this module.
pytest_plugins = ["pytest_randomly"]
pytestmark = [
    pytest.mark.randomly_disable,
]
from handlers.handler import (
    # Issues
    list_issues, get_issue, create_issue, update_issue, delete_issue,
    search_issues, bulk_update_issues, link_issues,
    # Teams
    list_teams, get_team,
    # Projects
    list_projects, get_project, create_project,
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

# Linear enforces uniqueness on label names and rejects overlapping cycles, so a
# re-run must not reuse the previous run's names.
RUN_ID = datetime.now().strftime("%m%d-%H%M%S")


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
        
        assert len(test_issue_ids) >= 3, (
            f"expected >=3 bulk-test issues from test_03, found {len(test_issue_ids)}"
        )
        
        result = bulk_update_issues(issue_ids=test_issue_ids[:3], priority=1)
        
        assert result["success_count"] == 3
        assert result["failure_count"] == 0
        assert result["rate_limited"] is False
        print(f"✓ Bulk updated {result['success_count']} issues to priority=1")
    
    def test_06_link_issues(self):
        """Should create relationships between test issues."""
        # Use search to find test issues (more reliable than list with limit)
        search_result = search_issues(query=TEST_PREFIX, limit=50)
        test_issues = [
            issue for issue in search_result["issues"]
            if issue["title"].startswith(TEST_PREFIX) and "Bulk Test" in issue["title"]
        ]
        
        assert len(test_issues) >= 2, f"need two test issues to link, found {len(test_issues)}"
        
        # Try to link, handling the case where issues might be trashed
        try:
            result = link_issues(
                issue_id=test_issues[0]["id"],
                related_issue_id=test_issues[1]["id"],
                relationship_type="blocks"
            )
            
            assert result["success"] is True
            assert result["relationship"] == "blocks"
            assert result["relation"]["type"] == "blocks"
            print(f"✓ Linked issues: {test_issues[0]['identifier']} blocks {test_issues[1]['identifier']}")
        except Exception as e:
            if "trashed" in str(e).lower():
                pytest.skip(f"Test issues are trashed: {e}")
            raise
    
    def test_07_get_issue_details(self):
        """Should retrieve detailed issue information."""
        issues = list_issues(limit=10)
        test_issue = next(
            (issue for issue in issues["issues"] 
             if issue["title"].startswith(TEST_PREFIX)),
            None
        )
        
        assert test_issue is not None, "no test issue found from the earlier tests"
        
        result = get_issue(issue_id=test_issue["id"])
        assert result["issue"]["id"] == test_issue["id"]
        assert result["issue"]["title"] == test_issue["title"]
        print(f"✓ Retrieved issue details: {result['issue']['identifier']}")
    
    def test_08_update_issue(self):
        """Should update a test issue."""
        issues = list_issues(limit=250)
        test_issue = next(
            (issue for issue in issues["issues"]
             if issue["title"] == f"{TEST_PREFIX} Integration Test Issue"),
            None
        )
        
        assert test_issue is not None, "issue created by test_02 not found"
        
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
    
    def test_02_create_test_project(self):
        """Should create a test project."""
        teams = list_teams()
        team_id = teams["teams"][0]["id"]
        
        project_name = f"{TEST_PREFIX} Project {RUN_ID}"
        result = create_project(
            team_ids=[team_id],
            name=project_name,
            description="Test project created by integration tests.",
            target_date=(datetime.now() + timedelta(days=120)).strftime("%Y-%m-%d"),
        )
        
        assert "project" in result
        assert result["project"]["name"] == project_name
        # targetDate is a TimelessDate - confirm it actually persisted
        assert result["project"]["targetDate"] is not None
        print(f"✓ Created project: {result['project']['name']}")
    
    def test_03_get_project_details(self):
        """Should get detailed project information."""
        projects = list_projects()
        assert len(projects["projects"]) > 0, "the previous test should have created a project"
        
        project_id = projects["projects"][0]["id"]
        result = get_project(project_id=project_id)
        assert "project" in result
        assert "targetDate" in result["project"]
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
        assert len(users["users"]) > 0, "workspace has no users"
        
        user_id = users["users"][0]["id"]
        result = get_user(user_id=user_id)
        assert result["user"]["id"] == user_id
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
        
        # Linear caps workflow state names at 30 characters
        result = create_state(
            team_id=team_id,
            name=f"RC Test State {RUN_ID}"[:30],
            color="#FF6B6B",
            state_type="backlog"
        )
        
        assert "state" in result
        assert result["state"]["name"] == f"RC Test State {RUN_ID}"[:30]
        print(f"✓ Created workflow state: {result['state']['name']}")
    
    def test_03_update_test_state(self):
        """Should update the test workflow state."""
        teams = list_teams()
        team_id = teams["teams"][0]["id"]
        
        states = list_states(team_id=team_id, limit=250)
        test_state = next(
            (state for state in states["states"]
             if state["name"] == f"RC Test State {RUN_ID}"[:30]),
            None
        )
        assert test_state is not None, "state created by the previous test not found"
        
        updated_name = f"RC State Upd {RUN_ID}"[:30]
        result = update_state(
            state_id=test_state["id"],
            name=updated_name,
            color="#4ECDC4"
        )
        
        assert result["state"]["name"] == updated_name
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
                name=f"{TEST_PREFIX} Label {i} {RUN_ID}",
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
        
        labels = list_labels(team_id=team_id, limit=250)
        test_label = next(
            (label for label in labels["labels"]
             if label["name"] == f"{TEST_PREFIX} Label 1 {RUN_ID}"),
            None
        )
        
        assert test_label is not None, "label created by the previous test not found"
        
        result = update_label(
            label_id=test_label["id"],
            name=f"{TEST_PREFIX} Label 1 Upd {RUN_ID}",
            color="#96CEB4"
        )
        
        assert result["label"]["name"] == f"{TEST_PREFIX} Label 1 Upd {RUN_ID}"
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
        
        # Push well past any existing cycle - Linear rejects overlapping ranges
        existing = list_cycles(team_id=team_id)["cycles"]
        latest_end = max(
            (datetime.fromisoformat(cycle["endsAt"].replace("Z", "+00:00")).replace(tzinfo=None)
             for cycle in existing if cycle.get("endsAt")),
            default=datetime.now(),
        )
        starts_at = max(latest_end, datetime.now()) + timedelta(days=7)
        ends_at = starts_at + timedelta(days=14)
        
        cycle_name = f"{TEST_PREFIX} Sprint {RUN_ID}"
        result = create_cycle(
            team_id=team_id,
            name=cycle_name,
            starts_at=starts_at.isoformat(),
            ends_at=ends_at.isoformat()
        )
        
        assert "cycle" in result
        assert result["cycle"]["name"] == cycle_name
        print(f"✓ Created cycle: {result['cycle']['name']}")
    
    def test_03_get_cycle_details(self):
        """Should get detailed cycle information."""
        teams = list_teams()
        team_id = teams["teams"][0]["id"]
        
        cycles = list_cycles(team_id=team_id)
        test_cycle = next(
            (cycle for cycle in cycles["cycles"]
             if cycle["name"] == f"{TEST_PREFIX} Sprint {RUN_ID}"),
            None
        )
        
        assert test_cycle is not None, "cycle created by the previous test not found"
        
        result = get_cycle(cycle_id=test_cycle["id"])
        assert result["cycle"]["id"] == test_cycle["id"]
        print(f"✓ Retrieved cycle: {result['cycle']['name']}")
    
    def test_04_update_cycle(self):
        """Should update a test cycle."""
        teams = list_teams()
        team_id = teams["teams"][0]["id"]
        
        cycles = list_cycles(team_id=team_id, limit=250)
        test_cycle = next(
            (cycle for cycle in cycles["cycles"]
             if cycle["name"] == f"{TEST_PREFIX} Sprint {RUN_ID}"),
            None
        )
        
        assert test_cycle is not None, "cycle created by test_02 not found"
        
        result = update_cycle(
            cycle_id=test_cycle["id"],
            name=f"{TEST_PREFIX} Sprint Upd {RUN_ID}"
        )
        
        assert result["cycle"]["name"] == f"{TEST_PREFIX} Sprint Upd {RUN_ID}"
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
        
        assert test_issue is not None, "no test issue to comment on"
        
        result = create_comment(
            issue_id=test_issue["id"],
            body=(
                f"{TEST_PREFIX} This is a test comment created by integration tests."
                f"\n\n**Timestamp:** {datetime.now().isoformat()}"
            )
        )
        
        assert result["comment"]["id"]
        assert TEST_PREFIX in result["comment"]["body"]
        print(f"✓ Created comment on issue: {test_issue['identifier']}")
    
    def test_02_list_comments(self):
        """Should list comments on an issue."""
        issues = list_issues(limit=250)
        test_issue = next(
            (issue for issue in issues["issues"]
             if issue["title"].startswith(TEST_PREFIX)),
            None
        )
        
        assert test_issue is not None, "no test issue to list comments on"
        
        result = list_comments(issue_id=test_issue["id"])
        assert result["count"] == len(result["comments"])
        assert any(TEST_PREFIX in c["body"] for c in result["comments"]), (
            "the comment created by the previous test is missing from the list"
        )
        print(f"✓ Listed {len(result['comments'])} comments on issue: {test_issue['identifier']}")
    
    def test_03_update_comment(self):
        """Should update a test comment."""
        issues = list_issues(limit=250)
        test_issue = next(
            (issue for issue in issues["issues"]
             if issue["title"].startswith(TEST_PREFIX)),
            None
        )
        
        assert test_issue is not None, "no test issue to update a comment on"
        
        comments = list_comments(issue_id=test_issue["id"])
        test_comment = next(
            (comment for comment in comments["comments"]
             if TEST_PREFIX in comment["body"]),
            None
        )
        assert test_comment is not None, "comment created by test_01 not found"
        
        new_body = (
            f"{TEST_PREFIX} This comment has been updated by integration tests."
            f"\n\n**Updated:** {datetime.now().isoformat()}"
        )
        result = update_comment(comment_id=test_comment["id"], body=new_body)
        
        assert result["comment"]["body"] == new_body
        print(f"✓ Updated comment on issue: {test_issue['identifier']}")


class TestCommentDeletion:
    """delete_comment, on a comment created solely to be deleted."""

    def test_01_delete_comment(self):
        """Should delete a comment and drop it from the issue's list."""
        issues = list_issues(limit=100)["issues"]
        test_issue = next(
            (issue for issue in issues if issue["title"].startswith(TEST_PREFIX)),
            None,
        )
        assert test_issue is not None, "no test issue to comment on"
        
        created = create_comment(
            issue_id=test_issue["id"],
            body=f"{TEST_PREFIX} Throwaway comment {RUN_ID} - deleted by the next assertion.",
        )
        comment_id = created["comment"]["id"]
        
        result = delete_comment(comment_id=comment_id)
        assert result["success"] is True
        
        remaining = [c["id"] for c in list_comments(issue_id=test_issue["id"])["comments"]]
        assert comment_id not in remaining
        print(f"✓ Deleted comment: {comment_id}")


class TestIssueDeletion:
    """delete_issue, on an issue created solely to be deleted."""

    def test_01_delete_issue(self):
        """Should delete an issue and drop it from the issue list."""
        teams = list_teams()
        team_id = teams["teams"][0]["id"]
        
        created = create_issue(
            team_id=team_id,
            title=f"{TEST_PREFIX} Throwaway Issue {RUN_ID}",
            description="Created by the integration suite purely to verify delete_issue.",
        )
        issue_id = created["issue"]["id"]
        
        result = delete_issue(issue_id=issue_id)
        assert result["success"] is True
        assert result["deleted_issue_id"] == issue_id
        
        remaining = [i["id"] for i in list_issues(limit=250)["issues"]]
        assert issue_id not in remaining
        print(f"✓ Deleted issue: {issue_id}")


class TestWebhooks:
    """Integration tests for webhook operations - creates visible test data."""

    URL = "https://webhook.site/test-railcall-integration"

    def test_01_list_webhooks(self):
        """Should list all webhooks."""
        result = list_webhooks()
        assert "webhooks" in result
        print(f"✓ Listed {len(result['webhooks'])} webhooks")
    
    def test_02_create_test_webhook(self):
        """Should create a test webhook.
        
        Linear enforces one webhook per URL per workspace, so a leftover from an
        earlier run is removed first. That also exercises delete_webhook.
        """
        stale = [
            webhook for webhook in list_webhooks()["webhooks"]
            if webhook["url"] == self.URL
        ]
        for webhook in stale:
            delete_webhook(webhook_id=webhook["id"])
            print(f"✓ Deleted stale webhook: {webhook['id']}")
        
        result = create_webhook(
            url=self.URL,
            resource_types=["Issue", "Comment"],
            label=f"{TEST_PREFIX} {RUN_ID}",
            all_public_teams=True,
            enabled=True
        )
        
        assert "webhook" in result
        assert result["webhook"]["url"] == self.URL
        print(f"✓ Created webhook: {result['webhook']['url']}")
    
    def test_03_update_webhook(self):
        """Should disable the test webhook."""
        webhooks = list_webhooks()
        test_webhook = next(
            (webhook for webhook in webhooks["webhooks"]
             if webhook["url"] == self.URL),
            None
        )
        assert test_webhook is not None, "webhook created by the previous test not found"
        
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
        """Should create a test milestone on a project."""
        projects = list_projects()["projects"]
        project = next(
            (p for p in projects if p["name"] == f"{TEST_PREFIX} Project {RUN_ID}"),
            projects[0] if projects else None,
        )
        assert project is not None, "no project available to attach a milestone to"
        
        target_date = datetime.now() + timedelta(days=90)
        milestone_name = f"{TEST_PREFIX} Release {RUN_ID}"
        
        result = create_milestone(
            project_id=project["id"],
            name=milestone_name,
            description="Test milestone created by integration tests.",
            target_date=target_date.strftime("%Y-%m-%d")
        )
        
        assert "milestone" in result
        assert result["milestone"]["name"] == milestone_name
        print(f"✓ Created milestone: {result['milestone']['name']}")
    
    def test_03_update_milestone(self):
        """Should update a test milestone."""
        milestones = list_milestones(limit=250)
        test_milestone = next(
            (milestone for milestone in milestones["milestones"]
             if milestone["name"] == f"{TEST_PREFIX} Release {RUN_ID}"),
            None
        )
        
        assert test_milestone is not None, "milestone created by the previous test not found"
        
        new_name = f"{TEST_PREFIX} Release {RUN_ID} Upd"
        result = update_milestone(
            milestone_id=test_milestone["id"],
            name=new_name,
            target_date=(datetime.now() + timedelta(days=120)).strftime("%Y-%m-%d"),
            description=(
                f"{TEST_PREFIX} Updated milestone description."
                f"\n\n**Updated:** {datetime.now().isoformat()}"
            )
        )
        
        assert result["milestone"]["name"] == new_name
        print(f"✓ Updated milestone: {result['milestone']['name']}")
