"""Tests for credential resolution.

The rule the RailCall review asked for: inside the Studio the station vault is
the ONLY source. Process environment is readable via `ps auxe` and lands in core
dumps, so falling back to it there would defeat the vault the operator
configured. Outside the Studio there is no vault, so LINEAR_API_KEY is the
supported source for library use and the test suite.
"""

import os
from unittest.mock import patch

import pytest

from handlers import credentials


@pytest.fixture
def in_studio():
    """Install a fake __rc_helpers__, the way the Studio loader does."""
    vault = {}

    def vault_get(provider):
        return vault.get(provider)

    with patch.dict(
        credentials.__dict__,
        {"__rc_helpers__": {"vault_get": vault_get}},
    ):
        yield vault


class TestInsideStudio:
    """Helpers present means the Studio is hosting us."""

    def test_reads_the_key_from_the_vault(self, in_studio):
        in_studio["linear"] = {"api_key": "vault_key"}

        with patch.dict(os.environ, {"LINEAR_API_KEY": "env_key"}):
            assert credentials.resolve_api_key() == "vault_key"

    def test_environment_is_never_read(self, in_studio):
        """The bypass the reviewer flagged: env must not rescue a missing vault."""
        with patch.dict(os.environ, {"LINEAR_API_KEY": "env_key"}):
            assert credentials.resolve_api_key() is None

    def test_blank_vault_value_is_not_a_credential(self, in_studio):
        in_studio["linear"] = {"api_key": "   "}

        with patch.dict(os.environ, {"LINEAR_API_KEY": "env_key"}):
            assert credentials.resolve_api_key() is None

    def test_team_id_follows_the_same_rule(self, in_studio):
        in_studio["linear"] = {"api_key": "k", "team_id": "vault_team"}

        with patch.dict(os.environ, {"LINEAR_TEAM_ID": "env_team"}):
            assert credentials.resolve_default_team_id() == "vault_team"

    def test_team_id_does_not_fall_back_to_environment(self, in_studio):
        with patch.dict(os.environ, {"LINEAR_TEAM_ID": "env_team"}):
            assert credentials.resolve_default_team_id() is None

    def test_a_broken_vault_helper_does_not_raise(self, in_studio):
        def exploding(provider):
            raise RuntimeError("vault unavailable")

        with patch.dict(
            credentials.__dict__, {"__rc_helpers__": {"vault_get": exploding}}
        ):
            assert credentials.resolve_api_key() is None

    def test_a_non_dict_vault_entry_is_ignored(self, in_studio):
        in_studio["linear"] = "not-a-dict"
        assert credentials.resolve_api_key() is None


class TestStandalone:
    """No helpers means library or test use, where the environment is the source."""

    def test_reads_the_key_from_the_environment(self):
        with patch.dict(os.environ, {"LINEAR_API_KEY": "env_key"}):
            assert credentials.resolve_api_key() == "env_key"

    def test_missing_environment_key_returns_none(self):
        with patch.dict(os.environ, {}, clear=True):
            assert credentials.resolve_api_key() is None

    def test_team_id_reads_the_environment(self):
        with patch.dict(os.environ, {"LINEAR_TEAM_ID": "env_team"}):
            assert credentials.resolve_default_team_id() == "env_team"

    def test_malformed_helpers_are_treated_as_absent(self):
        """__rc_helpers__ is loader-owned; anything unexpected is untrusted."""
        with patch.dict(credentials.__dict__, {"__rc_helpers__": "not-a-dict"}), \
             patch.dict(os.environ, {"LINEAR_API_KEY": "env_key"}):
            assert credentials.resolve_api_key() == "env_key"

    def test_helpers_without_vault_get_are_treated_as_no_vault(self):
        """Helpers present but no vault_get: nothing to read, and we must not
        silently reach for the environment inside the Studio."""
        with patch.dict(credentials.__dict__, {"__rc_helpers__": {}}), \
             patch.dict(os.environ, {"LINEAR_API_KEY": "env_key"}):
            assert credentials.resolve_api_key() is None
