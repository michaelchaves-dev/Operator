import os

from fastapi import FastAPI
from pydantic import BaseModel

from github_status import fetch_repo_status, format_status
from intake import build_packet, format_packet
from parser import AGENT_INDEX, PROJECT_INDEX, parse

app = FastAPI(title="Operator gateway", version="0.2.0-slice0")

ALLOW = {n.strip() for n in os.getenv("OPERATOR_ALLOWLIST", "+10000000000").split(",") if n.strip()}


class SmsIn(BaseModel):
    from_: str | None = None
    sender: str | None = None
    body: str

    def origin(self) -> str:
        return self.from_ or self.sender or ""


def real_status(agent_id: str, project_id: str | None) -> str:
    """Tier 0 status — real GitHub read via github_status, never mock."""
    agent = AGENT_INDEX[agent_id]
    if not project_id:
        return format_status(agent, None, None)
    project = PROJECT_INDEX[project_id]
    repo = (project.get("adapters") or {}).get("github")
    status = fetch_repo_status(repo) if repo else None
    return format_status(agent, project, status)


# Backwards-compatible alias (old name in v0 README / imports)
mock_status = real_status


@app.get("/health")
def health():
    return {"ok": True, "mode": "live-tier0", "intake": True, "slice": "0-roman"}


@app.post("/sms")
def sms(payload: SmsIn):
    origin = payload.origin()
    if origin and origin not in ALLOW:
        return {"ok": False, "reply": "Unauthorized number."}

    parsed = parse(payload.body)
    packet = build_packet(parsed, sender=origin, mask="owner")

    if not packet["allowed"]:
        return {
            "ok": False,
            "parsed": parsed,
            "intake": packet,
            "reply": format_packet(packet),
        }

    if parsed["verb"] == "help":
        work = (
            "OPERATOR\n"
            "Text: @roman #operator status\n"
            "Text: @twin #zali status\n"
            "Delivery: add 'email me' or 'text and email'. Voice is reserved."
        )
    else:
        work = real_status(parsed["agent"], parsed["project"])

    reply = format_packet(packet) + "\n---\n" + work
    return {"ok": True, "parsed": parsed, "intake": packet, "reply": reply}
