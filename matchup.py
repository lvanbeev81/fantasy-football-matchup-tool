#!/usr/bin/env python3
"""Weekly fantasy football matchup previews across Sleeper and ESPN leagues.

Sleeper (no login needed):
    python matchup.py --sleeper-user <username> [--week 7]

ESPN (private leagues need cookies -- see README):
    python matchup.py --espn-league-id <id> --espn-swid <swid> --espn-s2 <espn_s2> [--week 7]

Both at once:
    python matchup.py --sleeper-user <username> --espn-league-id <id> ...
"""

import argparse
import sys

import espn_api
import sleeper_api


def sleeper_preview(username, week, season):
    user = sleeper_api.get_user(username)
    leagues = sleeper_api.get_leagues(user["user_id"], season=season)
    if not leagues:
        print(f"No {season} leagues found for '{username}'.")
        return

    players = sleeper_api.get_players()
    for league in leagues:
        name = league.get("name", "Unnamed league")
        key = sleeper_api.scoring_key(league)
        matchups = sleeper_api.get_matchups(league["league_id"], week)
        rosters = {r["roster_id"]: r for r in sleeper_api.get_rosters(league["league_id"])}
        users = {u["user_id"]: u for u in sleeper_api.get_league_users(league["league_id"])}

        # find my roster and my matchup
        my_roster = next(
            (r for r in rosters.values() if r.get("owner_id") == user["user_id"]), None
        )
        if my_roster is None:
            print(f"\n{name}: you don't have a roster in this league.")
            continue
        my_entry = next(
            (m for m in matchups if m["roster_id"] == my_roster["roster_id"]), None
        )
        if my_entry is None:
            print(f"\n{name}: no matchup found for week {week}.")
            continue
        opp_entry = next(
            m for m in matchups if m["matchup_id"] == my_entry["matchup_id"]
            and m["roster_id"] != my_roster["roster_id"]
        )
        opp_roster = rosters[opp_entry["roster_id"]]
        opp_user = users.get(opp_roster.get("owner_id"), {})
        opp_name = (
            opp_user.get("metadata", {}).get("team_name")
            or opp_user.get("display_name")
            or f"Roster {opp_entry['roster_id']}"
        )

        def team_lines(entry):
            lines, total = [], 0.0
            for pid in entry["starters"]:
                proj = sleeper_api.get_projection(pid, week, season=season)
                pts = (proj or {}).get(key, 0.0) or 0.0
                total += pts
                lines.append(f"  {sleeper_api.describe_player(pid, players):<32} {pts:5.1f}")
            return lines, total

        my_lines, my_total = team_lines(my_entry)
        opp_lines, opp_total = team_lines(opp_entry)
        edge = my_total - opp_total
        edge_str = f"+{edge:.1f}" if edge >= 0 else f"{edge:.1f}"

        print(f"\n{name} -- Week {week} (Sleeper, {key})")
        print(f"  You ({my_total:.1f})  vs  {opp_name} ({opp_total:.1f})   [edge {edge_str}]")
        print("  Your starters:")
        print("\n".join(my_lines))
        print(f"  {opp_name} starters:")
        print("\n".join(opp_lines))


def espn_preview(league_id, week, season, swid, espn_s2):
    games = espn_api.get_matchups(league_id, week, season=season, swid=swid, espn_s2=espn_s2)
    if not games:
        print(f"\nESPN league {league_id}: no games found for week {week}.")
        return
    rosters = espn_api.get_team_rosters(league_id, week, season=season, swid=swid, espn_s2=espn_s2)
    print(f"\nESPN league {league_id} -- Week {week}")
    for g in games:
        home_id, away_id = g["home"]["teamId"], g["away"]["teamId"]
        home = rosters.get(home_id, {"name": f"Team {home_id}"})
        away = rosters.get(away_id, {"name": f"Team {away_id}"})
        hs = g.get("home", {}).get("totalPoints", 0) or 0
        aws = g.get("away", {}).get("totalPoints", 0) or 0
        print(f"  {espn_api.team_name(home):<28} {hs:6.1f} (proj)")
        print(f"  {espn_api.team_name(away):<28} {aws:6.1f} (proj)")


def main():
    parser = argparse.ArgumentParser(description="Fantasy football weekly matchup previews.")
    parser.add_argument("--sleeper-user", help="Sleeper username")
    parser.add_argument("--espn-league-id", help="ESPN league ID")
    parser.add_argument("--espn-swid", help="ESPN SWID cookie (private leagues)")
    parser.add_argument("--espn-s2", help="ESPN espn_s2 cookie (private leagues)")
    parser.add_argument("--week", type=int, help="NFL week (default: upcoming)")
    parser.add_argument("--season", default="2026", help="Season (default: 2026)")
    args = parser.parse_args()

    if not args.sleeper_user and not args.espn_league_id:
        parser.error("pass --sleeper-user and/or --espn-league-id")

    week = args.week
    if week is None:
        state = sleeper_api.get_state()
        # display_week is the week just played/in progress; preview the next one
        week = int(state.get("display_week", 1)) + 1

    try:
        if args.sleeper_user:
            sleeper_preview(args.sleeper_user, week, args.season)
        if args.espn_league_id:
            espn_preview(args.espn_league_id, week, args.season, args.espn_swid, args.espn_s2)
    except Exception as exc:  # noqa: BLE001 -- CLI: surface the error plainly
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
