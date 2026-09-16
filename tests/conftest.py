"""Shared fixtures for the FiestaBoard plugin test suite."""

import json
from pathlib import Path

import plugins.fantasy_football as fantasy_football_module
import pytest

ROOT = Path(__file__).parent.parent


@pytest.fixture(scope="session")
def plugin_package():
    return fantasy_football_module


@pytest.fixture
def manifest():
    return json.loads((ROOT / "manifest.json").read_text())


@pytest.fixture
def plugin(manifest):
    instance = fantasy_football_module.FantasyFootballPlugin(manifest)
    instance.config = {"league_teams": [{"league_id": 42, "team": "TIG"}]}
    return instance
