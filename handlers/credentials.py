"""Credential resolution.

The module runs in two places and they hand out secrets differently:

* **Standalone / tests** — `LINEAR_API_KEY` in the environment.
* **Inside the RailCall Studio** — the loader execs `handler.py` with a
  `__rc_helpers__` dict in globals, and the operator's key lives in the
  station vault under the ``linear`` provider entry.

Everything funnels through `resolve_api_key()` so neither the GraphQL client
nor the cache has to know which one it got.
"""

import os
from typing import Any, Dict, Optional


def _rc_helpers() -> Optional[Dict[str, Any]]:
    """The helper dict the Studio loader injects, or None when standalone.

    Trust boundary: ``__rc_helpers__`` is owned and populated by the Studio
    loader, not by this module. Any code sharing the bundled namespace could
    theoretically mutate it, so we treat whatever it contains as untrusted
    input (hence the isinstance/callable guards below). This is by design -
    the loader is the authority on what helpers exist.
    """
    helpers = globals().get("__rc_helpers__")
    return helpers if isinstance(helpers, dict) else None


def in_studio() -> bool:
    """Whether the RailCall Studio is hosting us.

    Presence of the loader-injected helper dict is the signal. It decides where
    credentials come from, so callers use this rather than re-deriving it.
    """
    return _rc_helpers() is not None


def vault_entry(provider: str = "linear") -> Optional[Dict[str, Any]]:
    """Read a provider credential from the station vault.

    Returns None when running outside the Studio, or when nothing is saved.
    """
    helpers = _rc_helpers()
    if not helpers:
        return None

    getter = helpers.get("vault_get")
    if not callable(getter):
        return None

    try:
        entry = getter(provider)
    except Exception as exc:
        import logging
        logging.debug("vault_get failed for provider %r: %s", provider, exc)
        return None

    return entry if isinstance(entry, dict) else None


def resolve_api_key() -> Optional[str]:
    """The Linear API key: the station vault inside the Studio, else the environment.

    Inside the Studio the vault is the ONLY source. Process environment is not an
    acceptable fallback there - it is readable via `ps auxe` and lands in core
    dumps, so silently reading it would defeat the vault the operator configured.
    A missing vault entry is an error to surface, not something to paper over.

    Outside the Studio (library use, the test suite) there is no vault to read
    from, so LINEAR_API_KEY is the supported source.
    """
    if in_studio():
        entry = vault_entry("linear")
        if not entry:
            return None
        return str(entry.get("api_key") or "").strip() or None

    return os.environ.get("LINEAR_API_KEY")


def resolve_default_team_id() -> Optional[str]:
    """Optional team_id saved alongside the key. Same vault-or-environment rule."""
    if in_studio():
        entry = vault_entry("linear")
        if not entry:
            return None
        return str(entry.get("team_id") or "").strip() or None

    return os.environ.get("LINEAR_TEAM_ID")
