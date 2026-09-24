import os
from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel

from parser import AGENT_INDEX, PROJECT_INDEX, parse

app = FastAPI(title="Operator gateway stub", version="0.1.0")

# Placeholder only. Real allowlist lives in env, never in git.
ALLOW = {n.strip() for n in os.getenv("OPERATOR_ALLOWLIST", "+10000000000").split(",") if n.strip()}


class SmsIn(BaseModel):
    from_: str | None = None
    sender: str | None = None
    body: str

    def origin(self) -> str:
        return self.from_ or self.sender or ""


def mock_status(agent_id: str, project_id: str | None) -> str:
    agent = AGENT_INDEX[agent_id]
    if not project_id:
        return (
            f"OPERATOR\n"
            f"Agent: {agent['id']} ({agent['role']})\n"
            f"Project: not named\n"
            f"Tier 0 stub. Name a project with #id to bind a repo."
        )
    project = PROJECT_INDEX[project_id]
    repo = (project.get("adapters") or {}).get("github") or "unwired"
    now = datetime.now(timezone.utc).strftime("%H:%M UTC")
    return (
        f"{project['label'].upper()}\n"
        f"Agent: {agent['id']}\n"
        f"Repo: {repo}\n"
        f"Branch: main\n"
        f"Checked: {now}\n"
        f"Open PRs: n/a (stub)\n"
        f"Tests: n/a (stub)\n"
        f"Live GitHub App: not connected"
    )


@app.get("/health")
def health():
    return {"ok": True, "mode": "stub-tier0"}


@app.post("/sms")
def sms(payload: SmsIn):
    origin = payload.origin()
    if origin and origin not in ALLOW:
        return {"ok": False, "reply": "Unauthorized number."}

    parsed = parse(payload.body)
    agent = AGENT_INDEX[parsed["agent"]]
    project_id = parsed["project"]

    if project_id and agent["projects"] != ["*"] and project_id not in agent["projects"]:
        return {
            "ok": False,
            "parsed": parsed,
            "reply": f"{agent['id']} is not on {project_id}.",
        }

    if parsed["verb"] == "help":
        reply = (
            "OPERATOR\n"
            "Text: @twin #zali status\n"
            "Or: Operator, status on Operator\n"
            "v0 is read-only mock status."
        )
    else:
        reply = mock_status(parsed["agent"], project_id)

    return {"ok": True, "parsed": parsed, "reply": reply}
