# Agent intake checklist

Every inbound text hits this packet **before** tools. Same list for Bella, Twin, Coder, Security, Research, Deploy, Commons, and any role you add later.

Reasoning path is `registry/reasoning-gates.md` (BabyG sequence + -Step0 seven-check). This file is the packet those gates must fill.

If a required field is empty, the agent asks **one** question. It does not guess a repo or a write.

## Packet

1. **Who** — allowlisted sender? owner or client mask?
2. **Which project / repo** — `#id` or explicit name. Unwired adapter = stop on write.
3. **What, exactly** — one sentence restatement of the ask.
4. **What, in total** — one bullet per reversible slice. Hidden extras stay off the list.
5. **Which agent** — named `@role` or Operator pick from the roster.
6. **Tier** — 0 read / 1 low-risk / 2 approve / 3 second confirm.
7. **Allowed?** — role × project × tool × tier. No → refuse and say why.
8. **How to deliver** — `sms` (default) | `email` | `both` | later `voice`.
9. **When** — `now` | a clock | `when-done`.
10. **Voice (later)** — off in v0. Field reserved: `none` | assigned voice id | random-from-pool.
11. **Approval id** — blank on Tier 0–1 unless policy says otherwise.
12. **Step0 action** — A proceed | B one question | C smallest tool | D refuse.
13. **Ternary** — project / write / allow as -1 | 0 | +1.
14. **Audit** — log who, agent, project, verb, delivery, time, action.

## Delivery codes

| code | now | later |
| --- | --- | --- |
| sms | reply in the same thread | same |
| email | founder@SubtractArchitect.com unless the packet names another owner inbox | client inbox only if allowlisted |
| both | sms summary + email body/link | same |
| voice | **not live** | outbound call with assigned or pooled voice, still after the checklist |

Voice does not skip tiers. A call is another channel into the same packet.

## One-question rule

Ask only the first missing required field:

- no project + write implied → "Which project?"
- project unwired + write → "Repo not wired."
- delivery missing on a long result → "SMS or email?"
- tier 2/3 → issue `APPROVE <id>` / `CONFIRM <id>`

Do not stack five clarifying texts.

## Self-check line

```
WHO / REPO / ASK / TOTAL / AGENT / TIER / ALLOWED / DELIVER / WHEN / VOICE / APPROVAL / ACTION
```

If any cell that must be filled is blank, stop. Action B, not invent.
