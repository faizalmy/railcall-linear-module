"""Tests for main handler functions."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from handlers.handler import (
    list_issues,
    get_issue,
    create_issue,
    update_issue,
    delete_issue,
    archive_issue,
    unarchive_issue,
    search_issues,
    bulk_update_issues,
    link_issues,
    list_teams,
    get_team,
    list_projects,
    get_project,
    create_project,
    create_project_update,
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
    list_initiatives,
    get_initiative,
    create_initiative,
    update_initiative,
    link_project_to_initiative,
    create_initiative_update,
)
from handlers.utils.errors import LinearError, RateLimitError, ValidationError


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
            "searchIssues": {
                "nodes": [{"id": "issue-1", "title": "Search Result"}],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
                "totalCount": 1,
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
        
        result = create_webhook(url="https://example.com", all_public_teams=True)
        assert result["webhook"]["url"] == "https://example.com"


class TestMilestoneCommands:
    """Test milestone-related commands."""
    
    @patch('handlers.handler.execute_query')
    def test_list_milestones_success(self, mock_query):
        """Should list milestones successfully."""
        mock_query.return_value = {
            "projectMilestones": {
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
            "projectMilestoneCreate": {
                "success": True,
                "projectMilestone": {"id": "milestone-1", "name": "v2.0"}
            }
        }
        
        result = create_milestone(
            project_id="123e4567-e89b-12d3-a456-426614174000",
            name="v2.0",
            target_date="2026-12-31T00:00:00Z"
        )
        assert result["milestone"]["name"] == "v2.0"


class TestGraphQLVariableShapes:
    """Regression tests: filters must be typed objects, not interpolated strings.

    Linear declares $filter as IssueFilter/WorkflowStateFilter/etc. Passing a
    string was silently accepted by the mocks but rejected by the real API.
    """

    @patch('handlers.handler.execute_query')
    def test_list_issues_sends_object_filter(self, mock_query):
        """Should send a nested dict filter, never a string."""
        mock_query.return_value = {
            "issues": {"nodes": [], "pageInfo": {"hasNextPage": False, "endCursor": None}}
        }

        list_issues(
            team_id="123e4567-e89b-12d3-a456-426614174000",
            state_id="123e4567-e89b-12d3-a456-426614174001",
            assignee_id="123e4567-e89b-12d3-a456-426614174002",
        )

        variables = mock_query.call_args[0][1]
        assert variables["filter"] == {
            "team": {"id": {"eq": "123e4567-e89b-12d3-a456-426614174000"}},
            "state": {"id": {"eq": "123e4567-e89b-12d3-a456-426614174001"}},
            "assignee": {"id": {"eq": "123e4567-e89b-12d3-a456-426614174002"}},
        }

    @patch('handlers.handler.execute_query')
    def test_list_issues_omits_filter_when_unfiltered(self, mock_query):
        """Should not send a null filter key when no filters are given."""
        mock_query.return_value = {
            "issues": {"nodes": [], "pageInfo": {"hasNextPage": False, "endCursor": None}}
        }

        list_issues()

        assert "filter" not in mock_query.call_args[0][1]

    @patch('handlers.handler.execute_query')
    def test_search_issues_sends_the_term_as_a_variable(self, mock_query):
        """The term travels as a typed variable, never interpolated into the query.

        searchIssues takes `term` and `teamId` natively - no IssueFilter is built.
        """
        mock_query.return_value = {
            "searchIssues": {
                "nodes": [], "pageInfo": {"hasNextPage": False, "endCursor": None},
                "totalCount": 0,
            }
        }

        search_issues(query='" } } bad { "', team_id="123e4567-e89b-12d3-a456-426614174000")

        variables = mock_query.call_args[0][1]
        assert variables["term"] == '" } } bad { "'
        assert variables["teamId"] == "123e4567-e89b-12d3-a456-426614174000"
        assert "filter" not in variables

    @patch('handlers.handler.execute_query')
    def test_search_includes_comments_by_default(self, mock_query):
        """This is what fixes the old title-only limitation."""
        mock_query.return_value = {
            "searchIssues": {
                "nodes": [], "pageInfo": {"hasNextPage": False, "endCursor": None},
                "totalCount": 0,
            }
        }

        search_issues(query="login")
        assert mock_query.call_args[0][1]["includeComments"] is True

        search_issues(query="login", include_comments=False)
        assert mock_query.call_args[0][1]["includeComments"] is False

    @patch('handlers.handler.execute_query')
    def test_search_issues_rejects_empty_query(self, mock_query):
        """Should reject a blank search rather than listing everything."""
        with pytest.raises(ValueError, match="query cannot be empty"):
            search_issues(query="   ")
        mock_query.assert_not_called()

    @patch('handlers.handler.execute_query')
    def test_list_states_filters_by_team(self, mock_query):
        """Should filter root workflowStates by team instead of returning []."""
        mock_query.return_value = {
            "workflowStates": {
                "nodes": [{"id": "state-1", "name": "Todo"}],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            }
        }

        result = list_states(team_id="123e4567-e89b-12d3-a456-426614174000")

        variables = mock_query.call_args[0][1]
        assert variables["filter"] == {"team": {"id": {"eq": "123e4567-e89b-12d3-a456-426614174000"}}}
        assert result["count"] == 1

    @patch('handlers.handler.execute_query')
    def test_list_labels_filters_by_team(self, mock_query):
        """Should filter root issueLabels by team instead of returning []."""
        mock_query.return_value = {
            "issueLabels": {
                "nodes": [{"id": "label-1", "name": "Bug"}],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            }
        }

        result = list_labels(team_id="123e4567-e89b-12d3-a456-426614174000")

        variables = mock_query.call_args[0][1]
        assert variables["filter"] == {"team": {"id": {"eq": "123e4567-e89b-12d3-a456-426614174000"}}}
        assert result["count"] == 1

    @patch('handlers.handler.execute_query')
    def test_list_cycles_filters_by_team(self, mock_query):
        """Should query root cycles with a team filter."""
        mock_query.return_value = {
            "cycles": {
                "nodes": [{"id": "cycle-1", "name": "Sprint 1"}],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            }
        }

        list_cycles(team_id="123e4567-e89b-12d3-a456-426614174000")

        variables = mock_query.call_args[0][1]
        assert variables["filter"] == {"team": {"id": {"eq": "123e4567-e89b-12d3-a456-426614174000"}}}


class TestLinkIssues:
    """Regression tests: linking must not clobber existing relations."""

    ISSUE_A = "123e4567-e89b-12d3-a456-426614174000"
    ISSUE_B = "123e4567-e89b-12d3-a456-426614174001"

    def _relation_response(self):
        return {
            "issueRelationCreate": {
                "success": True,
                "issueRelation": {"id": "rel-1", "type": "blocks"},
            }
        }

    @patch('handlers.handler.execute_query')
    def test_blocks_creates_relation(self, mock_query):
        """Should use issueRelationCreate, not an issueUpdate that overwrites."""
        mock_query.return_value = self._relation_response()

        result = link_issues(self.ISSUE_A, self.ISSUE_B, relationship_type="blocks")

        assert mock_query.call_count == 1
        variables = mock_query.call_args[0][1]
        assert variables["input"] == {
            "issueId": self.ISSUE_A,
            "relatedIssueId": self.ISSUE_B,
            "type": "blocks",
        }
        assert result["success"] is True

    @patch('handlers.handler.execute_query')
    def test_blocked_by_inverts_the_pair(self, mock_query):
        """Should express blocked_by as an inverted 'blocks' relation."""
        mock_query.return_value = self._relation_response()

        result = link_issues(self.ISSUE_A, self.ISSUE_B, relationship_type="blocked_by")

        assert mock_query.call_args[0][1]["input"] == {
            "issueId": self.ISSUE_B,
            "relatedIssueId": self.ISSUE_A,
            "type": "blocks",
        }
        assert result["relationship"] == "blocked_by"

    @patch('handlers.handler.execute_query')
    def test_related_is_not_a_silent_noop(self, mock_query):
        """Should send a real 'related' relation instead of an empty input."""
        mock_query.return_value = {
            "issueRelationCreate": {
                "success": True,
                "issueRelation": {"id": "rel-1", "type": "related"},
            }
        }

        link_issues(self.ISSUE_A, self.ISSUE_B, relationship_type="related")

        assert mock_query.call_args[0][1]["input"]["type"] == "related"

    @patch('handlers.handler.execute_query')
    def test_rejects_self_link(self, mock_query):
        """Should reject linking an issue to itself."""
        with pytest.raises(ValueError, match="itself"):
            link_issues(self.ISSUE_A, self.ISSUE_A)
        mock_query.assert_not_called()

    @patch('handlers.handler.execute_query')
    def test_raises_when_api_reports_failure(self, mock_query):
        """Should not report success when the mutation fails."""
        mock_query.return_value = {"issueRelationCreate": {"success": False}}

        with pytest.raises(ValueError, match="Failed to link issues"):
            link_issues(self.ISSUE_A, self.ISSUE_B)


class TestBulkUpdateRateLimit:
    """A batch must stop rather than hammer a closed rate-limit window."""

    IDS = [
        "123e4567-e89b-12d3-a456-42661417400{}".format(i) for i in range(4)
    ]
    STATE = "123e4567-e89b-12d3-a456-426614174009"

    @patch('handlers.handler.execute_query')
    def test_stops_and_reports_unattempted_ids(self, mock_query):
        """Should abandon the batch on 429 and name what was never tried."""
        ok = {"issueUpdate": {"success": True, "issue": {"id": "x"}}}
        mock_query.side_effect = [ok, ok, RateLimitError("Rate limit exceeded.")]

        result = bulk_update_issues(issue_ids=self.IDS, state_id=self.STATE)

        assert result["rate_limited"] is True
        assert result["success_count"] == 2
        assert result["not_attempted"] == self.IDS[2:]
        # Two successes, then it stops - the 4th ID is never sent
        assert mock_query.call_count == 3

    @patch('handlers.handler.execute_query')
    def test_one_bad_id_does_not_abort_the_batch(self, mock_query):
        """Should keep going past a per-issue failure."""
        ok = {"issueUpdate": {"success": True, "issue": {"id": "x"}}}
        mock_query.side_effect = [ok, LinearError("nope"), ok, ok]

        result = bulk_update_issues(issue_ids=self.IDS, state_id=self.STATE)

        assert result["rate_limited"] is False
        assert result["success_count"] == 3
        assert result["failure_count"] == 1


class TestAddedInputValidation:
    """Fields that previously reached the API unchecked."""

    TEAM = "123e4567-e89b-12d3-a456-426614174000"

    @patch('handlers.handler.execute_query')
    def test_create_label_rejects_bad_color(self, mock_query):
        with pytest.raises(ValidationError):
            create_label(team_id=self.TEAM, name="Bug", color="red")
        mock_query.assert_not_called()

    @patch('handlers.handler.execute_query')
    def test_create_state_rejects_blank_name(self, mock_query):
        with pytest.raises(ValidationError):
            create_state(team_id=self.TEAM, name="  ", color="#FF0000")
        mock_query.assert_not_called()

    @patch('handlers.handler.execute_query')
    def test_create_cycle_rejects_non_iso_dates(self, mock_query):
        with pytest.raises(ValidationError):
            create_cycle(team_id=self.TEAM, starts_at="01/01/2026", ends_at="14/01/2026")
        mock_query.assert_not_called()

    @patch('handlers.handler.execute_query')
    def test_create_cycle_rejects_inverted_range(self, mock_query):
        with pytest.raises(ValueError, match="earlier than"):
            create_cycle(
                team_id=self.TEAM,
                starts_at="2026-01-14T00:00:00Z",
                ends_at="2026-01-01T00:00:00Z",
            )
        mock_query.assert_not_called()

    @patch('handlers.handler.execute_query')
    def test_delete_comment_rejects_non_uuid(self, mock_query):
        with pytest.raises(ValidationError):
            delete_comment(comment_id="oops")
        mock_query.assert_not_called()

    @patch('handlers.handler.execute_query')
    def test_create_comment_rejects_blank_body(self, mock_query):
        with pytest.raises(ValidationError):
            create_comment(issue_id=self.TEAM, body="")
        mock_query.assert_not_called()

    @patch('handlers.handler.execute_query')
    def test_create_milestone_rejects_bad_date(self, mock_query):
        with pytest.raises(ValidationError):
            create_milestone(project_id=self.TEAM, name="v2.0", target_date="soon")
        mock_query.assert_not_called()


class TestCreateStateType:
    """Linear's WorkflowStateCreateInput does not accept 'triage'."""

    TEAM = "123e4567-e89b-12d3-a456-426614174000"

    @patch('handlers.handler.execute_query')
    def test_rejects_triage(self, mock_query):
        """Should reject the value Linear rejects, before the round trip."""
        with pytest.raises(ValueError, match="triage"):
            create_state(team_id=self.TEAM, name="Test", color="#FF0000", state_type="triage")
        mock_query.assert_not_called()

    @patch('handlers.handler.execute_query')
    def test_default_state_type_is_accepted_by_linear(self, mock_query):
        """The default must be a value the API actually allows."""
        mock_query.return_value = {
            "workflowStateCreate": {
                "success": True,
                "workflowState": {"id": "state-1", "name": "Test", "type": "backlog"},
            }
        }

        create_state(team_id=self.TEAM, name="Test", color="#FF0000")

        assert mock_query.call_args[0][1]["input"]["type"] == "backlog"


class TestSchemaShapes:
    """Shapes the real Linear API rejected before these were corrected."""

    PROJECT = "123e4567-e89b-12d3-a456-426614174000"
    ISSUE = "123e4567-e89b-12d3-a456-426614174001"

    @patch('handlers.handler.execute_query')
    def test_list_comments_sends_a_comment_filter(self, mock_query):
        """$issueId as String! landed in an ID position and 400'd."""
        mock_query.return_value = {
            "comments": {"nodes": [], "pageInfo": {"hasNextPage": False, "endCursor": None}}
        }

        list_comments(issue_id=self.ISSUE)

        variables = mock_query.call_args[0][1]
        assert "issueId" not in variables
        assert variables["filter"] == {"issue": {"id": {"eq": self.ISSUE}}}

    @patch('handlers.handler.execute_query')
    def test_create_webhook_sends_resource_types(self, mock_query):
        """resourceTypes is a required field of WebhookCreateInput."""
        mock_query.return_value = {
            "webhookCreate": {"success": True, "webhook": {"id": "wh-1", "url": "https://e.com"}}
        }

        create_webhook(url="https://e.com", all_public_teams=True)

        assert mock_query.call_args[0][1]["input"]["resourceTypes"] == ["Issue", "Comment"]

    @patch('handlers.handler.execute_query')
    def test_create_webhook_rejects_empty_resource_types(self, mock_query):
        with pytest.raises(ValidationError):
            create_webhook(url="https://e.com", resource_types=[], all_public_teams=True)
        mock_query.assert_not_called()

    @patch('handlers.handler.execute_query')
    def test_create_milestone_requires_a_project(self, mock_query):
        """Linear milestones are project-scoped; projectId is non-null."""
        mock_query.return_value = {
            "projectMilestoneCreate": {"success": True, "projectMilestone": {"id": "m-1"}}
        }

        create_milestone(project_id=self.PROJECT, name="v2.0", target_date="2026-12-31T00:00:00Z")

        input_data = mock_query.call_args[0][1]["input"]
        assert input_data["projectId"] == self.PROJECT
        # targetDate is a TimelessDate, not a datetime
        assert input_data["targetDate"] == "2026-12-31"

    @patch('handlers.handler.execute_query')
    def test_list_milestones_filters_by_project(self, mock_query):
        mock_query.return_value = {
            "projectMilestones": {"nodes": [], "pageInfo": {"hasNextPage": False, "endCursor": None}}
        }

        list_milestones(project_id=self.PROJECT)

        assert mock_query.call_args[0][1]["filter"] == {"project": {"id": {"eq": self.PROJECT}}}


class TestErrorMessages:
    """Linear hides the useful text in extensions.userPresentableMessage."""

    def test_prefers_user_presentable_message(self):
        from handlers.utils.errors import handle_graphql_errors

        response = {
            "errors": [{
                "message": "Argument Validation Error",
                "extensions": {
                    "code": "VALIDATION_ERROR",
                    "userPresentableMessage": "name must be shorter than or equal to 30 characters.",
                },
            }]
        }

        with pytest.raises(ValidationError, match="30 characters"):
            handle_graphql_errors(response)

    def test_falls_back_to_message(self):
        from handlers.utils.errors import handle_graphql_errors
        from handlers.utils.errors import LinearError

        response = {"errors": [{"message": "Something broke", "extensions": {}}]}

        with pytest.raises(LinearError, match="Something broke"):
            handle_graphql_errors(response)


class TestWebhookScope:
    """Linear requires a webhook to name either one team or all public teams."""

    TEAM = "123e4567-e89b-12d3-a456-426614174000"

    @patch('handlers.handler.execute_query')
    def test_rejects_no_scope(self, mock_query):
        with pytest.raises(ValueError, match="exactly one"):
            create_webhook(url="https://e.com")
        mock_query.assert_not_called()

    @patch('handlers.handler.execute_query')
    def test_rejects_both_scopes(self, mock_query):
        with pytest.raises(ValueError, match="exactly one"):
            create_webhook(url="https://e.com", team_id=self.TEAM, all_public_teams=True)
        mock_query.assert_not_called()

    @patch('handlers.handler.execute_query')
    def test_all_public_teams_scope(self, mock_query):
        mock_query.return_value = {
            "webhookCreate": {"success": True, "webhook": {"id": "wh-1", "url": "https://e.com"}}
        }

        create_webhook(url="https://e.com", all_public_teams=True)

        assert mock_query.call_args[0][1]["input"]["allPublicTeams"] is True

    @patch('handlers.handler.execute_query')
    def test_single_team_scope(self, mock_query):
        mock_query.return_value = {
            "webhookCreate": {"success": True, "webhook": {"id": "wh-1", "url": "https://e.com"}}
        }

        create_webhook(url="https://e.com", team_id=self.TEAM)

        input_data = mock_query.call_args[0][1]["input"]
        assert input_data["teamId"] == self.TEAM
        assert "allPublicTeams" not in input_data


class TestCreateProject:
    """ProjectCreateInput requires name and a non-empty teamIds list."""

    TEAM = "123e4567-e89b-12d3-a456-426614174000"
    USER = "123e4567-e89b-12d3-a456-426614174001"

    def _response(self):
        return {
            "projectCreate": {
                "success": True,
                "project": {"id": "proj-1", "name": "Apollo", "state": "planned"},
            }
        }

    @patch('handlers.handler.execute_query')
    def test_creates_with_minimum_fields(self, mock_query):
        mock_query.return_value = self._response()

        result = create_project(team_ids=[self.TEAM], name="Apollo")

        assert mock_query.call_args[0][1]["input"] == {"teamIds": [self.TEAM], "name": "Apollo"}
        assert result["project"]["name"] == "Apollo"

    @patch('handlers.handler.execute_query')
    def test_dates_are_truncated_to_timeless_dates(self, mock_query):
        """startDate/targetDate are TimelessDate, not datetimes."""
        mock_query.return_value = self._response()

        create_project(
            team_ids=[self.TEAM],
            name="Apollo",
            start_date="2026-08-01T00:00:00Z",
            target_date="2026-12-31",
        )

        input_data = mock_query.call_args[0][1]["input"]
        assert input_data["startDate"] == "2026-08-01"
        assert input_data["targetDate"] == "2026-12-31"

    @patch('handlers.handler.execute_query')
    def test_rejects_empty_team_ids(self, mock_query):
        with pytest.raises(ValueError, match="at least one team"):
            create_project(team_ids=[], name="Apollo")
        mock_query.assert_not_called()

    @patch('handlers.handler.execute_query')
    def test_rejects_blank_name(self, mock_query):
        with pytest.raises(ValidationError):
            create_project(team_ids=[self.TEAM], name="  ")
        mock_query.assert_not_called()

    @patch('handlers.handler.execute_query')
    def test_rejects_bad_team_id(self, mock_query):
        """A non-UUID is now read as a team name, so it fails at the lookup."""
        mock_query.return_value = {"teams": {"nodes": []}}

        with pytest.raises(ValueError, match="No team named 'not-a-uuid'"):
            create_project(team_ids=["not-a-uuid"], name="Apollo")

        # The lookup ran, but the project was never created.
        assert mock_query.call_count == 1

    @patch('handlers.handler.execute_query')
    def test_raises_when_api_reports_failure(self, mock_query):
        mock_query.return_value = {"projectCreate": {"success": False}}

        with pytest.raises(ValueError, match="Failed to create project"):
            create_project(team_ids=[self.TEAM], name="Apollo")

    @patch('handlers.handler.execute_query')
    def test_invalidates_the_project_list_cache(self, mock_query):
        """A stale list_projects must not survive a create."""
        from handlers.handler import list_projects

        mock_query.return_value = {
            "projects": {"nodes": [], "pageInfo": {"hasNextPage": False, "endCursor": None}}
        }
        list_projects()
        assert mock_query.call_count == 1

        mock_query.return_value = self._response()
        create_project(team_ids=[self.TEAM], name="Apollo")

        mock_query.return_value = {
            "projects": {
                "nodes": [{"id": "proj-1", "name": "Apollo"}],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            }
        }
        assert list_projects()["count"] == 1


class TestTeamIdDefault:
    """The Studio's credential form requires a team UUID next to the API key.

    Before this, that value was collected and never used - resolve_default_team_id()
    was dead code - while six commands demanded team_id as an argument. Now the
    saved team is the default, so the common single-team case does not paste the
    same UUID into every call.
    """

    TEAM = "123e4567-e89b-12d3-a456-426614174000"
    SAVED = "123e4567-e89b-12d3-a456-4266141749999"[:36]

    def _vault(self, team_id):
        from handlers import credentials
        entry = {"api_key": "k"}
        if team_id:
            entry["team_id"] = team_id
        return patch.dict(
            credentials.__dict__,
            {"__rc_helpers__": {"vault_get": lambda p: entry if p == "linear" else None}},
        )

    @patch('handlers.handler.execute_query')
    def test_create_issue_uses_the_saved_team(self, mock_query):
        mock_query.return_value = {
            "issueCreate": {"success": True, "issue": {"id": "i-1", "title": "x"}}
        }

        with self._vault(self.TEAM):
            create_issue(title="Fix login")

        assert mock_query.call_args[0][1]["input"]["teamId"] == self.TEAM

    @patch('handlers.handler.execute_query')
    def test_an_explicit_team_wins_over_the_saved_one(self, mock_query):
        explicit = "123e4567-e89b-12d3-a456-426614174001"
        mock_query.return_value = {
            "issueCreate": {"success": True, "issue": {"id": "i-1", "title": "x"}}
        }

        with self._vault(self.TEAM):
            create_issue(title="Fix login", team_id=explicit)

        assert mock_query.call_args[0][1]["input"]["teamId"] == explicit

    @patch('handlers.handler.execute_query')
    def test_no_team_anywhere_is_a_clear_error(self, mock_query):
        """Auto-detect queries teams; if 0 or >1 teams, raises ValueError."""
        mock_query.return_value = {"teams": {"nodes": []}}
        with self._vault(None):
            with pytest.raises(ValueError, match="No team_id given and none saved"):
                create_issue(title="Fix login")
        # Auto-detect called once to list teams
        mock_query.assert_called_once()

    @patch('handlers.handler.execute_query')
    def test_a_saved_team_is_still_validated(self, mock_query):
        """A non-UUID vault value is resolved as a name, and must resolve."""
        mock_query.return_value = {"teams": {"nodes": []}}

        with self._vault("not-a-uuid"):
            with pytest.raises(ValueError, match="No team named 'not-a-uuid'"):
                create_issue(title="Fix login")

        # Only the resolution attempt - no issue was created.
        assert mock_query.call_count == 1

    @patch('handlers.handler.execute_query')
    def test_every_team_scoped_command_accepts_the_default(self, mock_query):
        """All six that used to demand team_id now work without it."""
        responses = {
            "get_team": {"team": {"id": self.TEAM, "name": "Eng"}},
            "create_state": {"workflowStateCreate": {"success": True, "workflowState": {"id": "s"}}},
            "create_label": {"issueLabelCreate": {"success": True, "issueLabel": {"id": "l"}}},
            "list_cycles": {"cycles": {"nodes": [], "pageInfo": {"hasNextPage": False, "endCursor": None}}},
            "create_cycle": {"cycleCreate": {"success": True, "cycle": {"id": "c"}}},
        }
        calls = [
            ("get_team", get_team, {}),
            ("create_state", create_state, {"name": "Todo", "color": "#FF0000"}),
            ("create_label", create_label, {"name": "Bug", "color": "#FF0000"}),
            ("list_cycles", list_cycles, {}),
            ("create_cycle", create_cycle,
             {"starts_at": "2026-01-01", "ends_at": "2026-01-14"}),
        ]

        for name, fn, kwargs in calls:
            mock_query.return_value = responses[name]
            with self._vault(self.TEAM):
                fn(**kwargs)  # must not raise


class TestInitiativeCommands:
    """Initiatives are Linear's roadmap objects - `roadmap` is not in the schema."""

    INITIATIVE = "123e4567-e89b-12d3-a456-426614174000"
    PROJECT = "123e4567-e89b-12d3-a456-426614174001"
    USER = "123e4567-e89b-12d3-a456-426614174002"

    @patch('handlers.handler.execute_query')
    def test_list_filters_by_status(self, mock_query):
        mock_query.return_value = {
            "initiatives": {"nodes": [], "pageInfo": {"hasNextPage": False, "endCursor": None}}
        }

        list_initiatives(status="Active", limit=5)

        assert mock_query.call_args[0][1]["filter"] == {"status": {"eq": "Active"}}

    @patch('handlers.handler.execute_query')
    def test_list_rejects_an_unknown_status(self, mock_query):
        with pytest.raises(ValueError, match="status must be one of"):
            list_initiatives(status="Shipped")
        mock_query.assert_not_called()

    @patch('handlers.handler.execute_query')
    def test_get_requires_a_uuid(self, mock_query):
        with pytest.raises(ValidationError):
            get_initiative(initiative_id="nope")
        mock_query.assert_not_called()

    @patch('handlers.handler.execute_query')
    def test_create_sends_only_what_was_given(self, mock_query):
        mock_query.return_value = {
            "initiativeCreate": {"success": True, "initiative": {"id": "i-1", "name": "Q4"}}
        }

        create_initiative(name="Q4 platform")

        assert mock_query.call_args[0][1]["input"] == {"name": "Q4 platform"}

    @patch('handlers.handler.execute_query')
    def test_create_truncates_target_date_to_a_timeless_date(self, mock_query):
        """InitiativeCreateInput.targetDate is TimelessDate, not a datetime."""
        mock_query.return_value = {
            "initiativeCreate": {"success": True, "initiative": {"id": "i-1"}}
        }

        create_initiative(
            name="Q4", target_date="2026-12-31T23:59:59Z", status="Planned",
            owner_id=self.USER,
        )

        payload = mock_query.call_args[0][1]["input"]
        assert payload["targetDate"] == "2026-12-31"
        assert payload["status"] == "Planned"
        assert payload["ownerId"] == self.USER

    @patch('handlers.handler.execute_query')
    def test_create_rejects_an_unknown_status(self, mock_query):
        with pytest.raises(ValueError, match="status must be one of"):
            create_initiative(name="Q4", status="Done")
        mock_query.assert_not_called()

    @patch('handlers.handler.execute_query')
    def test_update_requires_at_least_one_field(self, mock_query):
        with pytest.raises(ValueError, match="No fields to update"):
            update_initiative(initiative_id=self.INITIATIVE)
        mock_query.assert_not_called()

    @patch('handlers.handler.execute_query')
    def test_link_project_sends_both_ids(self, mock_query):
        mock_query.return_value = {
            "initiativeToProjectCreate": {"success": True, "initiativeToProject": {"id": "l-1"}}
        }

        result = link_project_to_initiative(
            initiative_id=self.INITIATIVE, project_id=self.PROJECT
        )

        assert mock_query.call_args[0][1]["input"] == {
            "initiativeId": self.INITIATIVE,
            "projectId": self.PROJECT,
        }
        assert result["success"] is True

    @patch('handlers.handler.execute_query')
    def test_update_post_carries_health(self, mock_query):
        mock_query.return_value = {
            "initiativeUpdateCreate": {"success": True, "initiativeUpdate": {"id": "u-1"}}
        }

        create_initiative_update(
            initiative_id=self.INITIATIVE, body="On track for Q4", health="onTrack"
        )

        payload = mock_query.call_args[0][1]["input"]
        assert payload["health"] == "onTrack"
        assert payload["body"] == "On track for Q4"

    @patch('handlers.handler.execute_query')
    def test_update_post_rejects_unknown_health(self, mock_query):
        with pytest.raises(ValueError, match="health must be one of"):
            create_initiative_update(
                initiative_id=self.INITIATIVE, body="x", health="green"
            )
        mock_query.assert_not_called()

    @patch('handlers.handler.execute_query')
    def test_update_post_rejects_empty_body(self, mock_query):
        with pytest.raises(ValidationError):
            create_initiative_update(initiative_id=self.INITIATIVE, body="   ")
        mock_query.assert_not_called()

    @patch('handlers.handler.execute_query')
    def test_writes_invalidate_the_initiative_list(self, mock_query):
        mock_query.return_value = {
            "initiatives": {"nodes": [], "pageInfo": {"hasNextPage": False, "endCursor": None}}
        }
        list_initiatives()
        first = mock_query.call_count

        mock_query.return_value = {
            "initiativeCreate": {"success": True, "initiative": {"id": "i-1"}}
        }
        create_initiative(name="Q4")

        mock_query.return_value = {
            "initiatives": {
                "nodes": [{"id": "i-1", "name": "Q4"}],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            }
        }
        assert list_initiatives()["count"] == 1
        assert mock_query.call_count > first


class TestArchiveIssue:
    """Archiving is the reversible counterpart to delete_issue.

    Teams archive; permanent deletion is the rare case. Shipping only the rare
    one was the gap.
    """

    ISSUE = "123e4567-e89b-12d3-a456-426614174000"

    @patch('handlers.handler.execute_query')
    def test_archive_defaults_to_not_trashing(self, mock_query):
        mock_query.return_value = {"issueArchive": {"success": True}}

        result = archive_issue(issue_id=self.ISSUE)

        assert mock_query.call_args[0][1] == {"id": self.ISSUE, "trash": False}
        assert result["success"] is True
        assert result["trashed"] is False

    @patch('handlers.handler.execute_query')
    def test_archive_can_trash(self, mock_query):
        mock_query.return_value = {"issueArchive": {"success": True}}

        result = archive_issue(issue_id=self.ISSUE, trash=True)

        assert mock_query.call_args[0][1]["trash"] is True
        assert result["trashed"] is True

    @patch('handlers.handler.execute_query')
    def test_unarchive_restores(self, mock_query):
        mock_query.return_value = {"issueUnarchive": {"success": True}}

        result = unarchive_issue(issue_id=self.ISSUE)

        assert mock_query.call_args[0][1] == {"id": self.ISSUE}
        assert result["unarchived_issue_id"] == self.ISSUE

    @patch('handlers.handler.execute_query')
    def test_both_validate_the_id(self, mock_query):
        for fn in (archive_issue, unarchive_issue):
            with pytest.raises(ValidationError):
                fn(issue_id="not-a-uuid")
        mock_query.assert_not_called()

    @patch('handlers.handler.execute_query')
    def test_failure_is_not_reported_as_success(self, mock_query):
        mock_query.return_value = {"issueArchive": {"success": False}}

        with pytest.raises(ValueError, match="Failed to archive"):
            archive_issue(issue_id=self.ISSUE)


class TestProjectUpdate:
    """Projects use the same health vocabulary as initiatives."""

    PROJECT = "123e4567-e89b-12d3-a456-426614174000"

    @patch('handlers.handler.execute_query')
    def test_posts_body_and_health(self, mock_query):
        mock_query.return_value = {
            "projectUpdateCreate": {"success": True, "projectUpdate": {"id": "u-1"}}
        }

        create_project_update(
            project_id=self.PROJECT, body="Shipped the migration", health="atRisk"
        )

        payload = mock_query.call_args[0][1]["input"]
        assert payload == {
            "projectId": self.PROJECT,
            "body": "Shipped the migration",
            "health": "atRisk",
        }

    @patch('handlers.handler.execute_query')
    def test_health_is_optional(self, mock_query):
        mock_query.return_value = {
            "projectUpdateCreate": {"success": True, "projectUpdate": {"id": "u-1"}}
        }

        create_project_update(project_id=self.PROJECT, body="No health set")

        assert "health" not in mock_query.call_args[0][1]["input"]

    @patch('handlers.handler.execute_query')
    def test_rejects_unknown_health(self, mock_query):
        with pytest.raises(ValueError, match="health must be one of"):
            create_project_update(project_id=self.PROJECT, body="x", health="green")
        mock_query.assert_not_called()

    @patch('handlers.handler.execute_query')
    def test_rejects_empty_body(self, mock_query):
        with pytest.raises(ValidationError):
            create_project_update(project_id=self.PROJECT, body="  ")
        mock_query.assert_not_called()
