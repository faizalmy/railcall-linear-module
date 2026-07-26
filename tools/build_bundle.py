#!/usr/bin/env python3
"""Build the signed, single-file module bundle the RailCall Studio loader expects.

The loader (`station/workbench/studio_server.py::_load_modules`) installs exactly
three files per module and `exec`s the handler in an isolated namespace:

    modules/<slug>/module.json
    modules/<slug>/module.sig
    modules/<slug>/handlers/handler.py

That means no packages and no relative imports, which is the opposite of how the
source is organized. Rather than flatten the source and lose the test suite, this
script generates the bundle from it:

  1. concatenates `handlers/*.py` in dependency order, dropping relative imports
  2. appends a thin `linear_<command>(inputs, stamp)` adapter per command, which
     is the calling convention the loader registers into LOCAL_HANDLERS
  3. rewrites `module.json` into the loader's command shape (dotted `id`, flat
     `input_schema`, `mode`/`risk`/`requires` gating)
  4. signs `canonical(module.json) + b"\\n" + handler.py` with the publisher's
     Ed25519 key and writes `module.sig`

Usage:
    python3 tools/build_bundle.py [--out dist] [--install]

`--install` copies the result into ~/.railcall/station/modules/<slug>/ so the
Studio picks it up on its next module reload.
"""

import argparse
import ast
import json
import os
import re
import shutil
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_MANIFEST = os.path.join(REPO_ROOT, "module.json")

# Concatenation order is dependency order: a name must be defined before the
# module-level code of a later file uses it. Function bodies are late-bound, so
# only module-level statements actually constrain this.
SOURCE_FILES = [
    "handlers/credentials.py",
    "handlers/utils/errors.py",
    "handlers/utils/validation.py",
    "handlers/utils/pagination.py",
    "handlers/queries.py",
    "handlers/cache.py",
    "handlers/client.py",
    "handlers/handler.py",
]

# `from .x import y` / `from ..x import (a, b)` - possibly spanning lines.
RELATIVE_IMPORT = re.compile(
    r"^from\s+\.+[\w.]*\s+import\s+(?:\([^)]*\)|[^\n]*)\n",
    re.MULTILINE | re.DOTALL,
)

PROVIDER = "linear"
COMMAND_PREFIX = "linear."

BUNDLE_HEADER = '''"""RailCall Linear module - GENERATED, DO NOT EDIT.

Built by tools/build_bundle.py from the handlers/ package. Edit the source
there and rebuild; changes made here are overwritten and would also invalidate
module.sig.

The Studio loader execs this file in an isolated namespace seeded with `os`,
`json`, `time` and `__rc_helpers__`. Everything the module needs is inlined
below because relative imports have no parent package here.
"""

'''

ADAPTER_PREAMBLE = '''

# ==========================================================================
# RAILCALL ADAPTERS
# ==========================================================================
# The loader calls handlers as fn(inputs: dict, stamp) -> (output, artifact).
# The functions above use ordinary keyword arguments and return a dict, so
# each command gets a thin adapter rather than a rewritten implementation.

import inspect as _rc_inspect


def _rc_invoke(fn, inputs):
    """Call a command function with the subset of `inputs` it accepts.

    Unknown keys are dropped rather than raising TypeError, because the Studio
    may pass presentation fields alongside the real arguments. Missing required
    arguments still raise, which is what we want.
    """
    inputs = inputs or {}
    accepted = _rc_inspect.signature(fn).parameters
    kwargs = {k: v for k, v in inputs.items() if k in accepted}

    try:
        result = fn(**kwargs)
    except LinearError as exc:
        # The airlock records a failed_safely receipt from the raised message,
        # so it must carry the actionable text rather than a class name.
        raise RuntimeError(str(exc))
    except (TypeError, ValueError) as exc:
        raise RuntimeError(str(exc))

    # No artifact: these commands return JSON, not a file on disk.
    return result, None
'''


MINIFIED_HEADER = """# RailCall Linear module - GENERATED, DO NOT EDIT.
#
# Docstrings and comments are stripped so the published bundle fits the
# marketplace's 100 KiB request limit. The fully documented source this was
# generated from lives at:
#     https://github.com/faizalmy/railcall-linear-module
# Rebuild with: python3 tools/build_bundle.py --minify
"""


def minify(text):
    """Drop docstrings and comments; keep behavior byte-for-byte equivalent.

    ast.unparse regenerates source from the parse tree, which discards comments
    for free; docstrings are removed explicitly first. The result is checked by
    the same tests as the readable build, so a mistake here fails the suite
    rather than silently shipping.
    """
    tree = ast.parse(text)

    for node in ast.walk(tree):
        if not isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            continue
        body = node.body
        is_docstring = (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        )
        if is_docstring:
            # A function whose only statement was a docstring still needs a body.
            node.body = body[1:] or [ast.Pass()]

    return MINIFIED_HEADER + ast.unparse(ast.fix_missing_locations(tree)) + "\n"


def read_source(rel_path):
    with open(os.path.join(REPO_ROOT, rel_path), "r", encoding="utf-8") as handle:
        return handle.read()


def strip_relative_imports(text):
    """Remove intra-package imports; the bundle is one flat namespace."""
    return RELATIVE_IMPORT.sub("", text)


def flatten_sources():
    """Concatenate the package into one module body."""
    chunks = [BUNDLE_HEADER]

    for rel_path in SOURCE_FILES:
        body = strip_relative_imports(read_source(rel_path))
        chunks.append(
            f"\n# {'=' * 70}\n# source: {rel_path}\n# {'=' * 70}\n\n{body.strip()}\n"
        )

    return "\n".join(chunks)


def command_id(name):
    return COMMAND_PREFIX + name


def handler_function_name(cid):
    """Mirror the loader: fn_name = cid with dots and dashes as underscores."""
    return cid.replace(".", "_").replace("-", "_")


def risk_for(name, side_effects):
    if side_effects != "write":
        return "low"
    # Deletes are the only irreversible commands here.
    return "high" if name.startswith("delete_") else "medium"


def mode_for(side_effects):
    # resolve_status(): "read" -> available_read_only,
    # "write_requires_approval" -> gated behind the Approval Airlock.
    return "write_requires_approval" if side_effects == "write" else "read"


def flat_input_schema(parameters):
    """JSON-Schema properties -> the registry's flat {field: {type, required}}."""
    properties = (parameters or {}).get("properties") or {}
    required = set((parameters or {}).get("required") or [])

    schema = {}
    for field, spec in properties.items():
        entry = {
            "type": spec.get("type", "string"),
            "required": field in required,
        }
        if spec.get("description"):
            entry["description"] = spec["description"]
        if "default" in spec:
            entry["default"] = spec["default"]
        if spec.get("enum"):
            entry["enum"] = spec["enum"]
        schema[field] = entry

    return schema


def build_manifest(source):
    """Rewrite the authoring manifest into the loader's shape."""
    commands = []

    for command in source["commands"]:
        name = command["name"]
        side_effects = command.get("side_effects", "none")

        commands.append({
            # Both keys on purpose. The published spec
            # (railcall.ai/docs/marketplace-developer/modules) documents
            # `name` + `description`; the shipped Studio loader reads `id` and
            # skips any command without one. Emitting both satisfies the
            # marketplace validator and still registers in the runtime.
            "id": command_id(name),
            "name": name,
            "description": command.get("description") or "",
            "title": command.get("description") or name.replace("_", " ").capitalize(),
            "provider": PROVIDER,
            "risk": risk_for(name, side_effects),
            "mode": mode_for(side_effects),
            "wired": True,
            "requires": ["LINEAR_API_KEY"],
            "preview": True,
            "receipt_required": True,
            "input_schema": flat_input_schema(command.get("parameters")),
        })

    return {
        "id": source["id"],
        # `slug` is the documented manifest key; `id` is what the CLI's publish
        # path and the loader actually read. Same value, both spellings.
        "slug": source["id"],
        "version": source["version"],
        "name": source["name"],
        "description": source["description"],
        "author": source["author"],
        "license": source["license"],
        "provider": PROVIDER,
        "publisher_pubkey": source["publisher_pubkey"],
        "license_required": False,
        "category": source.get("category"),
        "tags": source.get("tags"),
        "contest_tag": source.get("contest_tag"),
        "auth": source["auth"],
        "commands": commands,
    }


def build_adapters(manifest):
    """One `linear_<command>` wrapper per declared command id."""
    lines = [ADAPTER_PREAMBLE]

    for command in manifest["commands"]:
        cid = command["id"]
        source_fn = cid[len(COMMAND_PREFIX):]
        lines.append(
            f'\n\ndef {handler_function_name(cid)}(inputs, stamp):\n'
            f'    """{command["title"]}"""\n'
            f'    return _rc_invoke({source_fn}, inputs)\n'
        )

    return "".join(lines)


def canonical(obj):
    """Byte-identical to studio_server._module_canonical."""
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def load_publisher_seed():
    """Ed25519 seed from the RailCall publisher keypair.

    Never printed or copied into the bundle - only the public half is embedded.
    """
    path = os.environ.get(
        "RAILCALL_PUBLISHER_KEY",
        os.path.expanduser("~/.railcall/marketplace_publisher.json"),
    )
    if not os.path.isfile(path):
        raise SystemExit(
            f"No publisher keypair at {path}.\n"
            "Create one with: railcall market publisher init \"<display name>\""
        )

    with open(path, "r", encoding="utf-8") as handle:
        record = json.load(handle)

    seed_hex = record.get("seed_hex")
    pubkey_hex = record.get("pubkey_hex")
    if not seed_hex or not pubkey_hex:
        raise SystemExit(f"Publisher keypair at {path} is missing seed_hex/pubkey_hex.")

    return seed_hex, pubkey_hex


def sign(manifest_bytes, handler_bytes, seed_hex):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    private_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(seed_hex))
    return private_key.sign(manifest_bytes + b"\n" + handler_bytes).hex()


def verify(manifest, handler_bytes, signature_hex):
    """Re-run the loader's own check so a bad bundle never leaves the build."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    public_key = Ed25519PublicKey.from_public_bytes(
        bytes.fromhex(manifest["publisher_pubkey"])
    )
    payload = canonical({k: v for k, v in manifest.items() if k != "signature"})
    public_key.verify(bytes.fromhex(signature_hex), payload + b"\n" + handler_bytes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="dist", help="output directory (default: dist)")
    parser.add_argument(
        "--install",
        action="store_true",
        help="also copy into ~/.railcall/station/modules/<slug>/",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="build and compile only - no signing key needed (for CI)",
    )
    parser.add_argument(
        "--minify",
        action="store_true",
        help="strip docstrings/comments to fit the marketplace 100 KiB limit",
    )
    args = parser.parse_args()

    with open(SOURCE_MANIFEST, "r", encoding="utf-8") as handle:
        source = json.load(handle)

    manifest = build_manifest(source)
    handler_text = flatten_sources() + build_adapters(manifest)
    if args.minify:
        handler_text = minify(handler_text)
    handler_bytes = handler_text.encode("utf-8")

    # The bundle must import cleanly on its own before it is worth signing.
    try:
        compile(handler_bytes, "handler.py", "exec")
    except SyntaxError as exc:
        raise SystemExit(f"Generated handler.py does not compile: {exc}")

    if args.check:
        print(f"bundle OK: {len(manifest['commands'])} commands, "
              f"{len(handler_bytes):,} bytes, compiles clean")
        return 0

    seed_hex, pubkey_hex = load_publisher_seed()
    if pubkey_hex != manifest["publisher_pubkey"]:
        raise SystemExit(
            "publisher_pubkey in module.json does not match the local keypair.\n"
            f"  module.json: {manifest['publisher_pubkey']}\n"
            f"  keypair:     {pubkey_hex}\n"
            "The loader verifies against the embedded key, so these must agree."
        )

    manifest_bytes = canonical(manifest)
    signature_hex = sign(manifest_bytes, handler_bytes, seed_hex)
    verify(manifest, handler_bytes, signature_hex)

    # The slug the CLI derives from the listing id: non-alphanumerics become '-'.
    slug = re.sub(r"[^A-Za-z0-9._-]", "-", manifest["id"])[:120].strip("_-.")
    out_dir = os.path.join(REPO_ROOT, args.out, slug)
    os.makedirs(os.path.join(out_dir, "handlers"), exist_ok=True)

    # module.json must be written as the exact bytes that were signed.
    with open(os.path.join(out_dir, "module.json"), "wb") as handle:
        handle.write(manifest_bytes)
    with open(os.path.join(out_dir, "handlers", "handler.py"), "wb") as handle:
        handle.write(handler_bytes)
    with open(os.path.join(out_dir, "module.sig"), "w", encoding="utf-8") as handle:
        handle.write(signature_hex + "\n")

    # The marketplace rejects a POST body over 100 KiB, and the body is the
    # manifest plus the handler plus JSON overhead.
    post_estimate = len(manifest_bytes) + len(handler_bytes) + 2048
    limit = 102_400

    print(f"bundle:    {out_dir}")
    print(f"commands:  {len(manifest['commands'])}")
    print(f"handler:   {len(handler_bytes):,} bytes" + (" (minified)" if args.minify else ""))
    print(f"POST size: ~{post_estimate:,} of {limit:,} bytes"
          + ("" if post_estimate < limit else "  <-- TOO LARGE, rebuild with --minify"))
    print(f"signature: verified against {manifest['publisher_pubkey'][:16]}...")

    if args.install:
        target = os.path.expanduser(f"~/.railcall/station/modules/{slug}")
        if os.path.exists(target):
            shutil.rmtree(target)
        shutil.copytree(out_dir, target)
        print(f"installed: {target}")
        print("Reload with: railcall studio  (or POST /api/modules/reload)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
