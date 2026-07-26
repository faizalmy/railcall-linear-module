"""Tests for the Linear GraphQL client's retry and rate-limit behavior."""

import os
from unittest.mock import Mock, patch

import pytest
import requests

from handlers.client import LinearClient
from handlers.utils.errors import (
    AuthenticationError,
    LinearError,
    NetworkError,
    NotFoundError,
    RateLimitError,
)


def _response(status_code=200, json_body=None, headers=None, text=""):
    response = Mock(spec=requests.Response)
    response.status_code = status_code
    response.headers = headers or {}
    response.text = text
    response.json.return_value = json_body if json_body is not None else {"data": {}}
    response.raise_for_status.return_value = None
    return response


@pytest.fixture
def client():
    with patch.dict(os.environ, {"LINEAR_API_KEY": "test_api_key"}):
        return LinearClient()


class TestRetryBudget:
    """The adapter must not stack urllib3 retries on top of the manual loop."""

    def test_adapter_does_not_retry(self, client):
        """Should leave retries entirely to execute()."""
        adapter = client.session.get_adapter("https://api.linear.app/graphql")
        assert adapter.max_retries.total == 0

    def test_network_failure_makes_exactly_max_retries_plus_one_attempts(self, client):
        """Should send 4 requests total, not 4 x 4."""
        with patch.object(client.session, "post") as post, patch("handlers.client.time.sleep"):
            post.side_effect = requests.exceptions.ConnectionError("boom")

            with pytest.raises(NetworkError):
                client.execute("query { viewer { id } }")

        assert post.call_count == client.MAX_RETRIES + 1

    def test_succeeds_after_a_transient_failure(self, client):
        """Should return data once a retry succeeds."""
        with patch.object(client.session, "post") as post, patch("handlers.client.time.sleep"):
            post.side_effect = [
                requests.exceptions.Timeout("slow"),
                _response(json_body={"data": {"viewer": {"id": "u1"}}}),
            ]

            result = client.execute("query { viewer { id } }")

        assert result == {"viewer": {"id": "u1"}}
        assert post.call_count == 2


class TestNonRetryableErrors:
    """Deterministic failures must fail fast instead of burning the budget."""

    def test_auth_error_is_not_retried(self, client):
        with patch.object(client.session, "post") as post, patch("handlers.client.time.sleep"):
            post.return_value = _response(status_code=401)

            with pytest.raises(AuthenticationError):
                client.execute("query { viewer { id } }")

        assert post.call_count == 1

    def test_client_error_is_not_retried(self, client):
        with patch.object(client.session, "post") as post, patch("handlers.client.time.sleep"):
            post.return_value = _response(status_code=400, text="bad request")

            with pytest.raises(LinearError):
                client.execute("query { viewer { id } }")

        assert post.call_count == 1

    def test_graphql_not_found_is_not_retried(self, client):
        body = {"errors": [{"message": "gone", "extensions": {"code": "NOT_FOUND"}}]}

        with patch.object(client.session, "post") as post, patch("handlers.client.time.sleep"):
            post.return_value = _response(json_body=body)

            with pytest.raises(NotFoundError):
                client.execute("query { issue { id } }")

        assert post.call_count == 1


class TestRateLimitHandling:
    """429 must be retried, and Retry-After must actually be honored."""

    def test_retry_after_drives_the_sleep(self, client):
        with patch.object(client.session, "post") as post, patch("handlers.client.time.sleep") as sleep:
            post.return_value = _response(status_code=429, headers={"Retry-After": "7"})

            with pytest.raises(RateLimitError):
                client.execute("query { viewer { id } }")

        assert post.call_count == client.MAX_RETRIES + 1
        assert [call.args[0] for call in sleep.call_args_list] == [7.0, 7.0, 7.0]

    def test_retry_after_is_capped(self, client):
        with patch.object(client.session, "post") as post, patch("handlers.client.time.sleep") as sleep:
            post.return_value = _response(status_code=429, headers={"Retry-After": "9999"})

            with pytest.raises(RateLimitError):
                client.execute("query { viewer { id } }")

        assert all(call.args[0] <= client.MAX_BACKOFF for call in sleep.call_args_list)

    def test_http_date_retry_after_falls_back_to_backoff(self, client):
        """Should not crash on the HTTP-date form of Retry-After."""
        headers = {"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"}

        with patch.object(client.session, "post") as post, patch("handlers.client.time.sleep") as sleep:
            post.return_value = _response(status_code=429, headers=headers)

            with pytest.raises(RateLimitError):
                client.execute("query { viewer { id } }")

        assert all(call.args[0] <= client.MAX_BACKOFF for call in sleep.call_args_list)

    def test_backoff_is_jittered_and_capped(self, client):
        """Should stay within [0, min(2**attempt, MAX_BACKOFF)]."""
        for attempt in range(6):
            window = min(client.RETRY_BACKOFF ** attempt, client.MAX_BACKOFF)
            wait = client._backoff_seconds(attempt)
            assert 0 <= wait <= window
