# 60-second demo walkthrough

Shot list for the marketplace `video_url` embed. Round-3 scoring adds up to +5
for a clear, honest walkthrough, with a bonus for showing the airlock approval
on screen — so the governance moment gets 22 of the 60 seconds, not a passing
mention.

Every on-screen string quoted below is what the Studio actually renders
(`station/workbench/studio/scripts/views/sends.js`). Nothing here needs staging
or editing to look better than it is.

## Before recording

- [ ] Workspace has ~6 unassigned issues with no priority. Create them first so
      the bulk update has something visible to change. Do **not** use the
      `[RailCall Test]` prefix — the live suite deletes those.
- [ ] Second browser tab open on Linear, filtered to that team, so the "after"
      state is one click away.
- [ ] `railcall studio` running, Sends tab already showing `linear.*` commands
      registered — the credential is saved and masked, so nothing leaks.
- [ ] Have the three bulk issue UUIDs on the clipboard. Typing them burns
      15 seconds of a 60-second video.
- [ ] Screen at 1280×800 or larger. The airlock cards are mono 11px; anything
      smaller is unreadable after YouTube compression.

## Shot list

| Time | Screen | Say |
|---|---|---|
| 0:00–0:06 | Linear board, six untriaged issues | "Monday triage. Six issues, no owner, no priority. In the UI that's six round trips each." |
| 0:06–0:12 | Studio → Sends tab, `linear.bulk_update_issues` selected | "One command stages the whole batch." |
| 0:12–0:18 | Paste `issue_ids`, set `priority`, `assignee_id` | "Issue ids, an assignee, a priority. Nothing has left the machine yet." |
| 0:18–0:26 | Click **1. Preview** — hold on the card | "Preview first. `external_touch = YES`, and the exact payload, hashed." |
| 0:26–0:34 | Click **2. Approve** — hold on "Approved · bound to payload_hash" | "A human approves *this* payload. The approval is bound to that hash and single-use — change one id and it's void." |
| 0:34–0:42 | Click **3. Execute** — hold on `receipt_id` / `integrity` / `signature present` | "Now it runs, and it leaves a receipt: who approved what, hashed." |
| 0:42–0:50 | Linear tab, refresh — six issues now assigned and prioritized | "Six issues triaged in one approval." |
| 0:50–0:56 | Studio → Receipts tab, the row just written | "And an answer to 'who closed those tickets' that isn't someone's memory." |
| 0:56–1:00 | Store card / repo | "Linear for RailCall. 45 commands, MIT." |

## The three cards to hold on

Do not cut away early — these are the frames that earn the governance bonus.

**Preview** (`1. Preview · pending approval`)
```
payload_hash    = <sha256>
idempotency_key = <key>
external_touch  = YES
{ "issue_ids": [...], "priority": 2, "assignee_id": "..." }
```

**Approve** (`2. Approved · bound to payload_hash`)
```
Approval single-use · consumed on next execute
```

**Execute** (`3. Executed · receipt signed`)
```
success_count = 6
failure_count = 0
receipt_id = ...
integrity  = ...
signature  = present
```

## Honesty notes

Things not to claim on camera, because they are not true:

- The receipt `integrity` is a **SHA-256 hash**, not an Ed25519 signature. The
  Ed25519 signature covers the *bundle* at install time. Say "hashed receipt",
  not "cryptographically signed receipt", unless the `signature` line reads
  `present` on screen — then point at that line specifically.
- Do not narrate the retry story over a successful run. Mutations are never
  auto-retried; if you want to show `not_attempted`, you have to actually
  rate-limit, and a 60-second video is the wrong place for it.
- Show real issue counts. `success_count` on screen should match the number of
  rows that changed in Linear on the next shot.

## Publishing the video

`video_url` in `module.json` is already wired — set it and the next build
carries it into the signed manifest:

```json
"video_url": "https://youtu.be/<id>"
```

For the listing that is already live, no republish is needed:

```bash
curl -X PATCH https://railcall-marketplace-lggm.onrender.com/listings/cms1741qi000gcctfv19hssfz/meta \
  -H "Authorization: Bearer $RAILCALL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://youtu.be/<id>"}'
```

`cms1741qi000gcctfv19hssfz` is the listing id for `agentstack-labs/linear`; the
`/listings/agentstack-labs/linear` path 404s, so the internal id is the one that
works.
