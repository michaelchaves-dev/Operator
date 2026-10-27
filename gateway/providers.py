"""Provider webhook adapters — Slice 1 scaffold (2026-10-26).

Inbound SMS from a real carrier lands here before it ever touches intake.

Design rules (Operator registry / intake checklist):
- Secrets live ONLY in environment variables. Nothing provider-specific
  is committed, logged, or returned in a reply.
- Signature verification FAILS CLOSED. If a provider's signing secret /
  public key is not configured, the webhook refuses the request unless
  OPERATOR_DEV_MODE=1 is explicitly set (local development only).
- Parsers only normalize: provider, from, to, body, message_id.
  Routing / tiers / allowlist all stay in app + intake, one plane.
"""
import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass


@dataclass
class InboundSms:
    provider: str
    sender: str
    to: str
    body: str
    message_id: str | None = None


def dev_mode() -> bool:
    return os.getenv("OPERATOR_DEV_MODE") == "1"


# ---------------------------------------------------------------- Twilio
# Twilio signs: base64(HMAC-SHA1(auth_token, url + sorted(param+value...)))
# Header: X-Twilio-Signature. Webhook content type: form-urlencoded.

def twilio_expected_signature(auth_token: str, url: str, params: dict) -> str:
    payload = url + "".join(f"{k}{params[k]}" for k in sorted(params))
    digest = hmac.new(auth_token.encode(), payload.encode(), hashlib.sha1).digest()
    return base64.b64encode(digest).decode()


def verify_twilio(url: str, params: dict, header_signature: str | None) -> tuple[bool, str]:
    token = os.getenv("TWILIO_AUTH_TOKEN")
    if not token:
        if dev_mode():
            return True, "dev-mode: TWILIO_AUTH_TOKEN unset, signature skipped"
        return False, "TWILIO_AUTH_TOKEN not configured — webhook fails closed"
    if not header_signature:
        return False, "missing X-Twilio-Signature"
    expected = twilio_expected_signature(token, url, params)
    if hmac.compare_digest(expected, header_signature):
        return True, "ok"
    return False, "bad Twilio signature"


def parse_twilio(params: dict) -> InboundSms:
    return InboundSms(
        provider="twilio",
        sender=params.get("From", ""),
        to=params.get("To", ""),
        body=params.get("Body", ""),
        message_id=params.get("MessageSid"),
    )


def twiml_reply(text: str) -> str:
    from xml.sax.saxutils import escape

    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response><Message>{escape(text)}</Message></Response>"
    )


# ---------------------------------------------------------------- Telnyx
# Telnyx signs with Ed25519. Headers: telnyx-signature-ed25519 (base64),
# telnyx-timestamp (unix seconds). Signed content: f"{timestamp}|{raw_body}"
# Public key: TELNYX_PUBLIC_KEY env, base64 — the raw 32-byte key as shown
# in Mission Control (also accepts a base64 DER/SPKI blob, tried second).

def verify_telnyx(raw_body: bytes, signature_b64: str | None, timestamp: str | None,
                  tolerance_seconds: int = 300) -> tuple[bool, str]:
    key_b64 = os.getenv("TELNYX_PUBLIC_KEY")
    if not key_b64:
        if dev_mode():
            return True, "dev-mode: TELNYX_PUBLIC_KEY unset, signature skipped"
        return False, "TELNYX_PUBLIC_KEY not configured — webhook fails closed"
    if not signature_b64 or not timestamp:
        return False, "missing Telnyx signature headers"
    try:
        ts = int(timestamp)
    except ValueError:
        return False, "bad Telnyx timestamp"
    if abs(time.time() - ts) > tolerance_seconds:
        return False, "Telnyx timestamp outside tolerance"
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.hazmat.primitives.serialization import load_der_public_key

        key_bytes = base64.b64decode(key_b64)
        try:
            key = Ed25519PublicKey.from_public_bytes(key_bytes)
        except Exception:
            key = load_der_public_key(key_bytes)
        signed = f"{timestamp}|".encode() + raw_body
        key.verify(base64.b64decode(signature_b64), signed)
        return True, "ok"
    except Exception as e:  # InvalidSignature or decode errors — refuse
        return False, f"bad Telnyx signature ({type(e).__name__})"


def parse_telnyx(raw_body: bytes) -> InboundSms | None:
    """Return None for non-message events (delivery reports etc.)."""
    try:
        doc = json.loads(raw_body.decode("utf-8"))
    except Exception:
        return None
    data = doc.get("data") or {}
    event_type = data.get("event_type")
    if event_type is not None and event_type != "message.received":
        # Telnyx also posts message.sent / message.finalized — not inbound asks.
        return None
    payload = data.get("payload") or doc
    sender = ((payload.get("from") or {}).get("phone_number")
              if isinstance(payload.get("from"), dict) else payload.get("from", ""))
    to_list = payload.get("to") or []
    to = ""
    if isinstance(to_list, list) and to_list:
        first = to_list[0]
        to = first.get("phone_number", "") if isinstance(first, dict) else str(first)
    elif isinstance(to_list, dict):
        to = to_list.get("phone_number", "")
    return InboundSms(
        provider="telnyx",
        sender=sender or "",
        to=to,
        body=payload.get("text", "") or payload.get("body", ""),
        message_id=payload.get("id"),
    )
