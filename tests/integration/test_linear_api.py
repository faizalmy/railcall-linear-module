"""Comprehensive integration tests for Linear module - creates visible test data."""

import os
import time
import pytest
from datetime import datetime, timedelta

# These tests have state dependencies (test_03 depends on test_02's created resource)
# so random ordering would break them. Deterministic order is enforced
# project-wide by `-p no:randomly` in pyproject.toml's addopts.
from handlers.handler import (
    # Issues
    list_issues, get_issue, create_issue, update_issue, delete_issue,
    archive_issue, unarchive_issue,
    search_issues, bulk_update_issues, link_issues,
    # Teams
    list_teams, get_team,
    # Projects
    list_projects, get_project, create_project, create_project_update,
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
    # Initiatives (Linear's roadmap)
    list_initiatives, get_initiative, create_initiative, update_initiative,
    link_project_to_initiative, create_initiative_update,
)


# Skip all tests if no API key is available
pytestmark = pytest.mark.skipif(
    not os.environ.get("LINEAR_API_KEY"),
    reason="LINEAR_API_KEY environment variable not set"
)


# Test data prefix for easy identification in Linear
TEST_PREFIX = "[RailCall Test]"

# Projects outlive the test that creates them - milestones and initiatives
# attach to them - so they are torn down at session end instead of inline.
_CREATED_PROJECTS = []

# Same for issues: TestIssueManagement creates in test_02/test_03 and reads them
# back in test_04 through test_08, so they cannot be deleted inline. Tracking
# the ids here is what lets the session leave the workspace as it found it.
_CREATED_ISSUES = []


def _track_issue(issue):
    """Register an issue for session teardown and hand it back."""
    _CREATED_ISSUES.append(issue["id"])
    return issue


# Linear enforces uniqueness on label names and rejects overlapping cycles, so a
# re-run must not reuse the previous run's names.
RUN_ID = datetime.now().strftime("%m%d-%H%M%S")


class TestIssueManagement:
    """Integration tests for issue operations.

    test_02 and test_03 create the issues the rest of the group reads back. They
    are handed down as class attributes rather than re-found by scanning
    list_issues: the scan matched on title, so it could pick up an issue from an
    earlier run - or miss its own once the workspace held enough data to push it
    out of the result window. Everything created here is deleted at session end.
    """

    integration_issue = None
    bulk_issue_ids = []

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
        TestIssueManagement.integration_issue = _track_issue(result["issue"])
        print(f"✓ Created issue: {result['issue']['identifier']}")

    def test_03_create_multiple_issues_for_bulk_test(self):
        """Should create multiple issues for bulk operations testing."""
        teams = list_teams()
        team_id = teams["teams"][0]["id"]

        created_issues = []
        for i in range(1, 4):
            result = create_issue(
                team_id=team_id,
                title=f"{TEST_PREFIX} Bulk Test Issue #{i} {RUN_ID}",
                description=f"This is test issue #{i} for bulk operations.",
                priority=3  # Medium
            )
            created_issues.append(_track_issue(result["issue"])["id"])

        assert len(created_issues) == 3
        TestIssueManagement.bulk_issue_ids = created_issues
        print("✓ Created 3 issues for bulk testing")

    def test_04_search_issues(self):
        """Should find the issues test_02 and test_03 just created.

        Linear's search index is eventually consistent, so a freshly created
        issue is not immediately findable. The poll waits for the index rather
        than asserting against whatever an earlier run happened to leave behind.
        """
        deadline = time.time() + 60
        while True:
            result = search_issues(query="RailCall Test", limit=25)
            assert "issues" in result
            if result["issues"] or time.time() > deadline:
                break
            time.sleep(3)

        assert len(result["issues"]) > 0, "search index did not catch up within 60s"
        print(f"✓ Found {len(result['issues'])} test issues via search")

    def test_05_bulk_update_issues(self):
        """Should bulk update the three issues test_03 created."""
        test_issue_ids = TestIssueManagement.bulk_issue_ids
        assert len(test_issue_ids) == 3, "test_03 did not hand down three issues"

        result = bulk_update_issues(issue_ids=test_issue_ids, priority=1)

        assert result["success_count"] == 3
        assert result["failure_count"] == 0
        assert result["rate_limited"] is False
        print(f"✓ Bulk updated {result['success_count']} issues to priority=1")
    
    def test_06_link_issues(self):
        """Should create relationships between two freshly created issues.

        This test owns its fixtures rather than scavenging issues left by
        earlier runs. Reusing leftovers made it flaky in two ways: a workspace
        with lots of accumulated test data pushed the ones it wanted out of the
        result window, and issues trashed by a previous cleanup were still
        returned by search but rejected by the link mutation. Creating the pair
        here means the assertions always run - no skip, no silent pass.
        """
        teams = list_teams()
        team_id = teams["teams"][0]["id"]

        blocker = create_issue(
            team_id=team_id,
            title=f"{TEST_PREFIX} Link Blocker {RUN_ID}",
            description="Created by test_06 to verify link_issues.",
        )["issue"]
        blocked = create_issue(
            team_id=team_id,
            title=f"{TEST_PREFIX} Link Blocked {RUN_ID}",
            description="Created by test_06 to verify link_issues.",
        )["issue"]

        try:
            result = link_issues(
                issue_id=blocker["id"],
                related_issue_id=blocked["id"],
                relationship_type="blocks",
            )

            assert result["success"] is True
            assert result["relationship"] == "blocks"
            assert result["relation"]["type"] == "blocks"
            assert result["relation"]["issue"]["id"] == blocker["id"]
            assert result["relation"]["relatedIssue"]["id"] == blocked["id"]
            print(f"✓ Linked issues: {blocker['identifier']} blocks {blocked['identifier']}")

            # blocked_by inverts the pair - Linear's enum has no such member.
            inverse = link_issues(
                issue_id=blocker["id"],
                related_issue_id=blocked["id"],
                relationship_type="blocked_by",
            )
            assert inverse["relation"]["issue"]["id"] == blocked["id"]
            assert inverse["relation"]["relatedIssue"]["id"] == blocker["id"]
            print(f"✓ Inverted: {blocked['identifier']} blocks {blocker['identifier']}")
        finally:
            # Always clean up, so a later run never inherits these.
            for issue in (blocker, blocked):
                try:
                    delete_issue(issue_id=issue["id"])
                except Exception:
                    pass
    
    def test_07_get_issue_details(self):
        """Should retrieve detailed issue information."""
        test_issue = TestIssueManagement.integration_issue
        assert test_issue is not None, "issue created by test_02 not handed down"

        result = get_issue(issue_id=test_issue["id"])
        assert result["issue"]["id"] == test_issue["id"]
        assert result["issue"]["title"] == test_issue["title"]
        print(f"✓ Retrieved issue details: {result['issue']['identifier']}")

    def test_08_update_issue(self):
        """Should update a test issue."""
        test_issue = TestIssueManagement.integration_issue
        assert test_issue is not None, "issue created by test_02 not handed down"

        result = update_issue(
            issue_id=test_issue["id"],
            title=f"{TEST_PREFIX} Integration Test Issue (Updated)",
            description="This issue has been updated by integration tests."
        )
        
        assert result["issue"]["title"] == f"{TEST_PREFIX} Integration Test Issue (Updated)"
        print(f"✓ Updated issue: {test_issue['identifier']}")

    def test_09_commands_accept_the_human_identifier(self):
        """ENG-123 must work everywhere the UUID does.

        The validator accepting both forms proves nothing on its own - what
        matters is that Linear resolves the identifier on each mutation, so
        this drives read, update, comment and archive through it. Owns its
        fixture: it archives, which would strand an issue the other tests read.
        """
        teams = list_teams()
        team_id = teams["teams"][0]["id"]

        issue = create_issue(
            team_id=team_id,
            title=f"{TEST_PREFIX} Identifier Path {RUN_ID}",
            description="Created by test_09 to drive commands by ENG-123.",
        )["issue"]
        identifier = issue["identifier"]

        try:
            fetched = get_issue(issue_id=identifier)
            assert fetched["issue"]["id"] == issue["id"]

            # Lowercase too - Linear matches the key case-insensitively.
            lowered = get_issue(issue_id=identifier.lower())
            assert lowered["issue"]["id"] == issue["id"]

            renamed = f"{TEST_PREFIX} Identifier Path {RUN_ID} (Updated)"
            updated = update_issue(issue_id=identifier, title=renamed)
            assert updated["issue"]["title"] == renamed
            assert updated["issue"]["id"] == issue["id"], "resolved a different issue"

            comment = create_comment(
                issue_id=identifier, body=f"{TEST_PREFIX} by identifier"
            )
            assert comment["comment"]["id"]

            archived = archive_issue(issue_id=identifier)
            assert archived["success"] is True
            unarchive_issue(issue_id=identifier)

            print(f"✓ get/update/comment/archive all accept {identifier}")
        finally:
            delete_issue(issue_id=issue["id"])


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

        # Registered for teardown; milestone and initiative tests use it first,
        # so it cannot be deleted inline here.
        _CREATED_PROJECTS.append(result["project"]["id"])
    
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
    
    def test_02_create_and_update_a_state(self):
        """Create a workflow state, update it, then archive it.

        Linear caps a team at 50 workflow statuses. Earlier revisions of this
        suite created one per run and never cleaned up, which eventually
        exhausted the quota and made create_state fail for everyone. This test
        owns its fixture end to end.
        """
        teams = list_teams()
        team_id = teams["teams"][0]["id"]

        # Linear caps workflow state names at 30 characters
        name = f"RC Test State {RUN_ID}"[:30]
        created = create_state(
            team_id=team_id,
            name=name,
            color="#FF6B6B",
            state_type="backlog",
        )["state"]
        state_id = created["id"]

        try:
            assert created["name"] == name
            print(f"✓ Created workflow state: {created['name']}")

            updated_name = f"RC State Upd {RUN_ID}"[:30]
            updated = update_state(
                state_id=state_id,
                name=updated_name,
                color="#4ECDC4",
            )["state"]
            assert updated["name"] == updated_name
            print(f"✓ Updated workflow state: {updated['name']}")
        finally:
            _archive_state(state_id)


class TestLabels:
    """Integration tests for label operations - creates visible test data."""
    
    def test_01_list_labels(self):
        """Should list all labels."""
        teams = list_teams()
        team_id = teams["teams"][0]["id"]
        
        result = list_labels(team_id=team_id)
        assert "labels" in result
        print(f"✓ Listed {len(result['labels'])} labels")
    
    def test_02_create_and_update_labels(self):
        """Create labels, update one, then delete them all.

        Earlier revisions left three labels behind per run; the workspace had
        accumulated well over a hundred before this was fixed.
        """
        teams = list_teams()
        team_id = teams["teams"][0]["id"]

        created = []
        for i, color in enumerate(["#FF6B6B", "#4ECDC4", "#45B7D1"], 1):
            created.append(create_label(
                team_id=team_id,
                name=f"{TEST_PREFIX} Label {i} {RUN_ID}",
                color=color,
                description=f"Test label {i} created by integration tests",
            )["label"])

        try:
            assert len(created) == 3
            print("✓ Created 3 test labels")

            updated_name = f"{TEST_PREFIX} Label 1 Upd {RUN_ID}"
            updated = update_label(
                label_id=created[0]["id"],
                name=updated_name,
                color="#96CEB4",
            )["label"]
            assert updated["name"] == updated_name
            print(f"✓ Updated label: {updated['name']}")
        finally:
            for label in created:
                _delete_label(label["id"])


class TestCycles:
    """Integration tests for cycle operations - creates visible test data."""
    
    def test_01_list_cycles(self):
        """Should list cycles for a team."""
        teams = list_teams()
        team_id = teams["teams"][0]["id"]
        
        result = list_cycles(team_id=team_id)
        assert "cycles" in result
        print(f"✓ Listed {len(result['cycles'])} cycles")
    
    def test_02_cycle_lifecycle(self):
        """Create a cycle, read it, update it, then archive it.

        Cycles were three separate tests chained by name lookup, each leaving
        the cycle behind. Collapsed into one lifecycle that owns its fixture:
        the workspace had 47 orphaned sprints before this.
        """
        teams = list_teams()
        team_id = teams["teams"][0]["id"]

        # Push well past any existing cycle - Linear rejects overlapping ranges
        existing = list_cycles(team_id=team_id, limit=250)["cycles"]
        latest_end = max(
            (datetime.fromisoformat(cycle["endsAt"].replace("Z", "+00:00")).replace(tzinfo=None)
             for cycle in existing if cycle.get("endsAt")),
            default=datetime.now(),
        )
        starts_at = max(latest_end, datetime.now()) + timedelta(days=7)
        ends_at = starts_at + timedelta(days=14)

        cycle_name = f"{TEST_PREFIX} Sprint {RUN_ID}"
        created = create_cycle(
            team_id=team_id,
            name=cycle_name,
            starts_at=starts_at.isoformat(),
            ends_at=ends_at.isoformat(),
        )["cycle"]
        cycle_id = created["id"]

        try:
            assert created["name"] == cycle_name
            print(f"✓ Created cycle: {created['name']}")

            fetched = get_cycle(cycle_id=cycle_id)["cycle"]
            assert fetched["id"] == cycle_id
            print(f"✓ Retrieved cycle: {fetched['name']}")

            updated_name = f"{TEST_PREFIX} Sprint Upd {RUN_ID}"
            updated = update_cycle(cycle_id=cycle_id, name=updated_name)["cycle"]
            assert updated["name"] == updated_name
            print(f"✓ Updated cycle: {updated['name']}")
        finally:
            _archive_cycle(cycle_id)


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


def _delete_label(label_id):
    """Remove a test label. Labels accumulate across runs otherwise."""
    from handlers.client import execute_query
    try:
        execute_query(
            "mutation($id: String!) { issueLabelDelete(id: $id) { success } }",
            {"id": label_id},
        )
    except Exception:
        pass


def _archive_cycle(cycle_id):
    """Remove a test cycle."""
    from handlers.client import execute_query
    try:
        execute_query(
            "mutation($id: String!) { cycleArchive(id: $id) { success } }",
            {"id": cycle_id},
        )
    except Exception:
        pass


def _delete_project(project_id):
    """Remove a test project."""
    from handlers.client import execute_query
    try:
        execute_query(
            "mutation($id: String!) { projectDelete(id: $id) { success } }",
            {"id": project_id},
        )
    except Exception:
        pass


def _archive_state(state_id):
    """Remove a test workflow state.

    There is no delete/archive_state command in this release, so the suite
    cleans up through the client. Workflow statuses are quota-limited (50 per
    team), so leaving them behind eventually breaks create_state.
    """
    from handlers.client import execute_query
    try:
        execute_query(
            "mutation($id: String!) { workflowStateArchive(id: $id) { success } }",
            {"id": state_id},
        )
    except Exception:
        pass


def _delete_initiative(initiative_id):
    """Remove a test initiative. There is no delete_initiative command in this
    release, so the suite cleans up through the client directly."""
    from handlers.client import execute_query
    execute_query(
        "mutation($id: String!) { initiativeDelete(id: $id) { success } }",
        {"id": initiative_id},
    )


class TestInitiatives:
    """Initiatives are Linear's roadmap. This group owns its fixtures.

    The workspace has no initiatives to scavenge, and leaving them behind would
    accumulate across runs, so each test creates what it needs and deletes it.
    """

    def test_01_list_initiatives(self):
        """Should list initiatives without error, even when there are none."""
        result = list_initiatives(limit=10)
        assert "initiatives" in result
        assert result["count"] == len(result["initiatives"])
        print(f"✓ Listed {result['count']} initiatives")

    def test_02_initiative_lifecycle(self):
        """create -> get -> update -> post an update -> delete."""
        name = f"{TEST_PREFIX} Roadmap {RUN_ID}"
        created = create_initiative(
            name=name,
            description="Created by the integration suite.",
            target_date="2026-12-31T00:00:00Z",
            status="Planned",
        )["initiative"]
        initiative_id = created["id"]

        try:
            assert created["name"] == name
            # targetDate is a TimelessDate - the datetime must have been truncated
            assert created["targetDate"] == "2026-12-31"
            assert created["status"] == "Planned"
            print(f"✓ Created initiative: {created['name']}")

            fetched = get_initiative(initiative_id=initiative_id)["initiative"]
            assert fetched["id"] == initiative_id
            assert "projects" in fetched

            updated = update_initiative(
                initiative_id=initiative_id,
                name=f"{name} (Updated)",
                status="Active",
            )["initiative"]
            assert updated["name"] == f"{name} (Updated)"
            assert updated["status"] == "Active"
            print(f"✓ Updated initiative -> status {updated['status']}")

            posted = create_initiative_update(
                initiative_id=initiative_id,
                body=f"{TEST_PREFIX} health check",
                health="onTrack",
            )["update"]
            assert posted["health"] == "onTrack"
            print(f"✓ Posted initiative update: health={posted['health']}")
        finally:
            _delete_initiative(initiative_id)

    def test_03_link_project_to_initiative(self):
        """A project rolled up under an initiative is what makes it a roadmap."""
        projects = list_projects()["projects"]
        if not projects:
            pytest.skip("workspace has no project to roll up")

        created = create_initiative(name=f"{TEST_PREFIX} Rollup {RUN_ID}")["initiative"]
        initiative_id = created["id"]

        try:
            result = link_project_to_initiative(
                initiative_id=initiative_id, project_id=projects[0]["id"]
            )
            assert result["success"] is True
            assert result["link"]["project"]["id"] == projects[0]["id"]

            fetched = get_initiative(initiative_id=initiative_id)["initiative"]
            linked = [p["id"] for p in fetched["projects"]["nodes"]]
            assert projects[0]["id"] in linked
            print(f"✓ Linked project {projects[0]['name']} to the initiative")
        finally:
            _delete_initiative(initiative_id)

    def test_04_rejects_an_unknown_status(self):
        """The enum guard runs before the API call."""
        with pytest.raises(ValueError, match="status must be one of"):
            create_initiative(name="x", status="Shipped")


class TestArchiveAndSearch:
    """The v0.2.6 additions, against the real API."""

    def test_01_archive_then_unarchive(self):
        """Archiving removes an issue from the active list; unarchiving restores it."""
        team_id = list_teams()["teams"][0]["id"]
        issue = create_issue(
            title=f"{TEST_PREFIX} Archive round-trip {RUN_ID}",
            team_id=team_id,
        )["issue"]

        try:
            archived = archive_issue(issue_id=issue["id"])
            assert archived["success"] is True
            assert archived["trashed"] is False

            active = [i["id"] for i in list_issues(limit=250)["issues"]]
            assert issue["id"] not in active, "archived issue still in the active list"
            print(f"✓ Archived {issue['identifier']} - gone from list_issues")

            restored = unarchive_issue(issue_id=issue["id"])
            assert restored["success"] is True

            active = [i["id"] for i in list_issues(limit=250)["issues"]]
            assert issue["id"] in active, "unarchived issue did not come back"
            print(f"✓ Unarchived {issue['identifier']} - back in list_issues")
        finally:
            try:
                delete_issue(issue_id=issue["id"])
            except Exception:
                pass

    def test_02_search_reaches_beyond_titles(self):
        """The whole point of moving to searchIssues.

        Creates an issue whose distinctive term appears ONLY in the description,
        so a title-only match could not find it.
        """
        team_id = list_teams()["teams"][0]["id"]
        needle = f"zzsearchprobe{RUN_ID}".replace("-", "")
        issue = create_issue(
            title=f"{TEST_PREFIX} Search probe {RUN_ID}",
            team_id=team_id,
            description=f"This body contains {needle} and the title does not.",
        )["issue"]

        try:
            # Linear's search index is eventually consistent - a freshly created
            # issue is sometimes searchable in under a second and sometimes not
            # for tens of seconds. Poll rather than race it; the assertion is
            # unchanged, only the patience is.
            deadline = time.time() + 60
            ids = []
            while time.time() < deadline:
                ids = [i["id"] for i in search_issues(query=needle, limit=10)["issues"]]
                if issue["id"] in ids:
                    break
                time.sleep(3)

            assert issue["id"] in ids, (
                "searchIssues did not match a term present only in the "
                "description within 60s"
            )
            print(f"✓ Found {issue['identifier']} by a description-only term")
        finally:
            try:
                delete_issue(issue_id=issue["id"])
            except Exception:
                pass

    def test_03_create_project_update(self):
        """Projects carry the same health updates as initiatives."""
        projects = list_projects()["projects"]
        if not projects:
            pytest.skip("workspace has no project to post an update against")

        result = create_project_update(
            project_id=projects[0]["id"],
            body=f"{TEST_PREFIX} status {RUN_ID}",
            health="onTrack",
        )["update"]

        assert result["health"] == "onTrack"
        assert TEST_PREFIX in result["body"]
        print(f"✓ Posted project update: health={result['health']}")


@pytest.fixture(scope="session", autouse=True)
def _teardown_created_objects():
    """Remove what this session created, once everything that uses it is done.

    Issues and projects are read back by tests other than the one that created
    them, so neither can be deleted inline. Running the suite must not grow the
    workspace: leftovers made assertions pass against stale data, and workflow
    statuses are quota-limited outright.
    """
    yield
    for issue_id in _CREATED_ISSUES:
        try:
            delete_issue(issue_id=issue_id)
        except Exception:
            pass
    for project_id in _CREATED_PROJECTS:
        _delete_project(project_id)
