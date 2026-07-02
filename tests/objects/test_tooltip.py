"""Tests for the Tooltip widget."""

import pytest
import play
from play.io.mouse import mouse


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def _make(text="Hi", target_x=200):
    # Target sits away from the origin so the tooltip is hidden by default
    # (the fixture resets the mouse to (0, 0)).
    target = play.new_box(color="red", x=target_x, y=0, width=100, height=100)
    tip = play.new_tooltip(text, target=target)
    return target, tip


def test_tooltip_text_and_target_stored():
    target, tip = _make()
    assert tip.text == "Hi"
    assert tip.target is target


def test_tooltip_hidden_by_default():
    _target, tip = _make()
    # Mouse at (0, 0), target at (200, 0) — not hovering.
    assert tip._is_hidden is True


def test_tooltip_shows_on_hover():
    _target, tip = _make()
    mouse.x, mouse.y = 200, 0
    tip.update()
    assert tip._is_hidden is False


def test_tooltip_hides_when_mouse_leaves():
    _target, tip = _make()
    mouse.x, mouse.y = 200, 0
    tip.update()
    assert tip._is_hidden is False
    mouse.x, mouse.y = 0, 0
    tip.update()
    assert tip._is_hidden is True


def test_tooltip_follows_mouse_with_offset():
    _target, tip = _make()
    mouse.x, mouse.y = 200, 0
    tip.update()
    assert tip._x == 200 + tip._offset_x
    assert tip._y == 0 + tip._offset_y


def test_tooltip_no_target_stays_hidden():
    tip = play.new_tooltip("orphan")
    tip.update()
    assert tip._is_hidden is True


def test_tooltip_text_setter_triggers_recompute():
    _target, tip = _make()
    tip._should_recompute = False
    tip.text = "Updated"
    assert tip.text == "Updated"
    assert tip._should_recompute is True


def test_tooltip_target_setter():
    _target, tip = _make()
    other = play.new_box(color="blue", x=-200, y=0)
    tip.target = other
    assert tip.target is other


def test_tooltip_renders_when_visible():
    _target, tip = _make()
    mouse.x, mouse.y = 200, 0
    tip.update()
    assert tip.image is not None
    assert tip.image.get_width() > 0
    assert tip.image.get_height() > 0


def test_tooltip_multiline_taller_than_single_line():
    target = play.new_box(color="red", x=200, y=0, width=100, height=100)
    single = play.new_tooltip("A", target=target)
    multi = play.new_tooltip("A\nB\nC", target=target)
    mouse.x, mouse.y = 200, 0
    single.update()
    multi.update()
    assert multi.image.get_height() > single.image.get_height()


def test_tooltip_alive():
    _target, tip = _make()
    assert tip.alive()
