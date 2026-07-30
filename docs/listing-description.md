Most Mondays I open Linear to a pile of issues nobody has looked at yet. Assign someone, set a priority, move it out of the backlog, repeat. Twenty minutes of clicking, and if anyone asks a month later who moved them, I have no answer.

This module does the whole pile in one pass, and it makes you look before it writes anything. You hand it the issues and what to change. RailCall shows you the exact payload and waits. You approve once, it runs, and it saves a receipt with your name on it and a hash of what you approved.

45 commands, covering issues, comments, labels, workflow states, cycles, projects, milestones, teams, users, webhooks and initiatives. Reading anything is instant. Anything that writes stops for a human first.

## Worth knowing

- Issue arguments take the `ENG-123` you can already see in the Linear URL. No digging for a UUID.
- Search uses Linear's own, so it matches descriptions and comments, not just titles.
- Rate-limited halfway through a batch? It stops and tells you which issues it never touched. Run it again and it picks up from there.
- It never silently retries a write. Linear can't tell a retry from a second request, so you could end up with duplicates. If a write fails, approve it again.
- Initiatives work too: group projects under a goal, post an onTrack / atRisk / offTrack update.

## Setup

Start `railcall studio`, open **Sends**, pick **Linear — API key + team**, then paste a key from Linear's API settings and your team id. Two minutes, and most commands won't ask for the team again.

Your key stays in the station vault. The published module can't read one out of your environment, never writes it to disk or a log, and receipts record which fields you sent, not the values.

## What it won't do

Only issues accept `ENG-123`; everything else wants an id. Milestones belong to a project, because that's how Linear models them. API keys only for now, no OAuth.

Tested against a real Linear workspace, not mocks, with every command exercised end to end. MIT licensed.

[Source](https://github.com/faizalmy/railcall-linear-module) · [CI](https://github.com/faizalmy/railcall-linear-module/actions/workflows/ci.yml)

contest:2026Q3
