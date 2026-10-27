"""Audit log — Slice 1 scaffold (2026-10-26).

One JSONL row per handled message, per the intake checklist's AUDIT cell:
who (masked), agent, project, verb, tier, allowed, delivery, time, action.

Never logged: message bodies, signatures, tokens, full phone numbers.
Sender is masked to its last 4 digits. Path: OPERATOR_AUDIT_LOG env,
default ./audit.jsonl next to the gateway (gitignored).
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def _path() -> Path:
    return Path(os.getenv("OPERATOR_AUDIT_LOG", Path(__file__).with_name("audit.jsonl")))


def mask_number(number: str | None) -> str:
    digits = "".join(c for c in (number or "") if c.isdigit())
    return f"***{digits[-4:]}" if len(digits) >= 4 else "***"


def write_audit(packet: dict, provider: str, message_id: str | None = None) -> dict:
    row = {
        "at": datetime.now(timezone.utc).isoformat(),
        "provider": provider,
        "message_id": message_id,
        "sender_masked": mask_number((packet.get("who") or {}).get("sender")),
        "mask": (packet.get("who") or {}).get("mask"),
        "agent": packet.get("agent_id"),
        "project": packet.get("project_id"),
        "repo": packet.get("repo"),
        "tier": packet.get("tier"),
        "allowed": packet.get("allowed"),
        "deliver": packet.get("deliver"),
        "when": packet.get("when"),
        "action": packet.get("step0_action"),
        "block_reason": packet.get("block_reason"),
    }
    try:
        p = _path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
    except Exception:
        # Audit failure must not take the gateway down; the row is returned
        # either way so callers/tests can assert on it.
        pass
    return row
