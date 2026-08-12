"""Tests for exclusive click ownership between overlapping widgets.

A click is delivered to the top-most interactive widget under the cursor, so
stacked widgets don't all react to it. Plain sprites are deliberately left
alone: every sprite under the cursor still receives the click, as before.
"""

import pytest
import play
from play.io.mouse import mouse
from play.core.mouse_loop import mouse_state
from tests.conftest import click_at


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def _resolve_click_at(x, y):
    """Put the frame into the state it has just after a MOUSEBUTTONDOWN."""
    mouse.x, mouse.y = x, y
    mouse._is_clicked = True
    mouse_state.click_happened = True
    mouse_state.resolve_click_owner()


def _end_click():
    mouse_state.clear()
    mouse._is_clicked = False


# ── widgets are exclusive ─────────────────────────────────────────────────────


def test_only_topmost_stacked_widget_receives_the_click():
    low = play.new_checkbox(x=0, y=0, size_px=40, layer=10)
    high = play.new_checkbox(x=0, y=0, size_px=40, layer=20)
    click_at(0, 0, low, high)
    assert high.checked is True
    assert low.checked is False


def test_widget_takes_ownership_from_an_overlapping_plain_sprite():
    box = play.new_box(color="red", x=0, y=0, width=60, height=60)
    btn = play.new_button("Go", x=0, y=0, width=60, height=60)
    _resolve_click_at(0, 0)
    try:
        assert mouse_state.click_owner is btn
        assert mouse_state.click_hits(btn) is True
        assert mouse_state.click_hits(box) is False
    finally:
        _end_click()


# ── plain sprites keep their original behaviour ───────────────────────────────


def test_plain_sprites_never_take_ownership():
    a = play.new_box(color="red", x=0, y=0, width=60, height=60)
    b = play.new_box(color="blue", x=0, y=0, width=60, height=60)
    _resolve_click_at(0, 0)
    try:
        assert mouse_state.click_owner is None
        # Both still see the click, exactly as before widgets existed.
        assert mouse_state.click_hits(a) is True
        assert mouse_state.click_hits(b) is True
    finally:
        _end_click()


# ── an open dropdown still wins, and still closes ─────────────────────────────


def test_open_dropdown_claims_clicks_on_its_menu():
    dd = play.new_dropdown(options=["A", "B", "C"], x=0, y=0, width=160, height=40)
    under = play.new_checkbox(x=0, y=-120, size_px=40)
    click_at(0, 0, dd)  # open the menu
    assert dd.is_open is True
    click_at(0, -120, under, dd)  # third option row, over the checkbox
    assert dd.selected_value == "C"
    assert under.checked is False  # the menu swallowed the click


def test_open_dropdown_closes_when_another_widget_is_clicked():
    # Regression: closing relied on click_hits(self), which is False once
    # another widget owns the click, so the menu stayed open forever.
    dd = play.new_dropdown(options=["A", "B", "C"], x=0, y=0, width=160, height=40)
    cb = play.new_checkbox(x=250, y=0, size_px=40)
    click_at(0, 0, dd)
    assert dd.is_open is True
    click_at(250, 0, cb, dd)
    assert cb.checked is True
    assert dd.is_open is False


def test_open_dropdown_closes_on_click_over_empty_space():
    dd = play.new_dropdown(options=["A", "B", "C"], x=0, y=0, width=160, height=40)
    click_at(0, 0, dd)
    assert dd.is_open is True
    click_at(350, 250, dd)
    assert dd.is_open is False
