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
    """The helper dict the Studio loader injects, or None when standalone."""
    helpers = globals().get("__rc_helpers__")
    return helpers if isinstance(helpers, dict) else None


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
    except Exception:
        return None

    return entry if isinstance(entry, dict) else None


def resolve_api_key() -> Optional[str]:
    """The Linear API key, vault first then environment.

    The vault wins because inside the Studio it is the operator's configured
    credential, whereas a stray LINEAR_API_KEY in the station's environment
    would be an accident rather than a choice.
    """
    entry = vault_entry("linear")
    if entry:
        key = str(entry.get("api_key") or "").strip()
        if key:
            return key

    return os.environ.get("LINEAR_API_KEY")


def resolve_default_team_id() -> Optional[str]:
    """Optional team_id saved alongside the key, used as a fallback."""
    entry = vault_entry("linear")
    if entry:
        team_id = str(entry.get("team_id") or "").strip()
        if team_id:
            return team_id
    return os.environ.get("LINEAR_TEAM_ID")
