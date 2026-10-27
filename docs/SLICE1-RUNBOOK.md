# Slice 1 Runbook — live number + signed webhook

Status: **scaffold built, $0 spent, no number bought.** Everything below the
"Michael's steps" line is already coded and tested. The remaining steps need
Michael's account, Michael's card, and Michael's merge clicks.

## What Slice 1 adds over Slice 0

- `gateway/providers.py` — Twilio (HMAC-SHA1 `X-Twilio-Signature`) and Telnyx
  (Ed25519 `telnyx-signature-ed25519`) webhook verification. **Fails closed**:
  no signing secret configured = webhook refuses, unless `OPERATOR_DEV_MODE=1`
  (local only).
- `POST /webhook/twilio` → replies in TwiML. `POST /webhook/telnyx` → replies
  go back out through the Telnyx API (`gateway/outbound.py`).
- `gateway/audit.py` — one JSONL row per handled message: time, provider,
  masked sender (`***1234`), agent, project, tier, allowed, action. No bodies,
  no numbers in full, no secrets.
- `POST /notify` — how Roman/Operator texts Michael first (watched reply,
  tour confirmation, etc.). Gated by `OPERATOR_NOTIFY_TOKEN` header and
  **recipients are hard-restricted to `OPERATOR_ALLOWLIST`** — it cannot text
  anyone else.
- Deploy scaffold: `gateway/Procfile`, root `railway.json`, `gateway/.env.example`.

## How a text flows

```
Michael's phone ──SMS──▶ provider number ──signed webhook──▶ gateway (Railway)
   ▲                                                            │ allowlist
   │                                                            │ intake packet
   └────────────── reply (TwiML or provider API) ◀── tier gate ──┘
```

## Michael's steps (the only ones left)

1. **Merge PR #1** (Slice 0), then the Slice 1 PR stacked on it.
2. **Pick a provider.** Recommendation: **Telnyx** (~$1/mo number,
   ~$0.004/SMS segment + carrier fees, prices checked Oct 2026, can change).
   Twilio also works (~$1.15/mo, ~$0.0083/segment + carrier fees) and is the
   adapter MarciAi's TITAN ancestor used. One provider only to start.
3. **Create the account in your name** and add a small balance ($10 is plenty
   for months of personal use). Card via the provider's own page — never in
   chat, never in the repo.
4. **Pick the number route:**
   - *Toll-free (recommended first):* ~$2/mo, needs a free verification form
     (name, use case: "personal notifications / two-way control line, one
     user"). Usually the fastest legal route for a private line.
   - *Local 10DLC:* looks like a normal local number, but US carriers require
     brand + campaign registration (a few dollars one-time, ~$1.50–$10/mo
     campaign fee) and approval can take days to weeks. Do NOT pick a 603
     number without thinking — the MarciAi ruling was demo number ≠ 603;
     your call for Operator's private line.
5. **Put secrets in the host env** (Railway variables), per `.env.example`:
   provider key(s), `OPERATOR_FROM_NUMBER`, `OPERATOR_ALLOWLIST` (your cell),
   `OPERATOR_NOTIFY_TOKEN`, optional read-only `GITHUB_TOKEN`.
6. **Point the provider webhook** at the deployed gateway:
   `https://<your-host>/webhook/telnyx` (or `/webhook/twilio`), event:
   inbound message.
7. **Smoke test:** text `@roman #operator status` → expect a real Tier 0
   reply. Text from any other phone → expect "Unauthorized number."

## Honest limits of this scaffold

- No number exists yet, no account exists yet, nothing is deployed yet.
- Voice is NOT Slice 1. Voice is Slice 3, reusing the MarciAi stack
  (LiveKit + Deepgram Nova-3 + Cartesia Sonic).
- Outbound `/notify` is coded but has never sent a real text — first real
  send happens in step 7's smoke test, with Michael watching.
