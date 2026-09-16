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

To find them in Chrome, sign in to your ESPN Fantasy Football account at
`https://fantasy.espn.com`, then:

1. Right-click anywhere on the page and choose **Inspect**.
2. Open the **Application** tab.
3. Under **Storage**, expand **Cookies** and select `https://fantasy.espn.com`.
4. Copy the cookie values named `espn_s2` and `SWID` into their matching masked
   FiestaBoard fields. Copy the value only, and keep the braces around SWID.

These values normally remain the same between browser sessions, but ESPN can
replace them. If private-league access stops working, retrieve the current values
again from the same ESPN account that belongs to the league.

The [`espn-api` private-league credential guide](https://github.com/cwendt94/espn-api/discussions/150)
has browser-specific illustrations and alternatives if the cookie table is hard to find.

Treat both values as passwords. Do not add them to a template, commit them, or
share them in screenshots or chat. The plugin will add SWID braces if they are
accidentally omitted, but copying the full cookie value is preferred.

### 3. Create a Board Template

Add a page using the first configured matchup:

```
{{fantasy_football.index.0.team1_abbrev}} {{fantasy_football.index.0.team1_score}}
{{fantasy_football.index.0.team2_abbrev}} {{fantasy_football.index.0.team2_score}}
```

Use `score_margin`, `team1_score_projected`, `team2_score_projected`, `team1_record`,
`team1_rank`, or `team1_players_remaining` if those fit your layout.
`score_margin` is positive when team1 leads and negative when it trails. A bye
returns `BYE` for `team2` and `team2_abbrev`. Players remaining is blank whenever
ESPN does not provide live matchup data.

### 4. View on Your Board

Save the page, select it for your board, and wait for the configured refresh
interval. Confirm that the displayed names and scores correspond to ESPN's current
scoring week.

### Optional: Create the Bundled Demo Page

After you save at least one **League teams** entry, FiestaBoard's Integration
settings for Fantasy Football Scores offers **Create Demo Page**. It creates a
managed example page for your configured board type using the first matchup
(`fantasy_football.index.0`). Use **Recreate Demo Page** there if you want to
replace that example with a fresh copy.

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
