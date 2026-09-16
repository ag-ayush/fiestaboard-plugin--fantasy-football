"""Unit tests for ESPN response parsing and plugin output."""

import pytest


def fake_league():
    return {
        "teams": [
            {
                "id": 1,
                "name": "Tigers",
                "abbrev": "TIG",
                "record": {"overall": {"wins": 4, "losses": 1, "ties": 0}},
                "playoffSeed": 2,
            },
            {
                "id": 2,
                "name": "Wolves",
                "abbrev": "WLV",
                "record": {"overall": {"wins": 3, "losses": 2, "ties": 1}},
                "playoffSeed": 4,
            },
        ],
        "current_week": 3,
        "league_name": "Sunday League",
        "starter_count": 9,
        "schedule": [
            {
                "home": {
                    "teamId": 1,
                    "gamesPlayed": 6,
                    "totalPointsLive": 112.4,
                    "totalProjectedPointsLive": 114.25,
                },
                "away": {
                    "teamId": 2,
                    "gamesPlayed": 8,
                    "totalPointsLive": 98.7,
                    "totalProjectedPointsLive": 99.5,
                },
                "playoffTierType": "NONE",
            }
        ],
    }


def test_plugin_id(plugin_package, manifest):
    assert (
        plugin_package.FantasyFootballPlugin(manifest).plugin_id == "fantasy_football"
    )


def test_matchup_matches_team_name_and_orients_scores(plugin_package):
    result = plugin_package.FantasyFootballPlugin._matchup_for_team(
        fake_league(), "tigers"
    )
    assert result["league_name"] == "Sunday League"
    assert result["team1"] == "Tigers"
    assert result["team2"] == "Wolves"
    assert result["team1_abbrev"] == "TIG"
    assert result["team2_abbrev"] == "WLV"
    assert result["team1_record"] == "4-1"
    assert result["team2_record"] == "3-2-1"
    assert result["team1_rank"] == "2"
    assert result["team2_rank"] == "4"
    assert result["team1_players_remaining"] == "3"
    assert result["team2_players_remaining"] == "1"
    assert result["score1"] == "112.40"
    assert result["score2"] == "98.70"
    assert result["score_margin"] == "+13.70"


def test_matchup_matches_abbreviation_and_orients_away_score(plugin_package):
    result = plugin_package.FantasyFootballPlugin._matchup_for_team(
        fake_league(), "wlv"
    )
    assert result["team1"] == "Wolves"
    assert result["team2"] == "Tigers"
    assert result["score1"] == "98.70"
    assert result["score2"] == "112.40"
    assert result["score_margin"] == "-13.70"


def test_matchup_handles_a_bye(plugin_package):
    league = {
        "teams": [{"id": 1, "name": "Tigers", "abbrev": "TIG"}],
        "current_week": 3,
        "schedule": [{"away": {"teamId": 1, "totalPointsLive": 112.4}}],
    }
    result = plugin_package.FantasyFootballPlugin._matchup_for_team(league, "TIG")
    assert result["team2"] == "BYE"
    assert result["team2_abbrev"] == "BYE"
    assert result["score2"] == "0.00"


def test_fetch_data_returns_index_and_partial_errors(
    plugin_package, manifest, monkeypatch
):
    plugin = plugin_package.FantasyFootballPlugin(manifest)
    plugin.config = {
        "league_teams": [
            {"league_id": 42, "team": "TIG"},
            {"league_id": 99, "team": "Nope"},
        ]
    }

    def fetch(league_id, year):
        if league_id == 42:
            return fake_league()
        raise RuntimeError("not accessible")

    monkeypatch.setattr(plugin, "_fetch_league", fetch)
    result = plugin.fetch_data()
    assert result.available is True
    assert result.data["index"][0]["team1"] == "Tigers"
    assert "League 99" in result.data["fetch_errors"]


def test_fetch_data_rejects_invalid_year(plugin, manifest):
    plugin.config = {"league_teams": [{"league_id": 42, "team": "TIG"}], "year": "nope"}
    result = plugin.fetch_data()
    assert result.available is False
    assert result.error == "ESPN season year must be a number"


def test_fetch_data_returns_unavailable_when_every_league_fails(plugin, monkeypatch):
    monkeypatch.setattr(
        plugin,
        "_fetch_league",
        lambda *_: (_ for _ in ()).throw(RuntimeError("offline")),
    )
    result = plugin.fetch_data()
    assert result.available is False
    assert "offline" in result.error


def test_fetch_data_handles_malformed_entry(plugin):
    plugin.config = {"league_teams": ["not an object"]}
    result = plugin.fetch_data()
    assert result.available is False
    assert "League unknown" in result.error


def test_get_json_uses_private_cookies_and_repeated_views(
    plugin_package, manifest, monkeypatch
):
    plugin = plugin_package.FantasyFootballPlugin(manifest)
    plugin.config = {"espn_s2": "s2", "swid": "{id}"}
    captured = {}

    class Response:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"ok": True}

    def get(*args, **kwargs):
        captured.update(kwargs)
        return Response()

    monkeypatch.setattr(plugin_package.requests, "get", get)
    assert plugin._get_json(
        "https://example.test", [("view", "mTeam"), ("view", "mSettings")]
    ) == {"ok": True}
    assert captured["cookies"] == {"espn_s2": "s2", "SWID": "{id}"}
    assert captured["params"] == [("view", "mTeam"), ("view", "mSettings")]


def test_cookies_adds_missing_swid_braces(plugin):
    plugin.config.update(
        {"espn_s2": "cookie", "swid": "F7900531-DB89-4ED5-AD2F-245A579369A6"}
    )
    assert plugin._cookies() == {
        "espn_s2": "cookie",
        "SWID": "{F7900531-DB89-4ED5-AD2F-245A579369A6}",
    }


@pytest.mark.parametrize(
    ("status_code", "expected_exception"),
    [(401, PermissionError), (404, ValueError)],
)
def test_get_json_translates_access_errors(
    plugin, plugin_package, monkeypatch, status_code, expected_exception
):
    class Response:
        def __init__(self):
            self.status_code = status_code

    monkeypatch.setattr(
        plugin_package.requests, "get", lambda *args, **kwargs: Response()
    )
    with pytest.raises(expected_exception):
        plugin._get_json("https://example.test", [])


def test_get_json_returns_first_item_from_list_payload(
    plugin, plugin_package, monkeypatch
):
    class Response:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return [{"first": True}]

    monkeypatch.setattr(
        plugin_package.requests, "get", lambda *args, **kwargs: Response()
    )
    assert plugin._get_json("https://example.test", []) == {"first": True}


def test_fetch_league_requests_metadata_and_scoreboard(plugin, monkeypatch):
    responses = [
        {
            "scoringPeriodId": 4,
            "status": {
                "latestScoringPeriod": 5,
                "currentMatchupPeriod": 3,
                "finalScoringPeriod": 4,
            },
            "teams": [{"id": 1}],
            "settings": {
                "name": "Sunday League",
                "rosterSettings": {"lineupSlotCounts": {"0": 1, "2": 2, "20": 6}},
            },
        },
        {"schedule": [{"home": {"teamId": 1}}]},
    ]
    calls = []

    def get_json(url, params, headers=None):
        calls.append((url, params, headers))
        return responses.pop(0)

    monkeypatch.setattr(plugin, "_get_json", get_json)
    league = plugin._fetch_league(42, 2026)
    assert league["current_week"] == 4
    assert league["league_name"] == "Sunday League"
    assert league["starter_count"] == 3
    assert league["schedule"] == [{"home": {"teamId": 1}}]
    assert "lm-api-reads.fantasy.espn.com" in calls[0][0]
    assert calls[1][1][-1] == ("scoringPeriodId", 4)
    assert '"value": [3]' in calls[1][2]["x-fantasy-filter"]


def test_fetch_league_clamps_postseason_scoring_period(plugin, monkeypatch):
    responses = [
        {
            "scoringPeriodId": 18,
            "status": {"currentMatchupPeriod": 17, "finalScoringPeriod": 17},
            "teams": [],
        },
        {"schedule": []},
    ]
    monkeypatch.setattr(plugin, "_get_json", lambda *args, **kwargs: responses.pop(0))
    assert plugin._fetch_league(42, 2026)["current_week"] == 17


def test_fetch_league_rejects_missing_current_period(plugin, monkeypatch):
    monkeypatch.setattr(plugin, "_get_json", lambda *args, **kwargs: {"status": {}})
    with pytest.raises(ValueError, match="current scoring period"):
        plugin._fetch_league(42, 2026)


def test_matchup_rejects_unknown_team_and_missing_matchup(plugin_package):
    with pytest.raises(ValueError, match="was not found"):
        plugin_package.FantasyFootballPlugin._matchup_for_team(
            fake_league(), "Otters"
        )
    league = fake_league()
    league["schedule"] = []
    with pytest.raises(ValueError, match="no current matchup"):
        plugin_package.FantasyFootballPlugin._matchup_for_team(league, "TIG")


def test_matchup_uses_fallback_name_and_playoff_data(plugin_package):
    league = fake_league()
    league["teams"][0] = {
        "id": 1,
        "location": "The",
        "nickname": "Tigers",
        "abbrev": "TIG",
    }
    league["schedule"][0]["playoffTierType"] = "WINNERS_BRACKET"
    league["schedule"][0]["home"]["totalPointsLive"] = None
    league["schedule"][0]["home"]["totalPoints"] = 88
    league["schedule"][0]["home"]["totalProjectedPointsLive"] = -1
    result = plugin_package.FantasyFootballPlugin._matchup_for_team(league, "TIG")
    assert result["team1"] == "The Tigers"
    assert result["score1"] == "88.00"
    assert result["score1_projected"] == ""
    assert result["matchup_type"] == "PLAYOFF"


def test_players_remaining_is_blank_without_live_espn_data(plugin_package):
    league = fake_league()
    league["schedule"][0]["home"].pop("totalPointsLive")
    result = plugin_package.FantasyFootballPlugin._matchup_for_team(league, "TIG")
    assert result["team1_players_remaining"] == ""


def test_starter_count_excludes_bench_and_reserve_slots(plugin_package):
    settings = {"rosterSettings": {"lineupSlotCounts": {"0": 1, "20": 7, "21": 1, "24": 1}}}
    assert plugin_package.FantasyFootballPlugin._starter_count(settings) == 1


@pytest.mark.parametrize(
    ("config", "message"),
    [
        ({}, "At least one league team"),
        (
            {"league_teams": [{"league_id": 0, "team": "TIG"}]},
            "positive ESPN league ID",
        ),
        ({"league_teams": [{"league_id": 4, "team": ""}]}, "team name or abbreviation"),
        (
            {"league_teams": [{"league_id": 4, "team": "TIG"}], "espn_s2": "cookie"},
            "both ESPN S2",
        ),
        ({"league_teams": ["bad entry"]}, "must be an object"),
        (
            {
                "league_teams": [
                    {"league_id": 4, "team": "TIG"},
                    {"league_id": 4, "team": "tig"},
                ]
            },
            "duplicates league",
        ),
    ],
)
def test_validate_config(plugin_package, manifest, config, message):
    errors = plugin_package.FantasyFootballPlugin(manifest).validate_config(config)
    assert any(message in error for error in errors)


def test_manifest_declares_requested_index_fields(manifest):
    fields = manifest["variables"]["arrays"]["index"]["item_fields"]
    assert {
        "team1",
        "team2",
        "team1_abbrev",
        "team2_abbrev",
        "score1",
        "score2",
    } <= set(fields)
