"""Slice 0 tests — Roman routing + real Tier 0 status formatting.

Run: cd gateway && python -m pytest test_slice0.py -q
No network: github_status fetcher is injected with canned GitHub JSON.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from github_status import fetch_repo_status, format_status
from intake import build_packet
from parser import AGENT_INDEX, parse


def test_roman_and_rome_route_to_roman():
    assert parse("@roman #operator status")["agent"] == "roman"
    assert parse("@rome #aim status")["agent"] == "roman"
    assert parse("roman #operator status")["agent"] == "roman"


def test_roman_in_registry_with_tier2_ceiling_no_merge():
    roman = AGENT_INDEX["roman"]
    assert roman["max_tier"] == 2
    assert roman["merge"] is False
    assert roman["deploy"] is False
    assert roman["projects"] == ["*"]


def test_bella_still_default_router():
    assert parse("status")["agent"] == "bella"


def test_roman_packet_allowed_for_tier0_status():
    packet = build_packet(parse("@roman #operator status"), sender="+10000000000")
    assert packet["allowed"] is True
    assert packet["tier"] == 0
    assert packet["agent_id"] == "roman"
    assert packet["repo"] == "michaelchaves-dev/Operator"


def test_wired_adapters():
    from parser import PROJECT_INDEX
    assert PROJECT_INDEX["aim"]["adapters"]["github"] == "michaelchaves-dev/AIM"
    assert PROJECT_INDEX["subtractoken"]["adapters"]["github"] == "michaelchaves-dev/subtractoken-router"
    assert PROJECT_INDEX["bellaos"]["adapters"]["github"] == "michaelchaves-dev/bellaOS"
    # Zali deliberately unwired: two candidate repos, do not guess.
    assert PROJECT_INDEX["zali"]["adapters"]["github"] is None


def _fake_fetcher(path, token):
    if path.endswith("/pulls?state=open&per_page=100"):
        return [{}, {}]
    if path.endswith("/commits?per_page=1"):
        return [{
            "sha": "ba223f4feee4259d5d71af39a91d571d10975603",
            "commit": {"committer": {"date": "2026-10-06T17:29:53Z"},
                        "message": "docs(ip): add notice\n\nbody"},
        }]
    return {
        "private": False,
        "default_branch": "main",
        "pushed_at": "2026-10-06T17:29:53Z",
        "open_issues_count": 3,
    }


def test_fetch_status_real_shape_no_mock():
    s = fetch_repo_status("michaelchaves-dev/Operator", fetcher=_fake_fetcher, token="")
    assert s["ok"] is True
    assert s["open_prs"] == 2
    assert s["latest_commit"]["sha"] == "ba223f4"


def test_fetch_status_404_is_honest_not_fabricated():
    import urllib.error
    def boom(path, token):
        raise urllib.error.HTTPError(url=path, code=404, msg="nf", hdrs=None, fp=None)
    s = fetch_repo_status("michaelchaves-dev/AIM", fetcher=boom, token="")
    assert s["ok"] is False
    assert "private" in s["error"]


def test_format_status_unwired_never_guesses():
    from parser import PROJECT_INDEX
    txt = format_status(AGENT_INDEX["roman"], PROJECT_INDEX["zali"], None)
    assert "unwired" in txt
    assert "No repo guessed" in txt
