"""Live ESPN fantasy-football matchup scores for FiestaBoard."""

from __future__ import annotations

import json
import logging
from typing import Any

import requests
from src.plugins.base import PluginBase, PluginResult

logger = logging.getLogger(__name__)
ESPN_LEAGUE_URL = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{year}/segments/0/leagues/{league_id}"
USER_AGENT = "FiestaBoard (https://github.com/FiestaBoard/FiestaBoard)"
REQUEST_TIMEOUT_SECONDS = 15


class FantasyFootballPlugin(PluginBase):
    """Fetch current matchups with only the ESPN endpoints this plugin needs."""

    @property
    def plugin_id(self) -> str:
        return "fantasy_football"

    def fetch_data(self) -> PluginResult:
        """Fetch the current matchup for each configured league/team pair."""
        entries = self.config.get("league_teams", [])
        try:
            year = int(self.config.get("year", 2026))
        except (TypeError, ValueError):
            return PluginResult(
                available=False, error="ESPN season year must be a number"
            )

        leagues: dict[int, dict[str, Any]] = {}
        matchups: list[dict[str, Any]] = []
        errors: list[str] = []
        current_week: int | None = None
        for entry in entries:
            try:
                league_id = int(entry["league_id"])
                selected_team = str(entry["team"]).strip()
                league = leagues.get(league_id)
                if league is None:
                    league = self._fetch_league(league_id, year)
                    leagues[league_id] = league
                if current_week is None:
                    current_week = league["current_week"]
                matchups.append(
                    self._matchup_for_team(league, selected_team)
                )
            except Exception as exc:
                league_label = (
                    entry.get("league_id", "unknown")
                    if isinstance(entry, dict)
                    else "unknown"
                )
                team_label = (
                    entry.get("team", "unknown")
                    if isinstance(entry, dict)
                    else "unknown"
                )
                message = f"League {league_label}, team {team_label}: {exc}"
                logger.warning("Fantasy football fetch failed: %s", message)
                errors.append(message)

        if not matchups:
            return PluginResult(
                available=False,
                error="; ".join(errors)
                or "No configured league teams returned a matchup",
            )
        return PluginResult(
            available=True,
            data={
                "index": matchups,
                "current_week": current_week or "",
                "fetch_errors": "; ".join(errors),
            },
        )

    def validate_config(self, config: dict[str, Any]) -> list[str]:
        entries = config.get("league_teams")
        if not isinstance(entries, list) or not entries:
            return ["At least one league team is required"]
        errors: list[str] = []
        seen: set[tuple[int, str]] = set()
        for position, entry in enumerate(entries, start=1):
            if not isinstance(entry, dict):
                errors.append(f"League team {position} must be an object")
                continue
            try:
                league_id = int(entry.get("league_id"))
                if league_id < 1:
                    raise ValueError
            except (TypeError, ValueError):
                errors.append(f"League team {position} needs a positive ESPN league ID")
                continue
            team = str(entry.get("team") or "").strip()
            if not team:
                errors.append(
                    f"League team {position} needs a team name or abbreviation"
                )
                continue
            key = (league_id, team.casefold())
            if key in seen:
                errors.append(
                    f"League team {position} duplicates league {league_id} and team {team}"
                )
            seen.add(key)
        if bool(config.get("espn_s2")) != bool(config.get("swid")):
            errors.append("Private leagues require both ESPN S2 and SWID cookies")
        return errors

    def _fetch_league(self, league_id: int, year: int) -> dict[str, Any]:
        """Fetch league metadata then its live scoreboard, without an SDK."""
        url = ESPN_LEAGUE_URL.format(year=year, league_id=league_id)
        metadata = self._get_json(url, [("view", "mTeam"), ("view", "mSettings")])
        status = metadata.get("status") or {}
        current_week = int(
            metadata.get("scoringPeriodId")
            or status.get("latestScoringPeriod")
            or status.get("currentScoringPeriod")
            or status.get("currentMatchupPeriod")
            or 0
        )
        final_week = int(status.get("finalScoringPeriod") or current_week)
        current_week = min(current_week, final_week)
        matchup_period = int(status.get("currentMatchupPeriod") or current_week)
        if current_week < 1 or matchup_period < 1:
            raise ValueError("ESPN did not provide a current scoring period")
        schedule_filter = {
            "schedule": {"filterMatchupPeriodIds": {"value": [matchup_period]}}
        }
        scoreboard = self._get_json(
            url,
            [
                ("view", "mMatchupScore"),
                ("view", "mScoreboard"),
                ("scoringPeriodId", current_week),
            ],
            headers={"x-fantasy-filter": json.dumps(schedule_filter)},
        )
        return {
            "teams": metadata.get("teams") or [],
            "schedule": scoreboard.get("schedule") or [],
            "current_week": current_week,
            "league_name": str((metadata.get("settings") or {}).get("name") or ""),
        }

    def _get_json(
        self,
        url: str,
        params: list[tuple[str, Any]],
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        request_headers = {"User-Agent": USER_AGENT}
        request_headers.update(headers or {})
        response = requests.get(
            url,
            params=params,
            headers=request_headers,
            cookies=self._cookies(),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code == 401:
            raise PermissionError(
                "private league access requires valid ESPN S2 and SWID cookies"
            )
        if response.status_code == 404:
            raise ValueError("ESPN league was not found for this season")
        response.raise_for_status()
        payload = response.json()
        return payload[0] if isinstance(payload, list) else payload

    def _cookies(self) -> dict[str, str] | None:
        espn_s2 = str(self.config.get("espn_s2") or "").strip()
        swid = str(self.config.get("swid") or "").strip()
        if swid and not (swid.startswith("{") and swid.endswith("}")):
            swid = f"{{{swid}}}"
        return {"espn_s2": espn_s2, "SWID": swid} if espn_s2 and swid else None

    @staticmethod
    def _matchup_for_team(league: dict[str, Any], selected_team: str) -> dict[str, Any]:
        teams = {
            int(team["id"]): team
            for team in league["teams"]
            if team.get("id") is not None
        }
        team_id, team = next(
            (
                (candidate_id, candidate)
                for candidate_id, candidate in teams.items()
                if selected_team.casefold()
                in {
                    FantasyFootballPlugin._team_name(candidate).casefold(),
                    str(candidate.get("abbrev") or "").casefold(),
                }
            ),
            (None, None),
        )
        if team is None or team_id is None:
            raise ValueError("team was not found in this ESPN league")
        matchup = next(
            (
                item
                for item in league["schedule"]
                if team_id
                in {
                    int((item.get("home") or {}).get("teamId", -1)),
                    int((item.get("away") or {}).get("teamId", -1)),
                }
            ),
            None,
        )
        if matchup is None:
            raise ValueError("team has no current matchup")
        home, away = matchup.get("home") or {}, matchup.get("away") or {}
        current, opponent = (
            (home, away) if int(home.get("teamId", -1)) == team_id else (away, home)
        )
        opponent_team = teams.get(int(opponent.get("teamId", -1)))
        is_playoff = matchup.get("playoffTierType", "NONE") != "NONE"
        return {
            "league_name": str(league.get("league_name") or "Unknown league"),
            "team1": FantasyFootballPlugin._team_name(team),
            "team2": FantasyFootballPlugin._team_name(opponent_team)
            if opponent_team
            else "BYE",
            "team1_abbrev": str(team.get("abbrev") or ""),
            "team2_abbrev": str(opponent_team.get("abbrev") or "BYE")
            if opponent_team
            else "BYE",
            "score1": FantasyFootballPlugin._format_score(current),
            "score2": FantasyFootballPlugin._format_score(opponent),
            "score1_projected": FantasyFootballPlugin._format_projected(current),
            "score2_projected": FantasyFootballPlugin._format_projected(opponent),
            "week": str(league["current_week"]),
            "matchup_type": "PLAYOFF" if is_playoff else "REGULAR",
        }

    @staticmethod
    def _team_name(team: dict[str, Any] | None) -> str:
        if not team:
            return "BYE"
        return str(
            team.get("name") or f"{team.get('location', '')} {team.get('nickname', '')}"
        ).strip()

    @staticmethod
    def _format_score(side: dict[str, Any]) -> str:
        score = side.get("totalPointsLive")
        if score is None:
            score = side.get("totalPoints", 0)
        return f"{float(score):.2f}"

    @staticmethod
    def _format_projected(side: dict[str, Any]) -> str:
        projected = side.get("totalProjectedPointsLive")
        return (
            ""
            if projected is None or float(projected) < 0
            else f"{float(projected):.2f}"
        )
