"""Tests for the ProgressBar widget."""

import pytest
import play


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_progress_bar_creation():
    pb = play.new_progress_bar(min_value=0, max_value=100, value=50)
    assert pb.min_value == 0
    assert pb.max_value == 100
    assert pb.value == 50


def test_progress_bar_percentage():
    pb = play.new_progress_bar(min_value=0, max_value=200, value=100)
    assert pb.percentage == 0.5


def test_progress_bar_percentage_at_zero():
    pb = play.new_progress_bar(min_value=0, max_value=100, value=0)
    assert pb.percentage == 0.0


def test_progress_bar_percentage_at_max():
    pb = play.new_progress_bar(min_value=0, max_value=100, value=100)
    assert pb.percentage == 1.0


def test_progress_bar_value_setter_clamps_high():
    pb = play.new_progress_bar(min_value=0, max_value=100, value=50)
    pb.value = 150
    assert pb.value == 100


def test_progress_bar_value_setter_clamps_low():
    pb = play.new_progress_bar(min_value=0, max_value=100, value=50)
    pb.value = -10
    assert pb.value == 0


def test_progress_bar_value_setter_triggers_recompute():
    pb = play.new_progress_bar(value=50)
    pb.value = 75
    assert pb._should_recompute is True


def test_progress_bar_bar_color_setter():
    pb = play.new_progress_bar(bar_color="red")
    assert pb.bar_color == "red"
    pb.bar_color = "green"
    assert pb.bar_color == "green"
    assert pb._should_recompute is True


def test_progress_bar_min_value_setter_clamps():
    pb = play.new_progress_bar(min_value=0, max_value=100, value=30)
    pb.min_value = 50
    assert pb.value == 50  # clamped up


def test_progress_bar_max_value_setter_clamps():
    pb = play.new_progress_bar(min_value=0, max_value=100, value=80)
    pb.max_value = 60
    assert pb.value == 60  # clamped down


def test_progress_bar_alive():
    pb = play.new_progress_bar()
    assert pb.alive()


def test_progress_bar_image_rendered():
    pb = play.new_progress_bar()
    assert pb.image is not None


def test_progress_bar_clone():
    pb = play.new_progress_bar(min_value=10, max_value=90, value=50, bar_color="red")
    c = pb.clone()
    assert c.min_value == 10
    assert c.max_value == 90
    assert c.value == 50
    assert c.bar_color == "red"
