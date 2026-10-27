"""Slice 1 tests — provider webhooks, signatures, audit, outbound.

Run: cd gateway && python -m pytest test_slice1.py -q
No network, no real secrets: signatures are computed in-test from the
published provider algorithms; provider sends are injected fakes.
"""
import base64
import hashlib
import hmac as hmac_mod
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import providers


# ---------- Twilio signature (spec formula computed independently here)

def _twilio_sig(token, url, params):
    payload = url + "".join(f"{k}{params[k]}" for k in sorted(params))
    return base64.b64encode(hmac_mod.new(token.encode(), payload.encode(), hashlib.sha1).digest()).decode()


def test_twilio_signature_valid_and_invalid(monkeypatch):
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "test-token")
    monkeypatch.delenv("OPERATOR_DEV_MODE", raising=False)
    url = "https://example.test/webhook/twilio"
    params = {"From": "+10000000000", "To": "+19999999999", "Body": "@roman #operator status"}
    sig = _twilio_sig("test-token", url, params)
    ok, _ = providers.verify_twilio(url, params, sig)
    assert ok is True
    ok2, why2 = providers.verify_twilio(url, params, "bogus")
    assert ok2 is False and "bad" in why2


def test_twilio_fails_closed_without_token(monkeypatch):
    monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("OPERATOR_DEV_MODE", raising=False)
    ok, why = providers.verify_twilio("https://x.test/", {}, "anything")
    assert ok is False and "fails closed" in why


def test_dev_mode_skips_signature_explicitly(monkeypatch):
    monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)
    monkeypatch.setenv("OPERATOR_DEV_MODE", "1")
    ok, why = providers.verify_twilio("https://x.test/", {}, None)
    assert ok is True and "dev-mode" in why


def test_parse_twilio():
    msg = providers.parse_twilio({"From": "+1", "To": "+2", "Body": "hi", "MessageSid": "SM1"})
    assert (msg.provider, msg.sender, msg.body, msg.message_id) == ("twilio", "+1", "hi", "SM1")


def test_twiml_escapes():
    xml = providers.twiml_reply("a < b & c")
    assert "&lt;" in xml and "<Message>" in xml


# ---------- Telnyx parsing + Ed25519 verification

def _telnyx_body(event="message.received", text="@roman #operator status"):
    return json.dumps({
        "data": {
            "event_type": event,
            "payload": {
                "id": "msg-1",
                "from": {"phone_number": "+10000000000"},
                "to": [{"phone_number": "+19999999999"}],
                "text": text,
            },
        }
    }).encode()


def test_parse_telnyx_inbound():
    msg = providers.parse_telnyx(_telnyx_body())
    assert msg.provider == "telnyx"
    assert msg.sender == "+10000000000"
    assert msg.to == "+19999999999"
    assert msg.body == "@roman #operator status"


def test_parse_telnyx_ignores_outbound_events():
    assert providers.parse_telnyx(_telnyx_body(event="message.finalized")) is None


def test_telnyx_ed25519_roundtrip(monkeypatch):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    priv = Ed25519PrivateKey.generate()
    pub_raw = priv.public_key().public_bytes_raw()
    monkeypatch.setenv("TELNYX_PUBLIC_KEY", base64.b64encode(pub_raw).decode())
    monkeypatch.delenv("OPERATOR_DEV_MODE", raising=False)
    body = _telnyx_body()
    import time as _t
    ts = str(int(_t.time()))
    sig = base64.b64encode(priv.sign(f"{ts}|".encode() + body)).decode()
    ok, _ = providers.verify_telnyx(body, sig, ts)
    assert ok is True
    ok2, _ = providers.verify_telnyx(body + b" ", sig, ts)
    assert ok2 is False


def test_telnyx_fails_closed_without_key(monkeypatch):
    monkeypatch.delenv("TELNYX_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("OPERATOR_DEV_MODE", raising=False)
    ok, why = providers.verify_telnyx(b"{}", "x", "1")
    assert ok is False and "fails closed" in why


# ---------- Audit

def test_audit_masks_sender_and_has_no_body(tmp_path, monkeypatch):
    monkeypatch.setenv("OPERATOR_AUDIT_LOG", str(tmp_path / "audit.jsonl"))
    from audit import mask_number, write_audit
    assert mask_number("+16035551234") == "***1234"
    packet = {"who": {"sender": "+16035551234", "mask": "owner"}, "agent_id": "roman",
              "project_id": "operator", "repo": "michaelchaves-dev/Operator", "tier": 0,
              "allowed": True, "deliver": "sms", "when": "now", "step0_action": "A",
              "block_reason": None}
    row = write_audit(packet, provider="telnyx", message_id="m1")
    assert row["sender_masked"] == "***1234"
    lines = (tmp_path / "audit.jsonl").read_text().strip().splitlines()
    assert len(lines) == 1
    assert "603555" not in lines[0]  # full number never logged


# ---------- Outbound

def test_outbound_not_configured_is_honest(monkeypatch):
    for var in ("TELNYX_API_KEY", "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "OPERATOR_FROM_NUMBER"):
        monkeypatch.delenv(var, raising=False)
    import outbound
    result = outbound.send_sms("+10000000000", "hello")
    assert result["ok"] is False and "not_configured" in result["error"]


def test_outbound_uses_injected_sender(monkeypatch):
    monkeypatch.setenv("TELNYX_API_KEY", "k")
    monkeypatch.setenv("OPERATOR_FROM_NUMBER", "+19999999999")
    import outbound
    seen = {}
    def fake(provider, to, body):
        seen.update(provider=provider, to=to, body=body)
        return {"ok": True, "provider": provider, "id": "x"}
    result = outbound.send_sms("+10000000000", "hi", sender=fake)
    assert result["ok"] is True and seen["provider"] == "telnyx"


# ---------- Full-app integration (needs httpx for TestClient; skipped without)

def test_app_twilio_webhook_end_to_end(monkeypatch, tmp_path):
    pytest = __import__("pytest")
    httpx = pytest.importorskip("httpx")  # noqa: F841
    monkeypatch.setenv("OPERATOR_DEV_MODE", "1")
    monkeypatch.setenv("OPERATOR_ALLOWLIST", "+10000000000")
    monkeypatch.setenv("OPERATOR_AUDIT_LOG", str(tmp_path / "a.jsonl"))
    import importlib
    import app as app_module
    importlib.reload(app_module)
    from fastapi.testclient import TestClient
    client = TestClient(app_module.app)
    r = client.post("/webhook/twilio", data={"From": "+10000000000", "To": "+19999999999",
                                             "Body": "@roman #operator status", "MessageSid": "SM9"})
    assert r.status_code == 200
    assert "<Message>" in r.text and "OPERATOR" in r.text
    r2 = client.post("/notify", json={"text": "hi"})
    assert r2.status_code == 503  # notify token unset -> fails closed
