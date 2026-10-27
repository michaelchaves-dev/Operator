import hmac
import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel

import outbound
import providers
from audit import write_audit
from github_status import fetch_repo_status, format_status
from intake import build_packet, format_packet
from parser import AGENT_INDEX, PROJECT_INDEX, parse

app = FastAPI(title="Operator gateway", version="0.3.0-slice1")

ALLOW = {n.strip() for n in os.getenv("OPERATOR_ALLOWLIST", "+10000000000").split(",") if n.strip()}


class SmsIn(BaseModel):
    from_: str | None = None
    sender: str | None = None
    body: str

    def origin(self) -> str:
        return self.from_ or self.sender or ""


class NotifyIn(BaseModel):
    text: str
    to: str | None = None


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


def handle_inbound(sender: str, body: str, provider: str, message_id: str | None = None) -> dict:
    """One plane for every channel: dev JSON, Twilio, Telnyx.

    Allowlist -> parse -> intake packet -> tier gate -> work -> audit row.
    """
    if sender and sender not in ALLOW:
        return {"ok": False, "reply": "Unauthorized number.", "packet": None}

    parsed = parse(body)
    packet = build_packet(parsed, sender=sender, mask="owner")
    write_audit(packet, provider=provider, message_id=message_id)

    if not packet["allowed"]:
        return {"ok": False, "parsed": parsed, "intake": packet, "reply": format_packet(packet)}

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


@app.get("/health")
def health():
    return {
        "ok": True,
        "mode": "live-tier0",
        "intake": True,
        "slice": "1-provider-webhook-scaffold",
        "outbound_provider": outbound.configured_provider(),
        "dev_mode": providers.dev_mode(),
    }


@app.post("/sms")
def sms(payload: SmsIn):
    return handle_inbound(payload.origin(), payload.body, provider="dev-json")


@app.post("/webhook/twilio")
async def webhook_twilio(request: Request):
    form = dict(await request.form())
    ok, why = providers.verify_twilio(str(request.url), form, request.headers.get("X-Twilio-Signature"))
    if not ok:
        return PlainTextResponse(f"Forbidden: {why}", status_code=403)
    inbound = providers.parse_twilio(form)
    result = handle_inbound(inbound.sender, inbound.body, provider="twilio", message_id=inbound.message_id)
    return PlainTextResponse(providers.twiml_reply(result["reply"]), media_type="application/xml")


@app.post("/webhook/telnyx")
async def webhook_telnyx(request: Request):
    raw = await request.body()
    ok, why = providers.verify_telnyx(
        raw,
        request.headers.get("telnyx-signature-ed25519"),
        request.headers.get("telnyx-timestamp"),
    )
    if not ok:
        return JSONResponse({"ok": False, "error": f"Forbidden: {why}"}, status_code=403)
    inbound = providers.parse_telnyx(raw)
    if inbound is None:
        return {"ok": True, "ignored": True, "reason": "not an inbound message event"}
    result = handle_inbound(inbound.sender, inbound.body, provider="telnyx", message_id=inbound.message_id)
    # Telnyx replies go back out through the API, not the webhook response.
    sent = outbound.send_sms(inbound.sender, result["reply"]) if inbound.sender in ALLOW else None
    return {"ok": result["ok"], "reply_sent": sent, "would_reply": result["reply"] if not (sent and sent.get("ok")) else None}


@app.post("/notify")
def notify(payload: NotifyIn, request: Request):
    """Operator texts the owner. Token-gated, allowlist-only recipients."""
    expected = os.getenv("OPERATOR_NOTIFY_TOKEN")
    provided = request.headers.get("X-Operator-Notify-Token", "")
    if not expected:
        return JSONResponse({"ok": False, "error": "OPERATOR_NOTIFY_TOKEN not configured — /notify fails closed"}, status_code=503)
    if not hmac.compare_digest(expected, provided):
        return JSONResponse({"ok": False, "error": "bad notify token"}, status_code=403)
    to = payload.to or next(iter(ALLOW), None)
    if not to or to not in ALLOW:
        return JSONResponse({"ok": False, "error": "recipient is not on OPERATOR_ALLOWLIST — /notify only texts the owner"}, status_code=400)
    return outbound.send_sms(to, payload.text)
