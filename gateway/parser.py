import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = json.loads((ROOT / "registry" / "projects.json").read_text())
AGENTS = json.loads((ROOT / "registry" / "agents.json").read_text())

AGENT_INDEX = {}
for agent in AGENTS["agents"]:
    AGENT_INDEX[agent["id"].lower()] = agent
    for alias in agent.get("aliases", []):
        AGENT_INDEX[alias.lower()] = agent

PROJECT_INDEX = {}
for project in PROJECTS["projects"]:
    PROJECT_INDEX[project["id"].lower()] = project
    for alias in project.get("aliases", []):
        PROJECT_INDEX[alias.lower()] = project

AGENT_RE = re.compile(r"(?:@|/)?([A-Za-z][A-Za-z0-9_-]*)", re.I)
PROJECT_RE = re.compile(r"#([A-Za-z][A-Za-z0-9_-]*)")


def parse(body: str) -> dict:
    text = (body or "").strip()
    project = None
    agent = AGENTS["default_agent"]

    project_hit = PROJECT_RE.search(text)
    if project_hit:
        key = project_hit.group(1).lower()
        if key in PROJECT_INDEX:
            project = PROJECT_INDEX[key]["id"]

    at = re.search(r"@([A-Za-z][A-Za-z0-9_-]*)", text)
    if at and at.group(1).lower() in AGENT_INDEX:
        agent = AGENT_INDEX[at.group(1).lower()]["id"]
    else:
        first = AGENT_RE.match(text)
        if first and first.group(1).lower() in AGENT_INDEX:
            agent = AGENT_INDEX[first.group(1).lower()]["id"]

    lower = text.lower()
    verb = "status"
    if any(w in lower for w in ("inspect", "review", "look at")):
        verb = "inspect"
    elif any(w in lower for w in ("issue", "issues")):
        verb = "issues"
    elif any(w in lower for w in ("commit", "commits")):
        verb = "commits"
    elif "help" in lower or "who" in lower:
        verb = "help"

    return {
        "raw": text,
        "agent": agent,
        "project": project,
        "verb": verb,
    }
