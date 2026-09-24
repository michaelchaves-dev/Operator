# Reasoning gates (BabyG + -Step0)

Operator does not copy the skill files into this repo. Those stay skills.
This file is the public map: every inbound text runs the same sequence the house agents already use.

Line: Context-Aware Intent Recovery | Engineering by Subtraction.

## Sequence

`Segment → -Step0 → ternary {-1,0,+1} → lean RelAI → intake packet → act or one question`

NSZ mutate loop only if the slice would touch GitHub, Drive, money, deploy, or a known failure.

Do not load bellaOS as a second operating system inside the gateway.

## Segment

Split the text into reversible slices. One slice = one gate.
A text that says "fix retrieval and deploy prod" is two slices, not one heroic pass.

## -Step0 seven-check (silent unless the owner asked for the dump)

1. Intent — what the words mean.
2. Objective — what done looks like.
3. Deliverable — sms / email / both / later voice; artifact type.
4. Constraints — tier, roster, wired repo, allowlist, brand mail only.
5. Routes — reuse / answer / one question / refuse / escalate.
6. Elimination — drop guess-the-repo, drop write-without-wire, drop five clarifying texts.
7. Action — A proceed | B one question | C smallest tool | D refuse.

Stop at the first hard hit:

1. Duplicate result exists → reuse.
2. Cache / prior status exists → return it.
3. Lighter method exists → read not write.
4. Permissions missing → block.
5. Evidence insufficient → one question.
6. Unstable or known-bad pattern → delay.
7. Irreversible → T2/T3 confirm.
8. High risk, no automation grant → human gate.

## Ternary

Each claim gets `+1` support, `0` unknown, `-1` oppose.
Unknown stays `0`. Do not coerce a missing project into yes.

## RelAI width

Lean (2-way) default.
Widen only if lean disagrees on project, tier, or allow.
Do not open four-wide on a status text.

## How this fills the intake packet

| Packet field | Gate |
| --- | --- |
| Who | allowlist + mask |
| Repo | Segment + evidence check |
| Ask | Intent |
| Total | Segment slices |
| Agent | roster route |
| Tier | constraints |
| Allowed | elimination + permission |
| Deliver / When | Deliverable |
| Voice | reserved channel |
| Approval | irreversible / T2-T3 |
| Missing | first empty required cell |

## One-question rule stays

-Step0 wrapper cap: one to three questions, prefer one.
Operator cap for SMS: **one**.

## Learn gate

Durable lesson → ask owner before writing Commons / bella_rag / memory.
Gateway logs the packet. It does not silent-ingest doctrine.
