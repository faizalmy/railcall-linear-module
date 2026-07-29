#!/usr/bin/env python3
"""Attach the demo video to the live marketplace listing.

    python3 tools/attach_video.py https://youtu.be/<id>
    python3 tools/attach_video.py https://youtu.be/<id> --dry-run

Does two things, because either alone drifts:

  1. PATCHes `video_url` onto the listing, which takes effect immediately and
     needs no republish.
  2. Writes the same URL into `module.json`, so the next `market publish`
     carries it instead of dropping back to a listing with no video.

Uses the marketplace session `railcall market login` already saved. Reads the
listing back afterwards and prints the stored value, because a 200 on the PATCH
is not the same as the field being set.
"""

import argparse
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(REPO_ROOT, "module.json")

# The listing id, not the slug: /listings/agentstack-labs/linear returns 404,
# the internal id is what the API resolves.
LISTING_ID = "cms1741qi000gcctfv19hssfz"

# youtu.be/<id> or youtube.com/watch?v=<id> - the two forms the store embeds.
YOUTUBE_URL = re.compile(
    r"^https://(?:youtu\.be/[\w-]{6,}|(?:www\.)?youtube\.com/watch\?v=[\w-]{6,})"
)


def load_cli():
    """Import the RailCall CLI for its authenticated-request helper."""
    sys.path.insert(0, os.path.expanduser("~/.railcall"))
    try:
        import railcall_cli
    except ImportError:
        raise SystemExit(
            "Cannot import ~/.railcall/railcall_cli.py - is the RailCall CLI installed?"
        )
    return railcall_cli


def update_manifest(url):
    with open(MANIFEST, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    if manifest.get("video_url") == url:
        print("module.json: already set")
        return

    manifest["video_url"] = url
    with open(MANIFEST, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print("module.json: video_url written - rebuild the bundle before republishing")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="YouTube URL (https://youtu.be/<id>)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="validate the URL and show the current listing without writing",
    )
    parser.add_argument(
        "--no-manifest",
        action="store_true",
        help="PATCH the listing only, leave module.json alone",
    )
    args = parser.parse_args()

    if not YOUTUBE_URL.match(args.url):
        raise SystemExit(
            f"Not a YouTube URL the store can embed: {args.url}\n"
            "Expected https://youtu.be/<id> or https://youtube.com/watch?v=<id>"
        )
    if "<id>" in args.url or "YOUR_ID" in args.url:
        raise SystemExit("That is still the placeholder, not a real video id.")

    cli = load_cli()

    code, rows = cli._marketplace_authed_request("GET", "/listings/mine")
    if code != 200 or not rows:
        raise SystemExit(
            f"Could not read your listings (HTTP {code}). Run: railcall market login"
        )
    listing = next((r for r in rows if r.get("id") == LISTING_ID), rows[0])
    print(f"listing:   {listing.get('slug')} v{listing.get('version')} "
          f"({listing.get('status')})")
    print(f"current:   video_url = {listing.get('video_url')}")

    if args.dry_run:
        print(f"\ndry run - would PATCH video_url = {args.url}")
        if not args.no_manifest:
            print("dry run - would write the same URL into module.json")
        return 0

    code, _ = cli._marketplace_authed_request(
        "PATCH", f"/listings/{listing['id']}/meta", {"video_url": args.url}
    )
    if code != 200:
        raise SystemExit(f"PATCH failed with HTTP {code}")

    code, rows = cli._marketplace_authed_request("GET", "/listings/mine")
    stored = next(
        (r.get("video_url") for r in rows if r.get("id") == listing["id"]), None
    )
    print(f"stored:    video_url = {stored}")
    if stored != args.url:
        raise SystemExit("The listing did not keep the URL - check it in the store UI.")

    if not args.no_manifest:
        update_manifest(args.url)

    print(f"\nLive at: https://railcall.ai/marketplace/{listing.get('slug')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
