# Fantasy Football Scores Plugin

Show live ESPN Fantasy Football matchup scores for the teams you choose.

**→ [Setup Guide](./docs/SETUP.md)**

## Overview

Fantasy Football Scores fetches the current ESPN scoring-period matchup for each
configured league/team pair. It uses FiestaBoard's built-in HTTP client and calls
only ESPN's team metadata and scoreboard endpoints, so no extra dependency is
installed with the plugin.

## Template Variables

### Current matchup

Each configured entry is exposed in the same order under `fantasy_football.index`.

| Variable | Example | Description |
| --- | --- | --- |
| `{{fantasy_football.index.0.team1}}` | `Tigers` | Configured ESPN team |
| `{{fantasy_football.index.0.team2}}` | `Wolves` | Current opponent, or `BYE` |
| `{{fantasy_football.index.0.team1_abbrev}}` | `TIG` | Configured team abbreviation |
| `{{fantasy_football.index.0.team2_abbrev}}` | `WLV` | Opponent abbreviation |
| `{{fantasy_football.index.0.score1}}` | `112.40` | Configured team's score |
| `{{fantasy_football.index.0.score2}}` | `98.70` | Opponent's score |
| `{{fantasy_football.index.0.score1_projected}}` | `114.25` | Configured team's projected score, when ESPN provides it |
| `{{fantasy_football.index.0.score2_projected}}` | `99.50` | Opponent's projected score, when ESPN provides it |
| `{{fantasy_football.index.0.week}}` | `3` | ESPN current scoring week |
| `{{fantasy_football.index.0.matchup_type}}` | `REGULAR` | `REGULAR` or `PLAYOFF` |
| `{{fantasy_football.index.0.is_playoff}}` | `false` | Whether ESPN reports a playoff matchup |

### League details

| Variable | Description |
| --- | --- |
| `{{fantasy_football.current_week}}` | Current week from the first configured league |
| `{{fantasy_football.fetch_errors}}` | Per-entry errors when at least one other entry succeeds |

## Example Templates

### Current score

```
{{fantasy_football.index.0.team1_abbrev}} {{fantasy_football.index.0.score1}}
{{fantasy_football.index.0.team2_abbrev}} {{fantasy_football.index.0.score2}}
```

## Configuration

| Setting | Required | Description |
| --- | --- | --- |
| League teams | Yes | One or more ESPN league ID + team-name/abbreviation pairs |
| ESPN season year | No | Season to query; defaults to 2026 |
| ESPN S2 cookie | Private leagues | `espn_s2` cookie, used only together with SWID |
| ESPN SWID cookie | Private leagues | SWID cookie, used only together with ESPN S2 |
| Refresh interval | No | Fetch interval from 60 to 3,600 seconds; defaults to 300 |

## Features

- Supports public and private ESPN Fantasy Football leagues.
- Keeps configured matchup order stable for template indexes.
- Reports live scores, projected scores, bye weeks, and playoff status.
- Uses a 15-second timeout on every ESPN request.

## Author

FiestaBoard Community
