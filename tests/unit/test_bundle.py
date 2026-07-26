"""Tests for the generated RailCall module bundle.

These encode the Studio loader's contract (station/workbench/studio_server.py
::_load_modules). Every assertion here corresponds to a gate that silently
rejects the module if it is wrong:

  * commands keyed by `id`, not `name`   - `if not cid: continue` registers nothing
  * handler fn named `<id with . -> _>`  - "no callable ... in handler.py"
  * one flat file, no relative imports   - ImportError under exec()
  * Ed25519 signature over canonical json + handler bytes - "invalid signature"
"""

import ast
import json
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

import build_bundle  # noqa: E402


@pytest.fixture(scope="module")
def source_manifest():
    with open(build_bundle.SOURCE_MANIFEST, "r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture(scope="module")
def manifest(source_manifest):
    return build_bundle.build_manifest(source_manifest)


@pytest.fixture(scope="module")
def handler_text(manifest):
    return build_bundle.flatten_sources() + build_bundle.build_adapters(manifest)


class TestManifestShape:
    """The loader reads cmd["id"]; a manifest keyed by "name" registers zero commands."""

    def test_every_command_has_a_dotted_id(self, manifest):
        assert manifest["commands"], "no commands built"
        for command in manifest["commands"]:
            assert command["id"].startswith("linear."), command
            assert "name" not in command

    def test_command_count_matches_source(self, manifest, source_manifest):
        assert len(manifest["commands"]) == len(source_manifest["commands"])

    def test_ids_are_unique(self, manifest):
        ids = [c["id"] for c in manifest["commands"]]
        assert len(ids) == len(set(ids))

    def test_publisher_pubkey_is_an_ed25519_hex_key(self, manifest):
        key = manifest["publisher_pubkey"]
        assert len(key) == 64
        bytes.fromhex(key)

    def test_input_schema_is_flat(self, manifest):
        """The registry wants {field: {type, required}}, not JSON-Schema."""
        for command in manifest["commands"]:
            for field, spec in command["input_schema"].items():
                assert "type" in spec, (command["id"], field)
                assert isinstance(spec["required"], bool), (command["id"], field)
                assert "properties" not in spec

    def test_required_fields_survive_the_rewrite(self, manifest):
        create = next(c for c in manifest["commands"] if c["id"] == "linear.create_issue")
        required = {f for f, s in create["input_schema"].items() if s["required"]}
        assert required == {"team_id", "title"}

    def test_reads_and_writes_get_distinct_modes(self, manifest):
        """resolve_status() maps mode -> whether the airlock gates the command."""
        by_id = {c["id"]: c for c in manifest["commands"]}
        assert by_id["linear.list_teams"]["mode"] == "read"
        assert by_id["linear.create_issue"]["mode"] == "write_requires_approval"
        assert by_id["linear.delete_issue"]["mode"] == "write_requires_approval"

    def test_deletes_are_flagged_high_risk(self, manifest):
        for command in manifest["commands"]:
            expected = "high" if command["id"].startswith("linear.delete_") else None
            if expected:
                assert command["risk"] == expected, command["id"]

    def test_commands_declare_wiring_and_provider(self, manifest):
        for command in manifest["commands"]:
            assert command["wired"] is True
            assert command["provider"] == "linear"
            assert command["requires"] == ["LINEAR_API_KEY"]


class TestFlattenedHandler:
    """The loader execs one file with no parent package."""

    def test_no_relative_imports_survive(self, handler_text):
        tree = ast.parse(handler_text)
        offenders = [
            node.module or "."
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.level
        ]
        assert offenders == [], f"relative imports would ImportError: {offenders}"

    def test_it_compiles(self, handler_text):
        compile(handler_text, "handler.py", "exec")

    def test_it_execs_in_the_loader_namespace(self, handler_text):
        """Reproduces the loader's isolated exec, seeded exactly as it seeds it."""
        namespace = {
            "__name__": "railcall_module_test",
            "__file__": "handler.py",
            "__rc_helpers__": {},
            "os": os,
            "json": json,
            "time": __import__("time"),
        }
        exec(compile(handler_text, "handler.py", "exec"), namespace)
        assert callable(namespace.get("linear_list_teams"))

    def test_every_command_has_a_matching_adapter(self, manifest, handler_text):
        """fn_name = cid.replace('.', '_') - a mismatch rejects that command."""
        tree = ast.parse(handler_text)
        defined = {
            node.name for node in tree.body if isinstance(node, ast.FunctionDef)
        }

        missing = [
            command["id"]
            for command in manifest["commands"]
            if build_bundle.handler_function_name(command["id"]) not in defined
        ]
        assert missing == [], f"no callable adapter for: {missing}"

    def test_adapters_take_the_loader_signature(self, handler_text):
        """LOCAL_HANDLERS[cid](inputs, stamp) - two positional args."""
        tree = ast.parse(handler_text)
        adapters = [
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name.startswith("linear_")
        ]
        assert adapters
        for node in adapters:
            args = [a.arg for a in node.args.args]
            assert args == ["inputs", "stamp"], (node.name, args)


class TestAdapterBehavior:
    """The adapter bridges kwargs-and-dict to (inputs, stamp) -> (output, artifact)."""

    @pytest.fixture(scope="class")
    def namespace(self, manifest):
        text = build_bundle.flatten_sources() + build_bundle.build_adapters(manifest)
        ns = {
            "__name__": "railcall_module_test",
            "__file__": "handler.py",
            "__rc_helpers__": {},
            "os": os,
            "json": json,
            "time": __import__("time"),
        }
        exec(compile(text, "handler.py", "exec"), ns)
        return ns

    def test_returns_an_output_artifact_pair(self, namespace):
        def fake(limit=50):
            return {"teams": [], "count": 0}

        output, artifact = namespace["_rc_invoke"](fake, {"limit": 5})
        assert output == {"teams": [], "count": 0}
        assert artifact is None

    def test_unknown_inputs_are_dropped(self, namespace):
        """Studio may pass presentation fields the command does not accept."""
        def fake(limit=50):
            return {"limit": limit}

        output, _ = namespace["_rc_invoke"](fake, {"limit": 5, "_ui_hint": "x"})
        assert output == {"limit": 5}

    def test_module_errors_become_runtime_errors(self, namespace):
        """The airlock surfaces the message, so it must carry the useful text."""
        def fake():
            raise namespace["ValidationError"]("Invalid team_id format: nope")

        with pytest.raises(RuntimeError, match="Invalid team_id format"):
            namespace["_rc_invoke"](fake, {})

    def test_value_errors_become_runtime_errors(self, namespace):
        def fake():
            raise ValueError("No fields to update")

        with pytest.raises(RuntimeError, match="No fields to update"):
            namespace["_rc_invoke"](fake, {})


class TestSignature:
    """Signed material is canonical(module.json) + b"\\n" + handler.py bytes."""

    @pytest.fixture(scope="class")
    def keypair(self):
        try:
            return build_bundle.load_publisher_seed()
        except SystemExit:
            pytest.skip("no publisher keypair on this machine")

    def test_canonical_form_is_deterministic(self, manifest):
        assert build_bundle.canonical(manifest) == build_bundle.canonical(manifest)

    def test_canonical_form_ignores_key_order(self):
        assert build_bundle.canonical({"a": 1, "b": 2}) == build_bundle.canonical({"b": 2, "a": 1})

    def test_signature_verifies(self, manifest, handler_text, keypair):
        seed_hex, _ = keypair
        handler_bytes = handler_text.encode("utf-8")
        signature = build_bundle.sign(
            build_bundle.canonical(manifest), handler_bytes, seed_hex
        )
        build_bundle.verify(manifest, handler_bytes, signature)

    def test_a_tampered_handler_fails_verification(self, manifest, handler_text, keypair):
        """This is the gate that stops a swapped handler.py from loading."""
        from cryptography.exceptions import InvalidSignature

        seed_hex, _ = keypair
        signature = build_bundle.sign(
            build_bundle.canonical(manifest), handler_text.encode("utf-8"), seed_hex
        )

        tampered = (handler_text + "\n# injected\n").encode("utf-8")
        with pytest.raises(InvalidSignature):
            build_bundle.verify(manifest, tampered, signature)

    def test_a_tampered_manifest_fails_verification(self, manifest, handler_text, keypair):
        from cryptography.exceptions import InvalidSignature

        seed_hex, _ = keypair
        handler_bytes = handler_text.encode("utf-8")
        signature = build_bundle.sign(
            build_bundle.canonical(manifest), handler_bytes, seed_hex
        )

        tampered = dict(manifest, version="9.9.9")
        with pytest.raises(InvalidSignature):
            build_bundle.verify(tampered, handler_bytes, signature)
