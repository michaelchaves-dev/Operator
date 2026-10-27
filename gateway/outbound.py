"""Outbound SMS — Slice 1 scaffold (2026-10-26).

Used two ways:
1. Reply to a Telnyx inbound message (Telnyx has no TwiML — replies go
   back out through its API).
2. /notify — Operator texts the OWNER. Recipients are hard-restricted to
   the OPERATOR_ALLOWLIST numbers; there is no way to text anyone else
   through this module.

Credentials from env only: TELNYX_API_KEY + OPERATOR_FROM_NUMBER, or
TWILIO_ACCOUNT_SID + TWILIO_AUTH_TOKEN + OPERATOR_FROM_NUMBER.
If nothing is configured this returns an honest not-configured result —
it never pretends a text was sent.
"""
import base64
import json
import os
import urllib.request


def _post_json(url: str, payload: dict, headers: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8") or "{}")


def _post_form(url: str, payload: dict, headers: dict) -> dict:
    import urllib.parse

    req = urllib.request.Request(
        url,
        data=urllib.parse.urlencode(payload).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded", **headers},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8") or "{}")


def configured_provider() -> str | None:
    if os.getenv("TELNYX_API_KEY") and os.getenv("OPERATOR_FROM_NUMBER"):
        return "telnyx"
    if os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN") and os.getenv("OPERATOR_FROM_NUMBER"):
        return "twilio"
    return None


def send_sms(to: str, body: str, sender=None) -> dict:
    """sender is injectable for tests: sender(provider, to, body) -> dict."""
    provider = configured_provider()
    if provider is None:
        return {"ok": False, "provider": None,
                "error": "provider_not_configured — set TELNYX_API_KEY or Twilio env + OPERATOR_FROM_NUMBER"}
    if sender is not None:
        return sender(provider, to, body)
    from_number = os.environ["OPERATOR_FROM_NUMBER"]
    try:
        if provider == "telnyx":
            out = _post_json(
                "https://api.telnyx.com/v2/messages",
                {"from": from_number, "to": to, "text": body},
                {"Authorization": f"Bearer {os.environ['TELNYX_API_KEY']}"},
            )
            return {"ok": True, "provider": "telnyx", "id": (out.get("data") or {}).get("id")}
        sid = os.environ["TWILIO_ACCOUNT_SID"]
        basic = base64.b64encode(f"{sid}:{os.environ['TWILIO_AUTH_TOKEN']}".encode()).decode()
        out = _post_form(
            f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
            {"From": from_number, "To": to, "Body": body},
            {"Authorization": f"Basic {basic}"},
        )
        return {"ok": True, "provider": "twilio", "id": out.get("sid")}
    except Exception as e:
        return {"ok": False, "provider": provider, "error": f"send failed: {type(e).__name__}"}
