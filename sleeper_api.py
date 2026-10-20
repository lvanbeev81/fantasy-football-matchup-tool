"""Client for the Sleeper fantasy football API.

Public, read-only, no API key required.
Docs: https://docs.sleeper.app/
Rate limit: stay under ~1000 requests/minute.
"""

import json
import os
import time

import requests

BASE_URL = "https://api.sleeper.app/v1"
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "fantasy-matchup-tool")
PLAYERS_CACHE = os.path.join(CACHE_DIR, "players_nfl.json")
PLAYERS_CACHE_TTL = 7 * 24 * 3600  # refresh the 15MB player map weekly


def _get(path, **params):
    resp = requests.get(f"{BASE_URL}{path}", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_state():
    """Current NFL season state (week, season_type, ...)."""
    return _get("/state/nfl")


def get_user(username):
    """Resolve a Sleeper username to its user object (contains user_id)."""
    return _get(f"/user/{username}")


def get_leagues(user_id, season="2026"):
    """All NFL leagues for a user in a season."""
    return _get(f"/user/{user_id}/leagues/nfl/{season}")


def get_league(league_id):
    return _get(f"/league/{league_id}")


def get_rosters(league_id):
    return _get(f"/league/{league_id}/rosters")


def get_league_users(league_id):
    return _get(f"/league/{league_id}/users")


def get_matchups(league_id, week):
    """Matchup entries for a week. Two entries share a matchup_id = one game."""
    return _get(f"/league/{league_id}/matchups/{week}")


def get_projection(player_id, week, season="2026"):
    """Projected stats for one player in a week. Returns None if unavailable."""
    url = (
        f"https://api.sleeper.app/projections/nfl/player/{player_id}"
        f"?season_type=regular&season={season}&week={week}"
    )
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data or not data.get("stats"):
        return None
    return data["stats"]


def get_players():
    """Full NFL player map, cached locally for a week (it's ~15MB)."""
    if os.path.exists(PLAYERS_CACHE):
        age = time.time() - os.path.getmtime(PLAYERS_CACHE)
        if age < PLAYERS_CACHE_TTL:
            with open(PLAYERS_CACHE) as f:
                return json.load(f)
    os.makedirs(CACHE_DIR, exist_ok=True)
    players = _get("/players/nfl")
    with open(PLAYERS_CACHE, "w") as f:
        json.dump(players, f)
    return players


def describe_player(player_id, players):
    """Human-readable 'Name (POS, TEAM)' for a Sleeper player id."""
    p = players.get(str(player_id)) or {}
    name = p.get("full_name") or p.get("last_name") or str(player_id)
    pos = p.get("position") or ""
    team = p.get("team") or ""
    return f"{name} ({pos}, {team})".strip()


def scoring_key(league):
    """Which projection field matches this league's PPR setting."""
    rec = (league.get("scoring_settings") or {}).get("rec", 1)
    if rec == 1:
        return "pts_ppr"
    if rec == 0.5:
        return "pts_half_ppr"
    return "pts_std"
