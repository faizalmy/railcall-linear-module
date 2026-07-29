#!/usr/bin/env python3
"""Create and tear down the fixtures for the marketplace demo video.

Gathering ids on camera is the slowest part of a take: eight issue identifiers,
an assignee and a target state, all needed as paste-ready JSON before the
recording starts. This does that in one command and prints the exact blocks to
paste into the Studio Sends form.

    python3 tools/demo_setup.py --create     # make fixtures, print the inputs
    python3 tools/demo_setup.py --cleanup    # delete everything it created

Created ids are tracked in tools/.demo_fixtures.json so --cleanup never has to
guess from titles. Requires LINEAR_API_KEY in the environment (standalone use;
the published bundle has no environment read at all).

Titles use a "Demo:" prefix rather than the suite's "[RailCall Test]", so a
stray run of the live tests cannot delete the fixtures mid-recording.
"""

import argparse
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from handlers.handler import (  # noqa: E402
    create_issue, delete_issue, list_states, list_teams,
)
from handlers.client import execute_query  # noqa: E402

STATE_FILE = os.path.join(REPO_ROOT, "tools", ".demo_fixtures.json")
PREFIX = "Demo:"

# Realistic weekend intake - the point on camera is that these look like a real
# backlog, not like test rows.
DEMO_ISSUES = [
    "Login redirect drops the ?next param",
    "Stripe webhook retries create duplicate invoices",
    "Search returns archived projects",
    "Onboarding email links to the old docs domain",
    "CSV export truncates at 1000 rows",
    "Timezone off by one on the weekly digest",
    "Avatar upload fails silently over 5MB",
    "Rate limit banner never clears",
]


def load_state():
    if not os.path.isfile(STATE_FILE):
        return {"issues": []}
    with open(STATE_FILE, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)


def create():
    team = list_teams(limit=1)["teams"][0]
    team_id = team["id"]

    # The assignee: whoever owns the API key, so the demo assigns to a real
    # person with a real avatar rather than an arbitrary teammate.
    viewer = execute_query("query { viewer { id name } }")["viewer"]

    states = list_states(team_id=team_id, limit=50)["states"]
    started = next((s for s in states if s["type"] == "started"), None)
    if not started:
        raise SystemExit(
            "No 'started' workflow state in this team - the demo needs one to "
            "move issues into. Create an 'In Progress' state first."
        )

    state = load_state()
    created = []
    for title in DEMO_ISSUES:
        issue = create_issue(
            team_id=team_id,
            title=f"{PREFIX} {title}",
            description="Weekend intake for the RailCall demo recording.",
        )["issue"]
        created.append({"id": issue["id"], "identifier": issue["identifier"]})
        print(f"  created {issue['identifier']}  {title}")

    state["issues"] = state.get("issues", []) + created
    save_state(state)

    identifiers = [i["identifier"] for i in created]

    print("\n" + "=" * 68)
    print("PASTE INTO linear.bulk_update_issues")
    print("=" * 68)
    print("\nissue_ids  (paste into the issue_ids textarea):")
    print(json.dumps(identifiers))
    print(f"\nassignee_id  ({viewer['name']}):")
    print(viewer["id"])
    print(f"\nstate_id  ({started['name']}):")
    print(started["id"])
    print("\npriority:")
    print("2")
    print("\n" + "=" * 68)
    print(f"Board: filter Linear to team {team['key']} and search \"{PREFIX}\"")
    print("Teardown when the take is done: python3 tools/demo_setup.py --cleanup")
    print("=" * 68)


def cleanup():
    state = load_state()
    issues = state.get("issues", [])
    if not issues:
        print("Nothing tracked in tools/.demo_fixtures.json - nothing to delete.")
        return

    for issue in issues:
        try:
            delete_issue(issue_id=issue["id"])
            print(f"  deleted {issue['identifier']}")
        except Exception as exc:  # a manually deleted fixture is not an error
            print(f"  skipped {issue['identifier']}: {str(exc)[:70]}")

    save_state({"issues": []})
    print(f"\n{len(issues)} fixture(s) removed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--create", action="store_true", help="create demo fixtures")
    group.add_argument("--cleanup", action="store_true", help="delete what --create made")
    args = parser.parse_args()

    if not os.environ.get("LINEAR_API_KEY"):
        raise SystemExit("LINEAR_API_KEY is not set.")

    # Confirm which workspace before writing to it - this is a real backlog.
    org = execute_query("query { organization { name } }")["organization"]["name"]
    print(f"workspace: {org}\n")

    if args.create:
        create()
    else:
        cleanup()

    return 0


if __name__ == "__main__":
    sys.exit(main())
