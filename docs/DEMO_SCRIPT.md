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

## Before recording (both cuts)

- [ ] ~8 untriaged issues in the workspace: no assignee, no priority, all in
      the same state. Create them first. Do **not** use the `[RailCall Test]`
      prefix — the live suite deletes anything carrying it.
- [ ] A second browser tab on the Linear board, filtered to that team, so the
      before/after is one click away.
- [ ] `railcall studio` running, Sends tab showing the `linear.*` commands
      registered. The credential is saved and masked, so nothing leaks.
- [ ] Issue identifiers on the clipboard. **Use `ENG-123` form, not UUIDs** —
      v0.2.9 accepts them and it is visibly less alien on camera.
- [ ] Screen at 1280×800 or larger. The airlock cards are mono 11px and turn
      to mush under YouTube compression at anything smaller.
- [ ] One rehearsal pass. The approval is single-use: after Execute, the button
      stays dead, and re-firing means Close → re-open → re-approve. Know that
      before you are recording.

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
