# Operator

Text-to-agent control line for Subtract Architect Studios.

You text **Operator**. Operator routes. Specialists do the work. The roster adds and subtracts without changing the number.

Public face: talk-to-text on a phone → one Operator → the right role on the right project → a short reply.

Owner face: the same gateway as a command line with authority tiers.

Contact: founder@SubtractArchitect.com  
Site: https://www.subtractarchitect.com

The phone number is an entrance, not the system. This repo is the plane.

## Route / Gate / Cut

```
phone (SMS / talk-to-text)
  → identity allowlist
  → intake checklist (every agent)
  → agent from registry
  → authority tier
  → adapter (GitHub first)
  → audit row
  → delivery (sms default; email optional; voice later)
```

One human entry. Many agents. Many projects. Separate authority. Minimum privilege. Human final control. Full audit.

GitHub is adapter one. Vercel, Drive, Commons, client stacks are later adapters. SMS, iMessage, Slack, voice are later channels. Do not rebuild the plane for a new channel.

## Intake (all agents)

Before tools, every role fills the same packet:

WHO / REPO / ASK / TOTAL / AGENT / TIER / ALLOWED / DELIVER / WHEN / VOICE / APPROVAL

Spec: `registry/intake-checklist.md`  
Schema: `registry/intake.schema.json`  
Stub builder: `gateway/intake.py`

If a required cell is empty, ask one question. Do not guess a repo.

Delivery codes: `sms` | `email` | `both` | `voice` (reserved — still replies by SMS in v0).

## Two masks, one gateway

**User / client** talks to Operator in ordinary language. They do not pick `@security`. Operator selects the role.

**Owner** may address a role and a project directly:

```
@twin #zali inspect retrieval
@security #bellaOS status
@roman #operator status
Operator, status on Operator, email me when done
```

**Roman** (`@roman` / `@rome`) joined the roster in Slice 0 (2026-10-26, owner's direction): Michael's Muse operating partner as owner-face supervisor — projects `*`, Tier 2 ceiling, branch / proposed-patch writes only behind `APPROVE <id>`, no merge and no deploy. Bella remains the default router/desk.

## Authority

| Tier | Meaning | SMS may |
| --- | --- | --- |
| 0 | Automatic read | status, commits, issues, logs, tests, agent status |
| 1 | Low-risk | create issue, comment, start research, run tests, create branch, propose patch |
| 2 | Human approve | write files, commit, open PR, staging deploy, config |
| 3 | Second confirm | merge protected, production, delete, rotate secrets, change agent authority |

`yes` is not a merge. T2/T3 use `APPROVE <id>` / `CONFIRM <id>`.

Secrets never travel in SMS. Replies carry status, ids, and links. Patch bodies stay in the repo.

## v0 (this repo)

Shipped:

- this README
- `registry/projects.json`
- `registry/agents.json`
- `registry/intake-checklist.md` + `intake.schema.json`
- `gateway/` stub: parse text → intake packet → mock Tier 0 status

Slice 0 (2026-10-26, branch `slice-0-roman-tier0`):

- Roman added to `registry/agents.json` (see above).
- GitHub adapters wired in `registry/projects.json` for #aim, #subtractoken, and #bellaos (exact repos verified; #zali stays unwired — two candidate repos, no guessing).
- `gateway/github_status.py`: Tier 0 status is now a **live GitHub API read**, not a mock. Public repos need no token; private repos read an optional `GITHUB_TOKEN` / `GH_TOKEN` from the gateway environment only (never committed, never logged). If GitHub cannot be reached or auth is missing, the reply says so honestly — no fabricated numbers.
- Tests: `gateway/test_slice0.py`.

Not shipped: live number, GitHub App, writes, outbound email send, outbound voice.

## Run the stub

```bash
cd gateway
pip install -r requirements.txt
uvicorn app:app --reload --port 8080
```

```bash
curl -s -X POST http://127.0.0.1:8080/sms \
  -H 'content-type: application/json' \
  -d '{"sender":"+10000000000","body":"@roman #operator status"}'
```

Allowlist is env `OPERATOR_ALLOWLIST`. Never commit real numbers.

## Next reversible slices

1. GitHub App, named repos, live Tier 0 status.
2. Signed provider webhook + number allowlist.
3. Audit log.
4. T2 approval tokens.
5. Email delivery adapter (named inbox only).
6. Voice channel (assigned / random pool) — after email works.

One slice per gate.

<!-- SAS-IP-FOOTER-v1 -->
---
**Subtract Architect Studios™**  
Copyright © 2026 Michael F. Chaves. All rights reserved in original Subtract Architect Studios materials except as expressly licensed. See [IP_NOTICE.md](./IP_NOTICE.md). Existing open-source and third-party licenses remain controlling for materials they cover.
