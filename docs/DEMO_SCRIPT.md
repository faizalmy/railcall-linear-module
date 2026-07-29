# Demo walkthrough scripts

Round 3 moved the video from a +5 bonus to its own **/50 axis** — currently
0/50, which is the single largest gap between this listing and a top ranking.
Sami's steer: ~4 minutes, and lead with the composites, `bulk_update_issues`
above all.

Two cuts below. **Record the 4-minute one** — it is the scored artifact. The
60-second cut is for the store card if a short embed reads better there.

Every on-screen string quoted here is what the Studio actually renders
(`station/workbench/studio/scripts/views/sends.js`). Nothing needs staging.

---

## Step by step

Work top to bottom. Steps 1–4 are setup, 5 is the take, 6–8 publish it.

### 1. Create the fixtures (one command)

```bash
export LINEAR_API_KEY="lin_api_..."
python3 tools/demo_setup.py --create
```

Creates eight realistic untriaged issues — "Login redirect drops the ?next
param", "Stripe webhook retries create duplicate invoices", and so on — then
prints the three values you will paste on camera:

```
issue_ids   ["RAI-516", "RAI-517", ...]        <- paste into the textarea
assignee_id 4633036c-...                        <- you, so the avatar is real
state_id    306001a2-...  (In Progress)
priority    2
```

Keep that terminal output where you can copy from it. Gathering these live is
the single slowest thing you can do on camera.

Titles use a `Demo:` prefix, not `[RailCall Test]` — the live suite deletes
anything with the latter, and it would do it mid-recording.

### 2. Set the screen up

- **Display 1280×800 or larger.** The airlock cards are mono 11px; smaller and
  they turn to mush under YouTube compression.
- **Do Not Disturb on.** macOS: Control Centre → Focus → Do Not Disturb. A
  Slack toast over the receipt means re-recording the take.
- **Browser zoom at 100%** on the Studio, and again on the Linear tab.
- **Close other tabs.** Tab titles are readable at 1280 wide and they are
  nobody's business.
- Hide the desktop and any dock badges you would rather not publish.

### 3. Lay out the two windows

- **Studio:** `railcall studio`, open the **Sends** tab, confirm the `linear.*`
  commands are listed and not `not_configured`. The credential is saved and
  entered masked, so nothing leaks on screen — do not open `keys.local.json`
  or the vault for any reason.
- **Linear:** second tab on the board, filtered to the team, searching
  `Demo:` so all eight fixtures are visible in one frame.

### 4. Rehearse once, then reset

Run the whole ceremony once without recording. Two things you need to have felt
before the real take:

- **The approval is single-use.** After Execute the button stays dead. Firing
  again means Close → re-open the command → Preview → Approve again.
- **The rehearsal consumes the fixtures** — they end up assigned and In
  Progress. Reset before recording:

```bash
python3 tools/demo_setup.py --cleanup
python3 tools/demo_setup.py --create
```

New identifiers, so re-copy the paste block.

### 5. Record

macOS: **⌘⇧5** → *Record Selected Portion* → drag over the Studio window →
Record. Or QuickTime → File → New Screen Recording.

Then follow the shot table below. Speak over it live if you are comfortable;
otherwise record silent and narrate afterwards — the timings hold either way.

Stop with the button in the menu bar. It saves to the Desktop as `.mov`.

### 6. Check the take before uploading

Watch it once at full size and confirm:

- [ ] `payload_hash`, `external_touch = YES`, `receipt_id` and `integrity` are
      all legible — not just present
- [ ] `success_count` on screen matches the number of rows that visibly changed
      in Linear on the following shot
- [ ] No notification, no other tab title, no API key anywhere in frame
- [ ] Audio is audible and clip-free if you narrated live

### 7. Upload

YouTube → Create → Upload video.

- **Visibility: Unlisted or Public.** Both embed. **Private does not** — an
  embedded private video shows an error to every buyer.
- Title: `Linear for RailCall — batch triage behind an approval gate`
- Description: two lines and the two links —
  `https://railcall.ai/marketplace/agentstack-labs/linear` and
  `https://github.com/faizalmy/railcall-linear-module`
- Skip the end screens and cards; they cover the final frame in an embed.

Copy the share URL — the `https://youtu.be/<id>` form.

### 8. Attach it to the listing

```bash
python3 tools/attach_video.py https://youtu.be/<id>
```

That PATCHes the live listing and prints the stored value back, so you can see
it landed. It needs no republish. The equivalent by hand is in **Publishing the
video** at the bottom of this file.

Then tear the fixtures down:

```bash
python3 tools/demo_setup.py --cleanup
```

---

## Quick checklist

- [ ] `demo_setup.py --create`, paste block copied
- [ ] 1280×800+, Do Not Disturb, 100% zoom, tabs closed
- [ ] Studio Sends open, commands registered; Linear board filtered to `Demo:`
- [ ] Rehearsed once, then `--cleanup` and `--create` again
- [ ] Recorded, watched back, hashes legible, no leaks in frame
- [ ] Uploaded **unlisted or public**, `youtu.be` URL copied
- [ ] `attach_video.py <url>` run and confirmed
- [ ] `demo_setup.py --cleanup`

---

## The 4-minute cut (record this one)

| Time | Screen | Say |
|---|---|---|
| 0:00–0:20 | Linear board, eight untriaged issues | "Eight issues came in over the weekend. Each needs an owner, a priority, a state. In the UI that's eight round trips — and when someone asks next month who changed them, there's no answer." |
| 0:20–0:40 | Studio → Sends, scroll the `linear.*` list | "45 commands. Reads run immediately; every write goes through an approval gate. Today just one command." |
| 0:40–1:00 | Select `linear.bulk_update_issues`, paste `issue_ids` | "Bulk update. Eight ids — pasted straight from the Linear URLs, `ENG-123` form, no UUID hunting." |
| 1:00–1:20 | Fill `assignee_id`, `state_id`, `priority` | "One assignee, one state, one priority, for the whole batch. Nothing has left the machine yet." |
| 1:20–1:50 | **1. Preview** — hold, scroll the payload | "Preview first. `external_touch = YES` — this will reach Linear. And the exact payload, hashed." |
| 1:50–2:20 | **2. Approve** — hold on the green card | "A human approves *this* payload. The approval is bound to that hash and it is single-use. Change one id and it's void — that's the point: you cannot approve a preview and then send something else." |
| 2:20–2:45 | **3. Execute** — hold on the receipt block | "`success_count = 8`. And a receipt: id, integrity hash, signature line." |
| 2:45–3:05 | Linear tab, refresh | "Eight issues triaged, one approval." |
| 3:05–3:30 | Studio → Receipts tab, open the row | "Who approved what, and when. Field names and hashes — the payload values aren't stored." |
| 3:30–3:50 | Back to Sends, show `linear.link_issues` + `linear.create_comment` | "Same gate on everything else. Link a blocker, leave an audit comment — 45 commands, one ceremony." |
| 3:50–4:00 | Store card / repo | "Linear for RailCall. MIT, zero dependencies, source on GitHub." |

### If you want one more beat (pushes to ~4:30)

After the receipt, mention the failure path **without faking it**:

> "If Linear rate-limits halfway through, the command stops and reports which
> ids it didn't attempt. Re-run and it picks up there — it never silently
> retries a write, because Linear has no idempotency key and a retry after an
> accepted write would duplicate it."

Say it over the finished receipt. Do not stage a fake rate-limit.

---

## The 60-second cut

| Time | Screen | Say |
|---|---|---|
| 0:00–0:06 | Linear board, untriaged issues | "Monday triage. Eight issues, no owner, no priority." |
| 0:06–0:12 | Sends → `linear.bulk_update_issues` | "One command stages the whole batch." |
| 0:12–0:18 | Paste ids, set assignee + priority | "Ids straight from the Linear URL. Nothing has left the machine." |
| 0:18–0:26 | **1. Preview** | "Preview first. `external_touch = YES`, and the exact payload, hashed." |
| 0:26–0:34 | **2. Approve** | "A human approves this payload. Bound to the hash, single-use." |
| 0:34–0:42 | **3. Execute** | "It runs, and leaves a receipt." |
| 0:42–0:50 | Linear tab, refresh | "Eight issues triaged in one approval." |
| 0:50–0:56 | Receipts tab | "An answer to 'who closed those tickets' that isn't someone's memory." |
| 0:56–1:00 | Store card | "Linear for RailCall. 45 commands, MIT." |

---

## The three cards to hold on

These frames are the governance moment. Do not cut away early.

**Preview** — `1. Preview · pending approval`
```
payload_hash    = <sha256>
idempotency_key = <key>
external_touch  = YES
{ "issue_ids": [...], "priority": 2, "assignee_id": "..." }
```

**Approve** — `2. Approved · bound to payload_hash`
```
Approval single-use · consumed on next execute
```

**Execute** — `3. Executed · receipt signed`
```
success_count = 8
failure_count = 0
receipt_id = ...
integrity  = ...
signature  = present
```

---

## Honesty notes

Not to be claimed on camera, because they are not true:

- The receipt `integrity` field is a **SHA-256 hash**, not an Ed25519
  signature. The Ed25519 signature covers the *bundle* at install time. Say
  "hashed receipt" — or point at the `signature = present` line specifically,
  if it reads `present` on your screen.
- Do not narrate the rate-limit resume over a *successful* run as though it is
  being demonstrated. Describe it as behavior, or skip it.
- `success_count` on screen must match the number of rows that visibly change
  in Linear on the next shot. If you re-record a take, re-check the number.
- The Studio is the only place to save the credential — there is no CLI for
  it. Don't imply otherwise while showing the Sends tab.

---

## Publishing the video

`video_url` is wired in `module.json`, so the next build carries it into the
signed manifest:

```json
"video_url": "https://youtu.be/<id>"
```

The live listing takes it without a republish:

```bash
curl -X PATCH https://railcall-marketplace-lggm.onrender.com/listings/cms1741qi000gcctfv19hssfz/meta \
  -H "Authorization: Bearer $RAILCALL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://youtu.be/<id>"}'
```

`cms1741qi000gcctfv19hssfz` is the listing id — the `/listings/agentstack-labs/linear`
path 404s, so the internal id is the one that works. The same route is what set
`tests_url`, which the publish path does not propagate on its own; re-check both
columns after any republish.
