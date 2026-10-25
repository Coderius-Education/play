"""Coverage tests for the Database class — nested keys, fallbacks, edge cases."""

import json
import os

import pytest

import play


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


@pytest.fixture
def db_path(tmp_path):
    """A database file path that does not exist yet."""
    return str(tmp_path / "scores.json")


def test_database_creates_file(db_path):
    """Database should create a new JSON file if it doesn't exist."""
    assert not os.path.exists(db_path)
    play.new_database(db_filename=db_path)
    with open(db_path) as f:
        assert json.load(f) == {}


def test_database_loads_existing_data(db_path):
    """Database should load existing data from a JSON file."""
    with open(db_path, "w") as f:
        json.dump({"score": 42}, f)

    db = play.new_database(db_filename=db_path)
    assert db.get_data("score") == 42


def test_database_set_and_get(db_path):
    """Basic set and get should work."""
    db = play.new_database(db_filename=db_path)
    db.set_data("name", "Alice")
    assert db.get_data("name") == "Alice"


def test_database_get_fallback(db_path):
    """get_data with a missing key should return the fallback."""
    db = play.new_database(db_filename=db_path)
    assert db.get_data("missing", fallback=99) == 99


def test_database_get_fallback_default_none(db_path):
    """get_data with a missing key and no fallback should return None."""
    db = play.new_database(db_filename=db_path)
    assert db.get_data("missing") is None


def test_database_nested_keys_get(db_path):
    """get_data with colon-delimited nested keys should traverse the dict."""
    with open(db_path, "w") as f:
        json.dump({"player": {"stats": {"score": 100}}}, f)

    db = play.new_database(db_filename=db_path)
    assert db.get_data("player:stats:score") == 100


def test_database_nested_keys_get_fallback(db_path):
    """Nested get_data with a missing intermediate key returns fallback."""
    with open(db_path, "w") as f:
        json.dump({"player": {"name": "Bob"}}, f)

    db = play.new_database(db_filename=db_path)
    assert db.get_data("player:stats:score", fallback=-1) == -1


def test_database_nested_keys_non_dict_fallback(db_path):
    """get_data on a non-dict intermediate value returns fallback."""
    with open(db_path, "w") as f:
        json.dump({"player": "just a string"}, f)

    db = play.new_database(db_filename=db_path)
    assert db.get_data("player:stats", fallback="nope") == "nope"


def test_database_set_persists_to_file(db_path):
    """set_data should write changes to the JSON file."""
    db = play.new_database(db_filename=db_path)
    db.set_data("highscore", 500)

    with open(db_path, "r") as f:
        data = json.load(f)
    assert data["highscore"] == 500


def test_database_set_nested_key_creates_intermediate_dicts(db_path):
    """set_data with nested keys should create intermediate dicts when missing."""
    db = play.new_database(db_filename=db_path)
    db.set_data("player:stats:score", 100)
    assert db.get_data("player:stats:score") == 100


def test_setting_a_nested_key_keeps_the_keys_beside_it(db_path):
    db = play.new_database(db_filename=db_path)
    db.set_data("player:name", "Bo")
    db.set_data("player:score", 3)

    reopened = play.new_database(db_filename=db_path)
    assert reopened.get_data("player") == {"name": "Bo", "score": 3}


def test_setting_a_key_again_replaces_its_value(db_path):
    db = play.new_database(db_filename=db_path)
    db.set_data("highscore", 5)
    db.set_data("highscore", 8)

    assert play.new_database(db_filename=db_path).get_data("highscore") == 8
