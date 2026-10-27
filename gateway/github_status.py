"""Real Tier 0 GitHub status for Operator — Slice 0 (2026-10-26).

Replaces the old mock_status stub. Tier 0 is read-only by definition:
this module only ever issues GET requests to the GitHub REST API.

Honesty rules (from registry/intake-checklist.md):
- Never fabricate a number. If GitHub does not answer, say so and say why.
- No token is ever committed or logged. An optional token is read from
  the GITHUB_TOKEN / GH_TOKEN environment variables only, and is needed
  for private repos. Public repos work with no token.
- An unwired project reports "unwired", never a guessed repo.
"""
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone

API = "https://api.github.com"


def _token() -> str | None:
    return os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN") or None


def _get(path: str, token: str | None, timeout: float = 8.0):
    req = urllib.request.Request(
        f"{API}{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "operator-gateway-slice0",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_repo_status(repo: str, fetcher=None, token: str | None = None) -> dict:
    """Return a status dict for 'owner/name'. Never raises for API errors.

    fetcher is injectable for tests: fetcher(path, token) -> parsed JSON.
    """
    get = fetcher or _get
    if token is None:
        token = _token()
    out = {
        "repo": repo,
        "ok": False,
        "source": "github-api",
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }
    try:
        meta = get(f"/repos/{repo}", token)
        out.update(
            {
                "ok": True,
                "private": bool(meta.get("private")),
                "default_branch": meta.get("default_branch") or "main",
                "pushed_at": meta.get("pushed_at"),
                # GitHub's open_issues_count includes PRs; we report the
                # PR count separately below and label this field honestly.
                "open_issues_and_prs": meta.get("open_issues_count"),
            }
        )
    except urllib.error.HTTPError as e:
        reason = {
            401: "auth required — set GITHUB_TOKEN in the gateway env (never in the repo)",
            403: "forbidden / rate-limited by GitHub",
            404: "not found or private without auth — if this repo is private, set GITHUB_TOKEN in the gateway env",
        }.get(e.code, f"GitHub HTTP {e.code}")
        out["error"] = reason
        return out
    except Exception as e:  # network, timeout, DNS — report, don't invent
        out["error"] = f"unreachable: {type(e).__name__}"
        return out

    # Best-effort extras: a failure here does not kill the repo status.
    try:
        prs = get(f"/repos/{repo}/pulls?state=open&per_page=100", token)
        out["open_prs"] = len(prs) if isinstance(prs, list) else None
    except Exception:
        out["open_prs"] = None
    try:
        commits = get(f"/repos/{repo}/commits?per_page=1", token)
        if isinstance(commits, list) and commits:
            c = commits[0]
            out["latest_commit"] = {
                "sha": (c.get("sha") or "")[:7],
                "date": ((c.get("commit") or {}).get("committer") or {}).get("date"),
                "message": (((c.get("commit") or {}).get("message") or "").splitlines() or [""])[0],
            }
    except Exception:
        out["latest_commit"] = None
    return out


def format_status(agent: dict, project: dict | None, status: dict | None) -> str:
    if not project:
        return (
            "OPERATOR\n"
            f"Agent: {agent['id']} ({agent['role']})\n"
            "Project: not named\n"
            "Tier 0: name a project with #id to bind a repo."
        )
    label = project["label"].upper()
    repo = (project.get("adapters") or {}).get("github")
    if not repo:
        return (
            f"{label}\n"
            f"Agent: {agent['id']}\n"
            "Repo: unwired — no GitHub adapter in registry/projects.json\n"
            "Tier 0: cannot check status until a repo is wired. No repo guessed."
        )
    if not status or not status.get("ok"):
        reason = (status or {}).get("error", "unknown error")
        checked = (status or {}).get("checked_at", "")
        return (
            f"{label}\n"
            f"Agent: {agent['id']}\n"
            f"Repo: {repo}\n"
            f"Checked: {checked}\n"
            f"Live status: unavailable — {reason}\n"
            "Source: github-api (real check, no mock numbers)"
        )
    lines = [
        label,
        f"Agent: {agent['id']}",
        f"Repo: {status['repo']} ({'private' if status.get('private') else 'public'})",
        f"Branch: {status.get('default_branch')}",
        f"Checked: {status.get('checked_at')}",
        f"Last push: {status.get('pushed_at') or 'unknown'}",
    ]
    if status.get("open_prs") is not None:
        lines.append(f"Open PRs: {status['open_prs']}")
    if status.get("open_issues_and_prs") is not None:
        lines.append(f"Open issues+PRs (GitHub count): {status['open_issues_and_prs']}")
    lc = status.get("latest_commit")
    if lc:
        lines.append(f"Latest commit: {lc['sha']} {lc.get('date') or ''} — {lc.get('message') or ''}")
    lines.append("Source: github-api (live Tier 0 read)")
    return "\n".join(lines)
