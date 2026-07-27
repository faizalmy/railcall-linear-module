"""Pytest configuration and fixtures."""

import os
import pytest
from unittest.mock import Mock, patch


@pytest.fixture(autouse=True)
def clear_cache():
    """Reset the cache between tests.

    Metadata reads (list_teams, get_user, ...) are cached, so without this a
    result stored by one test would be served to the next and the mocked
    execute_query would never be called.
    """
    from handlers.cache import get_cache

    get_cache().clear()
    yield
    get_cache().clear()


@pytest.fixture
def mock_env():
    """Mock environment variables."""
    with patch.dict(os.environ, {
        'LINEAR_API_KEY': 'test_api_key',
        'RAILCALL_MODULE_NAME': 'linear',
        'RAILCALL_MODULE_VERSION': '0.2.6',
    }):
        yield


@pytest.fixture
def mock_linear_client():
    """Mock Linear GraphQL client."""
    with patch('handlers.client.execute_query') as mock:
        yield mock


@pytest.fixture
def sample_team():
    """Sample team data."""
    return {
        'id': 'team-123',
        'name': 'Engineering',
        'key': 'ENG',
    }


@pytest.fixture
def sample_issue():
    """Sample issue data."""
    return {
        'id': 'issue-456',
        'identifier': 'ENG-123',
        'title': 'Test Issue',
        'description': 'Test description',
        'priority': 2,
        'state': {
            'id': 'state-789',
            'name': 'In Progress',
        },
        'assignee': {
            'id': 'user-012',
            'name': 'John Doe',
        },
        'team': {
            'id': 'team-123',
            'name': 'Engineering',
        },
    }


@pytest.fixture
def sample_user():
    """Sample user data."""
    return {
        'id': 'user-012',
        'name': 'John Doe',
        'email': 'john@example.com',
    }


@pytest.fixture
def sample_project():
    """Sample project data."""
    return {
        'id': 'project-345',
        'name': 'Test Project',
        'description': 'Test project description',
        'state': 'active',
    }
