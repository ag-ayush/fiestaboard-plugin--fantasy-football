# Fantasy Football Scores Setup Guide

Configure current ESPN Fantasy Football matchups for use in FiestaBoard templates.

## Overview

**What it does:**

- Retrieves the live/current score and opponent for each selected ESPN team.
- Exposes projected scores, the scoring week, and playoff information when available.
- Supports public leagues and private leagues authenticated with ESPN browser cookies.

**Prerequisites:** An ESPN Fantasy Football league ID and the exact team name or abbreviation.
Private leagues also need the ESPN S2 and SWID cookies from an authenticated ESPN session.

## Quick Setup

### 1. Enable the Plugin

Install this repository as a custom FiestaBoard plugin, then enable **Fantasy
Football Scores** on the Integrations page.

### 2. Configure Fantasy Football Scores

Find the number after `leagueId=` in the ESPN Fantasy Football league URL. Add a
**League teams** entry for every matchup to display:

- **ESPN league ID**: the numeric league ID.
- **Team name or abbreviation**: ESPN's name or abbreviation for your team.

The pair is the entry's lookup key. Its position determines its template index:
the first entry is `fantasy_football.index.0`, the second is
`fantasy_football.index.1`, and so on.

Set the **ESPN season year** to the season to query. Use a refresh interval of at
least 60 seconds; 300 seconds is a good normal-use value.

For a private league, enter both masked credentials:

- **ESPN S2 cookie** (`espn_s2`)
- **ESPN SWID cookie** (`SWID`, including its braces)

To find them, sign in to ESPN in a desktop browser, then open Developer Tools:

1. In Chrome/Edge, use **F12** or **More tools → Developer tools**. In Firefox,
   use **F12** or **Tools → Browser Tools → Web Developer Tools**.
2. Open **Application** (Chrome/Edge) or **Storage** (Firefox), then expand
   **Cookies** and select `https://www.espn.com`.
3. Copy the cookie values named `espn_s2` and `SWID` into their matching masked
   FiestaBoard fields. Copy the value only, and keep the braces around SWID.

The [`espn-api` private-league credential guide](https://github.com/cwendt94/espn-api/discussions/150)
has browser-specific illustrations and alternatives if the cookie table is hard to find.

Treat both values as passwords. Do not add them to a template, commit them, or
share them in screenshots.

### 3. Create a Board Template

Add a page using the first configured matchup:

```
{{fantasy_football.index.0.team1_abbrev}} {{fantasy_football.index.0.score1}}
{{fantasy_football.index.0.team2_abbrev}} {{fantasy_football.index.0.score2}}
```

Use `score1_projected`, `score2_projected`, or `matchup_type` if those fit your
layout. A bye returns `BYE` for `team2` and `team2_abbrev`.

### 4. View on Your Board

Save the page, select it for your board, and wait for the configured refresh
interval. Confirm that the displayed names and scores correspond to ESPN's current
scoring week.

## Template Variables

See the complete variable table and examples in the [README](../README.md#template-variables).

## Configuration Reference

| Setting | Required | Notes |
| --- | --- | --- |
| League teams | Yes | Add at least one unique league ID + team name/abbreviation pair |
| ESPN season year | No | Defaults to 2026; minimum supported year is 2019 |
| ESPN S2 cookie | Private leagues | Must be supplied with SWID |
| ESPN SWID cookie | Private leagues | Must be supplied with ESPN S2 |
| Refresh interval | No | 60–3,600 seconds; defaults to 300 |

## Troubleshooting

| Problem | What to check |
| --- | --- |
| Team not found | Copy ESPN's exact team name or abbreviation; matching is case-insensitive. |
| League not found | Confirm the league ID and the selected ESPN season year. |
| Private league access error | Re-enter both current ESPN S2 and SWID cookies; either cookie alone is insufficient. |
| Scores are not changing | ESPN only updates as games score; confirm the refresh interval and current scoring week. |
