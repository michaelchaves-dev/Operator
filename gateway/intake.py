from parser import AGENT_INDEX, PROJECT_INDEX

WRITE_VERBS = {"fix", "commit", "patch", "deploy", "merge", "delete", "write"}
EMAIL_HINTS = ("email", "e-mail", "send me an email")
VOICE_HINTS = ("call me", "phone me", "voice")
BOTH_HINTS = ("both", "text and email")


def _tier_for(verb: str) -> int:
    if verb in {"deploy", "merge", "delete"}:
        return 3
    if verb in {"fix", "commit", "patch", "write"}:
        return 2
    if verb in {"issue", "issues"}:
        return 1
    return 0


def _deliver(text: str) -> str:
    lower = text.lower()
    if any(h in lower for h in VOICE_HINTS):
        return "voice"
    if any(h in lower for h in BOTH_HINTS):
        return "both"
    if any(h in lower for h in EMAIL_HINTS):
        return "email"
    return "sms"


def _when(text: str) -> str:
    lower = text.lower()
    if "when done" in lower or "when you finish" in lower:
        return "when-done"
    return "now"


def _ternary(project_id, needs_project, allowed) -> dict:
    project_t = 0 if not project_id else 1
    if needs_project and not project_id:
        project_t = 0
    write_t = 1 if not needs_project else (0 if not project_id else 1)
    allow_t = 1 if allowed else -1
    return {"project": project_t, "write": write_t, "allow": allow_t}


def build_packet(parsed: dict, sender: str, mask: str = "owner") -> dict:
    text = parsed.get("raw") or ""
    agent_id = parsed["agent"]
    project_id = parsed.get("project")
    verb = parsed.get("verb") or "status"
    agent = AGENT_INDEX[agent_id]
    project = PROJECT_INDEX.get(project_id) if project_id else None
    repo = None
    if project:
        repo = (project.get("adapters") or {}).get("github")

    tier = _tier_for(verb)
    deliver = _deliver(text)
    if deliver == "voice":
        deliver_live = "sms"
        voice = "assigned"
    else:
        deliver_live = deliver
        voice = "none"

    allowed = True
    block = None
    missing = []
    action = "A"

    if agent["projects"] != ["*"] and project_id and project_id not in agent["projects"]:
        allowed = False
        block = f"{agent_id} is not on {project_id}."
        action = "D"

    if tier > agent.get("max_tier", 0):
        allowed = False
        block = f"{agent_id} max tier is {agent.get('max_tier')}."
        action = "D"

    needs_project = verb in WRITE_VERBS or tier >= 2
    if needs_project and not project_id:
        missing.append("project_id")
        allowed = False
        block = block or "Which project?"
        action = "B"

    if needs_project and project_id and not repo:
        missing.append("repo")
        allowed = False
        block = block or f"{project_id} has no GitHub adapter yet."
        action = "D"

    if deliver == "voice":
        missing.append("voice_channel")

    if verb in {"deploy", "merge", "delete"}:
        action = "D" if action == "A" else action
        block = block or "T3 reserved. Reply CONFIRM when that slice ships."

    ask = text.strip() or verb
    total = [f"{verb} on {project_id or 'unspecified project'}"]
    if deliver_live != "sms":
        total.append(f"deliver via {deliver_live}")

    packet = {
        "who": {"sender": sender or "", "mask": mask},
        "project_id": project_id,
        "repo": repo,
        "ask": ask,
        "total": total,
        "agent_id": agent_id,
        "tier": tier,
        "allowed": allowed,
        "block_reason": block,
        "deliver": deliver_live,
        "when": _when(text),
        "when_at": None,
        "voice": voice,
        "voice_id": None,
        "approval_id": None,
        "missing": missing,
        "step0_action": action,
        "ternary": _ternary(project_id, needs_project, allowed),
    }
    return packet


def format_packet(packet: dict) -> str:
    t = packet.get("ternary") or {}
    lines = [
        "INTAKE",
        f"Who: {packet['who']['mask']} {packet['who']['sender']}",
        f"Repo: {packet['repo'] or packet['project_id'] or 'unspecified'}",
        f"Ask: {packet['ask']}",
        f"Total: {'; '.join(packet['total'])}",
        f"Agent: {packet['agent_id']}",
        f"Tier: {packet['tier']}",
        f"Allowed: {packet['allowed']}",
        f"Deliver: {packet['deliver']} / {packet['when']}",
        f"Voice: {packet['voice']}",
        f"Step0: {packet.get('step0_action')}",
        f"Ternary: project {t.get('project')} write {t.get('write')} allow {t.get('allow')}",
    ]
    if packet.get("block_reason"):
        lines.append(f"Stop: {packet['block_reason']}")
    if packet.get("missing"):
        lines.append(f"Missing: {', '.join(packet['missing'])}")
    return "\n".join(lines)
