# Fantasy Football Matchup Tool

Weekly matchup previews across your Sleeper and ESPN fantasy leagues, from the
terminal. No logins, no browser scraping — just the platforms' APIs.

```
$ python matchup.py --sleeper-user yourname

My Dynasty -- Week 7 (Sleeper, pts_ppr)
  You (112.4)  vs  Dezpacito (108.1)   [edge +4.3]
  Your starters:
    Josh Allen (QB, BUF)                23.2
    ...
```

## Setup

Requires Python 3.9+.

```
pip install -r requirements.txt
```

## Usage

**Sleeper** — public API, no login needed:

```
python matchup.py --sleeper-user <username> [--week 7] [--season 2026]
```

**ESPN** — private leagues need two cookies from a logged-in browser session:

```
python matchup.py --espn-league-id <id> --espn-swid <swid> --espn-s2 <espn_s2>
```

How to grab the cookies (30 seconds, Chrome):
1. Log in at fantasy.espn.com
2. DevTools (F12) → Application tab → Cookies → `https://fantasy.espn.com`
3. Copy the values of `espn_s2` and `SWID`

Your league ID is in the URL when you open your league
(`fantasy.espn.com/football/league?leagueId=12345`).

Treat the cookies like passwords: pass them as flags, never commit them.

**Both platforms at once:** pass both sets of flags in one command.

If `--week` is omitted, it previews the upcoming week automatically.

## How it works

- `sleeper_api.py` — thin client over Sleeper's free read-only API
  (leagues, rosters, matchups, weekly player projections). The 15MB player
  map is cached locally for a week. Projections use the field matching your
  league's PPR setting (`pts_ppr` / `pts_half_ppr` / `pts_std`).
- `espn_api.py` — client over ESPN's (unofficial) fantasy API.
- `matchup.py` — CLI that pulls both and prints side-by-side previews.

## Roadmap

- [ ] Start/sit suggestions (compare starter projection vs best bench option)
- [ ] Waiver-wire targets from Sleeper's trending-players endpoint
- [ ] Season-long record vs. projected record ("luck" differential)

## License

MIT
