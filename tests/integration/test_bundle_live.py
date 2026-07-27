"""Live tests for the generated bundle - the artifact users actually install.

tests/unit/test_bundle.py proves the bundle satisfies the loader's static
contract. tests/integration/test_linear_api.py proves the handlers/ package
works against Linear. Neither proves the *flattened* bundle works against
Linear, and that is what the Studio executes.

So this module builds the bundle from source, execs it exactly the way
`studio_server._load_modules` does - isolated namespace, no parent package,
seeded only with os/json/time and __rc_helpers__ - and drives real commands
through the generated `linear_*(inputs, stamp)` adapters.
"""

import json
import os
import sys
import time

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

import build_bundle  # noqa: E402

pytestmark = pytest.mark.skipif(
    not os.environ.get("LINEAR_API_KEY"),
    reason="LINEAR_API_KEY environment variable not set",
)

TEST_PREFIX = "[RailCall Test]"


@pytest.fixture(scope="module")
def bundle():
    """The bundle, exec'd the way the Studio loader execs it.

    Deliberately does NOT import handlers/ - if the flattening dropped
    something, this namespace is where it surfaces.

    __rc_helpers__ carries a working `vault_get`, exactly as the loader supplies.
    That also means this fixture exercises the vault credential path rather than
    the environment one: inside the Studio the module refuses to read
    LINEAR_API_KEY, so a bundle that ignored the vault would fail here.
    """
    with open(build_bundle.SOURCE_MANIFEST, "r", encoding="utf-8") as handle:
        source = json.load(handle)

    manifest = build_bundle.build_manifest(source)
    text = build_bundle.flatten_sources() + build_bundle.build_adapters(manifest)

    def vault_get(provider):
        """Stand-in for the station vault, keyed the same way the Studio is."""
        if provider != "linear":
            return None
        return {"api_key": os.environ["LINEAR_API_KEY"]}

    namespace = {
        "__name__": "railcall_module_agentstack_labs_linear",
        "__file__": "handlers/handler.py",
        "__rc_helpers__": {"vault_get": vault_get},
        "os": os,
        "json": json,
        "time": time,
    }
    exec(compile(text, "handlers/handler.py", "exec"), namespace)

    # Mirror the loader's registration step so the tests address commands by id.
    handlers = {}
    for command in manifest["commands"]:
        fn_name = build_bundle.handler_function_name(command["id"])
        handlers[command["id"]] = namespace[fn_name]

    return {"handlers": handlers, "manifest": manifest, "ns": namespace}


@pytest.fixture(scope="module")
def team_id(bundle):
    output, _ = bundle["handlers"]["linear.list_teams"]({"limit": 1}, "stamp")
    assert output["teams"], "workspace has no teams"
    return output["teams"][0]["id"]


class TestBundleReads:
    """Read commands, through the generated adapters, against the real API."""

    def test_list_teams(self, bundle):
        output, artifact = bundle["handlers"]["linear.list_teams"]({"limit": 10}, "stamp")

        assert artifact is None, "these commands return JSON, not a file"
        assert output["count"] == len(output["teams"])
        assert output["count"] > 0
        assert all(t.get("id") and t.get("key") for t in output["teams"])
        print(f"✓ bundle linear.list_teams -> {output['count']} team(s)")

    def test_list_issues_with_a_filter(self, bundle, team_id):
        """Exercises the IssueFilter object built inside the flattened code."""
        output, _ = bundle["handlers"]["linear.list_issues"](
            {"team_id": team_id, "limit": 5}, "stamp"
        )

        assert output["count"] == len(output["issues"])
        assert output["count"] <= 5
        print(f"✓ bundle linear.list_issues -> {output['count']} issue(s)")

    def test_search_issues(self, bundle):
        output, _ = bundle["handlers"]["linear.search_issues"](
            {"query": "RailCall", "limit": 5}, "stamp"
        )

        assert output["query"] == "RailCall"
        assert output["count"] == len(output["issues"])
        print(f"✓ bundle linear.search_issues -> {output['count']} match(es)")

    def test_list_states_labels_cycles(self, bundle, team_id):
        """The three commands whose root queries were rewritten."""
        for cid, payload, key in [
            ("linear.list_states", {"team_id": team_id, "limit": 5}, "states"),
            ("linear.list_labels", {"team_id": team_id, "limit": 5}, "labels"),
            ("linear.list_cycles", {"team_id": team_id, "limit": 5}, "cycles"),
        ]:
            output, _ = bundle["handlers"][cid](payload, "stamp")
            assert output["count"] == len(output[key]), cid
            print(f"✓ bundle {cid} -> {output['count']} row(s)")

    def test_pagination_runs_through_the_bundle(self, bundle):
        """paginate_query is inlined too - make sure the limit is honored."""
        output, _ = bundle["handlers"]["linear.list_issues"]({"limit": 3}, "stamp")
        assert len(output["issues"]) <= 3


class TestBundleWrites:
    """A full create -> read -> update -> delete cycle through the adapters."""

    def test_issue_lifecycle(self, bundle, team_id):
        handlers = bundle["handlers"]
        title = f"{TEST_PREFIX} Bundle Lifecycle"

        created, artifact = handlers["linear.create_issue"](
            {
                "team_id": team_id,
                "title": title,
                "description": "Created through the generated RailCall bundle.",
                "priority": 3,
            },
            "stamp",
        )
        assert artifact is None
        issue_id = created["issue"]["id"]
        assert created["issue"]["title"] == title
        print(f"✓ bundle linear.create_issue -> {created['issue']['identifier']}")

        fetched, _ = handlers["linear.get_issue"]({"issue_id": issue_id}, "stamp")
        assert fetched["issue"]["id"] == issue_id

        updated, _ = handlers["linear.update_issue"](
            {"issue_id": issue_id, "title": f"{title} (Updated)", "priority": 1}, "stamp"
        )
        assert updated["issue"]["title"] == f"{title} (Updated)"

        commented, _ = handlers["linear.create_comment"](
            {"issue_id": issue_id, "body": f"{TEST_PREFIX} bundle comment"}, "stamp"
        )
        assert commented["comment"]["id"]

        deleted, _ = handlers["linear.delete_issue"]({"issue_id": issue_id}, "stamp")
        assert deleted["success"] is True
        assert deleted["deleted_issue_id"] == issue_id
        print(f"✓ bundle linear.delete_issue -> {issue_id}")


class TestBundleErrorHandling:
    """Failures must reach the airlock as RuntimeError carrying useful text."""

    def test_validation_error_becomes_runtime_error(self, bundle):
        with pytest.raises(RuntimeError, match="Invalid issue_id"):
            bundle["handlers"]["linear.get_issue"]({"issue_id": "not-a-uuid"}, "stamp")

    def test_missing_required_argument_becomes_runtime_error(self, bundle):
        with pytest.raises(RuntimeError):
            bundle["handlers"]["linear.get_issue"]({}, "stamp")

    def test_empty_search_is_rejected_before_the_api(self, bundle):
        with pytest.raises(RuntimeError, match="query cannot be empty"):
            bundle["handlers"]["linear.search_issues"]({"query": "   "}, "stamp")

    def test_unknown_inputs_are_ignored(self, bundle):
        """Studio may pass presentation fields alongside real arguments."""
        output, _ = bundle["handlers"]["linear.list_teams"](
            {"limit": 2, "_ui_hint": "table", "context": {"run": 1}}, "stamp"
        )
        assert output["count"] >= 1


class TestInstalledBundleMatchesSource:
    """The installed copy must be the current build, or the station is stale."""

    def test_installed_bundle_is_current(self, bundle):
        installed = os.path.expanduser(
            "~/.railcall/station/modules/agentstack-labs-linear/handlers/handler.py"
        )
        if not os.path.isfile(installed):
            pytest.skip("bundle not installed into the local station")

        expected = (
            build_bundle.flatten_sources() + build_bundle.build_adapters(bundle["manifest"])
        )
        with open(installed, "r", encoding="utf-8") as handle:
            actual = handle.read()

        assert actual == expected, (
            "installed bundle is stale - rebuild with: "
            "python3 tools/build_bundle.py --install"
        )
