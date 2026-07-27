"""Tests for the Linear GraphQL client's transport, retry and rate-limit behavior.

Transport is stdlib urllib only - no `requests`. Everything here mocks
`urllib.request.urlopen`, which is the single seam the client goes through.
"""

import json
import os
import urllib.error
from unittest.mock import Mock, patch

import pytest

from handlers.client import LinearClient
from handlers.utils.errors import (
    AuthenticationError,
    LinearError,
    NetworkError,
    NotFoundError,
    RateLimitError,
)

QUERY = "query { viewer { id } }"
MUTATION = "mutation($input: IssueCreateInput!) { issueCreate(input: $input) { success } }"


def _ok(status=200, json_body=None, headers=None, text=""):
    """A urlopen context manager yielding a successful response."""
    body = json.dumps(json_body if json_body is not None else {"data": {}}).encode()
    if text:
        body = text.encode()

    response = Mock()
    response.getcode.return_value = status
    response.read.return_value = body
    response.headers = headers or {}

    ctx = Mock()
    ctx.__enter__ = Mock(return_value=response)
    ctx.__exit__ = Mock(return_value=False)
    return ctx


def _http_error(code, headers=None, body=b""):
    """urllib raises on 4xx/5xx; _post turns it back into a _Response."""
    error = urllib.error.HTTPError(
        url="https://api.linear.app/graphql",
        code=code,
        msg="error",
        hdrs=headers or {},
        fp=None,
    )
    error.read = Mock(return_value=body)
    return error


@pytest.fixture
def client():
    with patch.dict(os.environ, {"LINEAR_API_KEY": "test_api_key"}):
        return LinearClient()


class TestTransport:
    """One stdlib transport, no third-party dependency."""

    def test_client_has_no_requests_session(self, client):
        assert not hasattr(client, "session")

    def test_successful_request_returns_data(self, client):
        with patch("handlers.client.urllib.request.urlopen") as urlopen:
            urlopen.return_value = _ok(json_body={"data": {"viewer": {"id": "u1"}}})
            assert client.execute(QUERY) == {"viewer": {"id": "u1"}}


class TestMutationRetrySafety:
    """Linear has no idempotency key: retrying an accepted mutation duplicates it.

    A 429 or timeout can arrive after the server already applied the write, so a
    mutation gets exactly one attempt and recovery is a fresh airlock approval.
    """

    def test_is_mutation_classifies_correctly(self):
        assert LinearClient.is_mutation(MUTATION) is True
        assert LinearClient.is_mutation(QUERY) is False
        assert LinearClient.is_mutation("\n  mutation Foo { x }") is True

    def test_mutation_is_not_retried_on_rate_limit(self, client):
        with patch("handlers.client.urllib.request.urlopen") as urlopen, \
             patch("handlers.client.time.sleep") as sleep:
            urlopen.side_effect = _http_error(429, {"Retry-After": "5"})

            with pytest.raises(RateLimitError):
                client.execute(MUTATION)

        assert urlopen.call_count == 1, "a retried mutation can duplicate the write"
        sleep.assert_not_called()

    def test_mutation_is_not_retried_on_network_error(self, client):
        """A timeout may mean Linear applied the write and the reply was lost."""
        with patch("handlers.client.urllib.request.urlopen") as urlopen, \
             patch("handlers.client.time.sleep") as sleep:
            urlopen.side_effect = urllib.error.URLError("connection reset")

            with pytest.raises(NetworkError):
                client.execute(MUTATION)

        assert urlopen.call_count == 1
        sleep.assert_not_called()

    def test_mutation_is_not_retried_on_5xx(self, client):
        with patch("handlers.client.urllib.request.urlopen") as urlopen, \
             patch("handlers.client.time.sleep"):
            urlopen.side_effect = _http_error(503)

            with pytest.raises(NetworkError):
                client.execute(MUTATION)

        assert urlopen.call_count == 1

    def test_mutation_error_keeps_retry_after_for_the_caller(self, client):
        """bulk_update_issues surfaces this so a human can re-approve later."""
        with patch("handlers.client.urllib.request.urlopen") as urlopen, \
             patch("handlers.client.time.sleep"):
            urlopen.side_effect = _http_error(429, {"Retry-After": "12"})

            with pytest.raises(RateLimitError) as excinfo:
                client.execute(MUTATION)

        assert excinfo.value.details.get("retry_after") == 12.0

    def test_a_successful_mutation_still_returns_data(self, client):
        with patch("handlers.client.urllib.request.urlopen") as urlopen:
            urlopen.return_value = _ok(
                json_body={"data": {"issueCreate": {"success": True}}}
            )
            assert client.execute(MUTATION) == {"issueCreate": {"success": True}}

    def test_mutate_alias_gets_the_same_protection(self, client):
        """mutate() delegates to execute(), so detection covers it too."""
        with patch("handlers.client.urllib.request.urlopen") as urlopen, \
             patch("handlers.client.time.sleep"):
            urlopen.side_effect = _http_error(429)

            with pytest.raises(RateLimitError):
                client.mutate(MUTATION)

        assert urlopen.call_count == 1


class TestQueryRetryBudget:
    """Reads are safe to replay, so they keep the full retry budget."""

    def test_network_failure_makes_exactly_max_retries_plus_one_attempts(self, client):
        with patch("handlers.client.urllib.request.urlopen") as urlopen, \
             patch("handlers.client.time.sleep"):
            urlopen.side_effect = urllib.error.URLError("boom")

            with pytest.raises(NetworkError):
                client.execute(QUERY)

        assert urlopen.call_count == client.MAX_RETRIES + 1

    def test_succeeds_after_a_transient_failure(self, client):
        with patch("handlers.client.urllib.request.urlopen") as urlopen, \
             patch("handlers.client.time.sleep"):
            urlopen.side_effect = [
                urllib.error.URLError("slow"),
                _ok(json_body={"data": {"viewer": {"id": "u1"}}}),
            ]

            assert client.execute(QUERY) == {"viewer": {"id": "u1"}}
        assert urlopen.call_count == 2


class TestAuthHeaders:
    def test_valid_api_key_sends_authorization_header(self, client):
        with patch("handlers.client.urllib.request.urlopen") as urlopen:
            urlopen.return_value = _ok()
            client._post({"query": "q"}, timeout=5)

        request = urlopen.call_args.args[0]
        assert request.get_header("Authorization") == "test_api_key"

    def test_empty_api_key_sends_empty_authorization_header(self):
        with patch.dict(os.environ, {"LINEAR_API_KEY": "seed"}):
            client = LinearClient()
        client.api_key = ""

        with patch("handlers.client.urllib.request.urlopen") as urlopen:
            urlopen.return_value = _ok()
            client._post({"query": "q"}, timeout=5)

        request = urlopen.call_args.args[0]
        assert request.get_header("Authorization") == ""

    def test_missing_credential_raises_before_any_request(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(AuthenticationError):
                LinearClient()


class TestNonRetryableErrors:
    """Deterministic failures fail fast instead of burning the budget."""

    def test_auth_error_is_not_retried(self, client):
        with patch("handlers.client.urllib.request.urlopen") as urlopen, \
             patch("handlers.client.time.sleep"):
            urlopen.side_effect = _http_error(401)

            with pytest.raises(AuthenticationError):
                client.execute(QUERY)

        assert urlopen.call_count == 1

    def test_client_error_is_not_retried(self, client):
        with patch("handlers.client.urllib.request.urlopen") as urlopen, \
             patch("handlers.client.time.sleep"):
            urlopen.side_effect = _http_error(400, body=b"bad request")

            with pytest.raises(LinearError):
                client.execute(QUERY)

        assert urlopen.call_count == 1

    def test_graphql_not_found_is_not_retried(self, client):
        body = {"errors": [{"message": "gone", "extensions": {"code": "NOT_FOUND"}}]}

        with patch("handlers.client.urllib.request.urlopen") as urlopen, \
             patch("handlers.client.time.sleep"):
            urlopen.return_value = _ok(json_body=body)

            with pytest.raises(NotFoundError):
                client.execute("query { issue { id } }")

        assert urlopen.call_count == 1


class TestRateLimitHandling:
    """429 on a read is retried, and Retry-After is honored."""

    def test_retry_after_drives_the_sleep(self, client):
        with patch("handlers.client.urllib.request.urlopen") as urlopen, \
             patch("handlers.client.time.sleep") as sleep:
            urlopen.side_effect = _http_error(429, {"Retry-After": "7"})

            with pytest.raises(RateLimitError):
                client.execute(QUERY)

        assert urlopen.call_count == client.MAX_RETRIES + 1
        assert [call.args[0] for call in sleep.call_args_list] == [7.0, 7.0, 7.0]

    def test_retry_after_is_capped(self, client):
        with patch("handlers.client.urllib.request.urlopen") as urlopen, \
             patch("handlers.client.time.sleep") as sleep:
            urlopen.side_effect = _http_error(429, {"Retry-After": "9999"})

            with pytest.raises(RateLimitError):
                client.execute(QUERY)

        assert all(call.args[0] <= client.MAX_BACKOFF for call in sleep.call_args_list)

    def test_http_date_retry_after_falls_back_to_backoff(self, client):
        headers = {"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"}

        with patch("handlers.client.urllib.request.urlopen") as urlopen, \
             patch("handlers.client.time.sleep") as sleep:
            urlopen.side_effect = _http_error(429, headers)

            with pytest.raises(RateLimitError):
                client.execute(QUERY)

        assert all(call.args[0] <= client.MAX_BACKOFF for call in sleep.call_args_list)

    def test_backoff_is_jittered_and_capped(self, client):
        for attempt in range(6):
            window = min(client.RETRY_BACKOFF ** attempt, client.MAX_BACKOFF)
            assert 0 <= client._backoff_seconds(attempt) <= window


class TestAuthErrorMessages:
    """A 401 must name the credential store that actually applies.

    Pointing a Studio operator at LINEAR_API_KEY would send them somewhere the
    Studio never reads - and a stray env-var mention also reads like env-based
    auth to anyone grepping the published bundle.
    """

    def _install_helpers(self, vault):
        from handlers import credentials
        return patch.dict(
            credentials.__dict__,
            {"__rc_helpers__": {"vault_get": lambda p: vault.get(p)}},
        )

    def test_401_in_studio_points_at_the_vault(self):
        vault = {"linear": {"api_key": "revoked_key"}}

        with self._install_helpers(vault):
            client = LinearClient()
            with patch("handlers.client.urllib.request.urlopen") as urlopen, \
                 patch("handlers.client.time.sleep"):
                urlopen.side_effect = _http_error(401)

                with pytest.raises(AuthenticationError) as excinfo:
                    client.execute(QUERY)

        message = str(excinfo.value)
        assert "vault" in message
        assert "LINEAR_API_KEY" not in message

    def test_401_standalone_points_at_the_environment(self):
        with patch.dict(os.environ, {"LINEAR_API_KEY": "revoked_key"}):
            client = LinearClient()
            with patch("handlers.client.urllib.request.urlopen") as urlopen, \
                 patch("handlers.client.time.sleep"):
                urlopen.side_effect = _http_error(401)

                with pytest.raises(AuthenticationError) as excinfo:
                    client.execute(QUERY)

        message = str(excinfo.value)
        assert "LINEAR_API_KEY" in message
        assert "vault" not in message

    def test_missing_credential_in_studio_points_at_the_vault(self):
        """The construction-time branch, same rule."""
        with self._install_helpers({}):
            with pytest.raises(AuthenticationError) as excinfo:
                LinearClient()

        assert "vault" in str(excinfo.value)
