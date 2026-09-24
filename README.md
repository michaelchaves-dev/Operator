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
  → intent + project
  → agent from registry
  → authority tier
  → adapter (GitHub first)
  → audit row
  → SMS reply
```

One human entry. Many agents. Many projects. Separate authority. Minimum privilege. Human final control. Full audit.

GitHub is adapter one. Vercel, Drive, Commons, client stacks are later adapters. SMS, iMessage, Slack are later channels. Do not rebuild the plane for a new channel.

## Two masks, one gateway

**User / client** talks to Operator in ordinary language. They do not pick `@security`. Operator selects the role.

**Owner** may address a role and a project directly:

```
@twin #zali inspect retrieval
@security #bellaOS status
Operator, what are agents working on?
```

Talk-to-text is sloppy. If a write is requested and no project is named, Operator asks one question. It does not guess a repo.

## Authority

| Tier | Meaning | SMS may |
| --- | --- | --- |
| 0 | Automatic read | status, commits, issues, logs, tests, agent status |
| 1 | Low-risk | create issue, comment, start research, run tests, create branch, propose patch |
| 2 | Human approve | write files, commit, open PR, staging deploy, config |
| 3 | Second confirm | merge protected, production, delete, rotate secrets, change agent authority |

`yes` is not a merge. T2/T3 use `APPROVE <id>` / `CONFIRM <id>`.

Secrets never travel in SMS. Replies carry status, ids, and links. Patch bodies stay in the repo.

## v0 (this commit)

Shipped:

- this README
- `registry/projects.json` — add/subtract projects here
- `registry/agents.json` — add/subtract roles here
- `gateway/` — stub webhook that parses a text and returns **mock Tier 0 status only**

Not shipped:

- live Twilio/Telnyx number
- signed webhook verification
- GitHub App
- write paths
- multi-channel
- conversation memory beyond one parsed line

## Registries

Edit JSON. Do not invent a second control plane to add a worker.

Projects use `adapters.github` when a repo exists. `null` means named but not wired.

Agents declare `max_tier`, `projects` (`*` or ids), and tools. Operator (`bella`) is the default router.

## Run the stub

```bash
cd gateway
pip install -r requirements.txt
uvicorn app:app --reload --port 8080
```

```bash
curl -s -X POST http://127.0.0.1:8080/sms \
  -H 'content-type: application/json' \
  -d '{"from":"+10000000000","body":"@twin #zali status"}'
```

Allowlist in the stub is a placeholder. Put real numbers in env, never in git.

## Next reversible slices

1. GitHub App, install on named repos, Tier 0 live status.
2. Signed provider webhook + number allowlist.
3. Audit log file / table.
4. T2 approval tokens.
5. Vercel adapter.

One slice per gate.
