"""Live conformance checks against Linear's schema.

The unit suite guards known deprecations by pattern. This asks the server
directly, so it catches Linear deprecating something we use *after* we shipped —
the failure mode a static check cannot see.

Runs only with a real API key; skipped in CI like the rest of the live suite.
"""

import os
import re

import pytest

import handlers.queries as queries
from handlers.client import get_client

pytestmark = pytest.mark.skipif(
    not os.environ.get("LINEAR_API_KEY"),
    reason="LINEAR_API_KEY environment variable not set",
)

# Types whose fields we select. Kept explicit rather than derived, so adding a
# command that touches a new type is a deliberate edit here too.
SELECTED_TYPES = [
    "Issue", "Project", "Team", "User", "Cycle", "Comment", "IssueLabel",
    "WorkflowState", "Initiative", "ProjectMilestone", "Webhook",
    "IssueRelation", "InitiativeUpdate", "ProjectUpdate", "InitiativeToProject",
    "ProjectStatus",
]


def _documents():
    return {n: getattr(queries, n) for n in dir(queries) if n.isupper()}


@pytest.fixture(scope="module")
def gql():
    client = get_client()

    def run(document):
        response = client._post({"query": document}, 30).json()
        assert "errors" not in response, response.get("errors")
        return response["data"]

    return run


class TestNoDeprecatedUsage:
    def test_root_operations_are_current(self, gql):
        """Every query/mutation we call must be undeprecated."""
        data = gql(
            "query{ __schema{"
            " queryType{ fields{ name isDeprecated deprecationReason } }"
            " mutationType{ fields{ name isDeprecated deprecationReason } } } }"
        )
        deprecated = {
            f["name"]: f["deprecationReason"]
            for kind in ("queryType", "mutationType")
            for f in data["__schema"][kind]["fields"]
            if f["isDeprecated"]
        }

        called = set()
        for document in _documents().values():
            body = re.sub(r"\s+", " ", document).strip()
            match = re.search(r"\{\s*(\w+)", body)
            if match:
                called.add(match.group(1))

        offenders = {n: deprecated[n] for n in called if n in deprecated}
        assert offenders == {}, f"calling deprecated operations: {offenders}"

    def test_arguments_are_current(self, gql):
        """Arguments we pass must be undeprecated."""
        data = gql(
            "query{ __schema{"
            " queryType{ fields{ name args(includeDeprecated:true)"
            "  { name isDeprecated deprecationReason } } }"
            " mutationType{ fields{ name args(includeDeprecated:true)"
            "  { name isDeprecated deprecationReason } } } } }"
        )
        schema = {
            f["name"]: {
                a["name"]: a["deprecationReason"]
                for a in f["args"] if a["isDeprecated"]
            }
            for kind in ("queryType", "mutationType")
            for f in data["__schema"][kind]["fields"]
        }

        offenders = []
        for document in _documents().values():
            body = re.sub(r"\s+", " ", document).strip()
            match = re.search(r"\{\s*(\w+)\s*\(([^)]*)\)", body)
            if not match:
                continue
            root, arglist = match.group(1), match.group(2)
            for arg in (a.split(":")[0].strip() for a in arglist.split(",") if ":" in a):
                reason = schema.get(root, {}).get(arg)
                if reason is not None:
                    offenders.append(f"{root}({arg}:) -> {reason}")

        assert offenders == [], offenders

    def test_input_fields_we_set_are_current(self, gql):
        """Keys we build into input_data must be undeprecated."""
        input_types = set()
        for document in _documents().values():
            input_types.update(re.findall(r"\$\w+:\s*(\w+Input)!?", document))

        deprecated = {}
        for name in sorted(input_types):
            data = gql(
                'query{ __type(name:"%s"){ inputFields(includeDeprecated:true)'
                "{ name isDeprecated deprecationReason } } }" % name
            )
            node = data["__type"]
            if not node:
                continue
            for field in node["inputFields"]:
                if field["isDeprecated"]:
                    deprecated.setdefault(field["name"], []).append(
                        (name, field["deprecationReason"])
                    )

        source = open(
            os.path.join(os.path.dirname(__file__), "..", "..", "handlers", "handler.py")
        ).read()
        keys = set(re.findall(r'input_data\[\s*[\'"](\w+)[\'"]\s*\]', source))
        keys.update(re.findall(r'^\s*[\'"]([a-z]\w*)[\'"]\s*:\s*', source, re.M))

        offenders = [
            f"{t}.{k} -> {why}"
            for k in sorted(set(deprecated) & keys)
            for t, why in deprecated[k]
        ]
        assert offenders == [], offenders

    def test_selected_fields_are_current(self, gql):
        """Fields we select on the types we touch must be undeprecated.

        Reported as candidates rather than proven usage - the check is
        name-based, so a name deprecated on one type but used on another shows
        up here for a human to judge. Issue.state vs the deprecated
        Project.state is exactly that case.
        """
        deprecated = {}
        for name in SELECTED_TYPES:
            data = gql(
                'query{ __type(name:"%s"){ fields(includeDeprecated:true)'
                "{ name isDeprecated deprecationReason } } }" % name
            )
            node = data["__type"]
            if not node:
                continue
            for field in node["fields"]:
                if field["isDeprecated"]:
                    deprecated.setdefault(field["name"], []).append(name)

        # `state` is deprecated on Project but current on Issue; we select only
        # the Issue form, always as a nested object.
        allowed = {"state"}
        selected = set()
        for document in _documents().values():
            flattened = re.sub(r"[{}()]", " ", re.sub(r"\s+", " ", document))
            selected.update(re.findall(r"\b([a-z][A-Za-z]*)\b", flattened))

        offenders = sorted((set(deprecated) & selected) - allowed)
        detail = {name: deprecated[name] for name in offenders}
        assert offenders == [], f"selecting deprecated fields: {detail}"
