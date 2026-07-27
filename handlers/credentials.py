"""Credential resolution.

The module runs in two places and they hand out secrets differently:

* **Inside the RailCall Studio** — the loader execs `handler.py` with a
  `__rc_helpers__` dict in globals, and the operator's key lives in the
  station vault under the ``linear`` provider entry. The vault is the ONLY
  source there: process environment is readable via `ps auxe` and lands in
  core dumps, so reading it would defeat the vault the operator configured.
* **Standalone / tests** — there is no vault, so the environment is used.

Every environment read lives in a `_standalone_*` function below, and nothing
else in this module touches `os.environ`. `tools/build_bundle.py` replaces
those bodies with `return None` when generating the published bundle, because
that artifact only ever runs inside the Studio - so the shipped code contains
no credential environment read at all, not merely an unreachable one.

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


# ---------------------------------------------------------------------------
# Standalone-only sources. NEUTRALIZED IN THE PUBLISHED BUNDLE.
#
# tools/build_bundle.py rewrites each of these bodies to `return None` (or an
# empty string) before signing. Keep every os.environ read and every literal
# credential variable name inside them - anything that leaks outside will ship
# in the bundle and read as environment-based auth to a reviewer.
# ---------------------------------------------------------------------------

def _standalone_api_key() -> Optional[str]:
    """The API key when there is no vault. Neutralized in the bundle."""
    return os.environ.get("LINEAR_API_KEY")


def _standalone_team_id() -> Optional[str]:
    """The default team when there is no vault. Neutralized in the bundle."""
    return os.environ.get("LINEAR_TEAM_ID")


def standalone_credential_hint() -> str:
    """Operator guidance for the no-vault case. Neutralized in the bundle."""
    return "Set LINEAR_API_KEY in the environment."


def standalone_invalid_hint() -> str:
    """Operator guidance for a rejected standalone key. Neutralized in the bundle."""
    return "Check LINEAR_API_KEY in the environment."


def resolve_api_key() -> Optional[str]:
    """The Linear API key: the station vault inside the Studio, else the environment.

    Inside the Studio the vault is the ONLY source. A missing vault entry is an
    error to surface, not something to paper over.
    """
    if in_studio():
        entry = vault_entry("linear")
        if not entry:
            return None
        return str(entry.get("api_key") or "").strip() or None

    return _standalone_api_key()


def resolve_default_team_id() -> Optional[str]:
    """Optional team_id saved alongside the key. Same vault-or-environment rule."""
    if in_studio():
        entry = vault_entry("linear")
        if not entry:
            return None
        return str(entry.get("team_id") or "").strip() or None

    return _standalone_team_id()
