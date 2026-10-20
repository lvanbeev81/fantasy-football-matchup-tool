"""Client for the ESPN fantasy football API.

ESPN's API is unofficial but stable. Public leagues work without auth;
private leagues need two cookies from a logged-in browser session:
  - espn_s2
  - SWID

How to grab them (30 seconds, in Chrome):
  1. Log in at fantasy.espn.com
  2. Open DevTools (F12) -> Application tab -> Cookies -> https://fantasy.espn.com
  3. Copy the values of `espn_s2` and `SWID`

Treat these like passwords: pass them as CLI flags, never commit them.
"""

import requests

BASE_URL = "https://fantasy.espn.com/apis/v3/sports/football/nfl"


def _get(league_id, season, params, swid=None, espn_s2=None):
    url = f"{BASE_URL}/{season}/segments/0/leagues/{league_id}"
    cookies = {}
    if swid:
        cookies["SWID"] = swid
    if espn_s2:
        cookies["espn_s2"] = espn_s2
    resp = requests.get(url, params=params, cookies=cookies, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_league(league_id, season="2026", swid=None, espn_s2=None):
    """League settings, teams, and schedule metadata."""
    return _get(
        league_id,
        season,
        [("view", "mSettings"), ("view", "mTeam")],
        swid=swid,
        espn_s2=espn_s2,
    )


def get_matchups(league_id, week, season="2026", swid=None, espn_s2=None):
    """Scoreboard for a scoring period: projected + actual scores per team.

    Returns the raw schedule entries for the week; each entry has `home` and
    `away` dicts with `teamId`, and `homeTotalScore` / `awayTotalScore`
    (projected before games, live during, final after).
    """
    data = _get(
        league_id,
        season,
        {"view": "mMatchupScore", "scoringPeriodId": week},
        swid=swid,
        espn_s2=espn_s2,
    )
    return [g for g in data.get("schedule", []) if g.get("matchupPeriodId") == week]


def get_team_rosters(league_id, week, season="2026", swid=None, espn_s2=None):
    """Current rosters with lineup slots for every team (for starter lists)."""
    data = _get(
        league_id,
        season,
        {"view": "mRoster", "scoringPeriodId": week},
        swid=swid,
        espn_s2=espn_s2,
    )
    return {t["id"]: t for t in data.get("teams", [])}


def team_name(team):
    return team.get("name") or f"Team {team.get('id')}"
