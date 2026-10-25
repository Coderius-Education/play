import json

import pytest

import play
from play.db import Database


@pytest.fixture(autouse=True)
def in_a_fresh_folder(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def test_a_database_without_a_name_is_database_json_in_the_current_folder(tmp_path):
    db = play.new_database()
    db.set_data("score", 3)

    assert json.loads((tmp_path / "database.json").read_text()) == {"score": 3}


def test_saved_data_is_there_when_the_game_is_started_again():
    db = Database()
    db.set_data("test", "value")
    db.set_data("test_nested", {})
    db.set_data("test_nested:sub", "value")
    db.set_data("test_none", None)

    again = Database()

    assert again.get_data("test") == "value"
    assert again.get_data("test_nested:sub") == "value"
    assert again.get_data("test_none", fallback="N/A") is None
    assert again.get_data("test:sub", fallback="N/A") == "N/A"
    assert again.get_data("missing", fallback="N/A") == "N/A"
    assert again.get_data("test_nested:missing", fallback="N/A") == "N/A"


def test_opening_a_database_keeps_what_is_already_in_the_file(tmp_path):
    (tmp_path / "database.json").write_text('{"high_score": 12}')

    db = Database()
    db.set_data("name", "Ada")

    assert Database().get_data("high_score") == 12
    assert Database().get_data("name") == "Ada"
