"""Regression tests for widget change/callback semantics.

Covers three consistency rules that the widgets previously broke:

* ``when_changed`` fires on *programmatic* mutation, not just on clicks.
* ``when_changed`` fires only when the value actually changes.
* A widget's public colour/value setters survive the next ``update()``.
"""

import pytest
import play
from play.io.mouse import mouse
from tests.conftest import click_at


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


# ── Button.color round-trips ──────────────────────────────────────────────────


def test_button_color_setter_survives_update():
    # Regression: update() re-derives _color from _base_color every frame, so a
    # plain Box.color setter was silently reverted on the next frame.
    btn = play.new_button("Go", color="royalblue", x=0, y=0)
    btn.color = "red"
    assert btn.color == "red"
    mouse.x, mouse.y = 999, 999  # keep the pointer off the button
    btn.update()
    assert btn.color == "red"


def test_button_color_getter_reports_resting_colour_not_hover():
    btn = play.new_button("Go", color="royalblue", hover_color="steelblue", x=0, y=0)
    mouse.x, mouse.y = 0, 0  # hover it
    btn.update()
    assert btn.color == "royalblue"


def test_button_disabled_while_hovered_fires_unhover():
    # Regression: disabling a hovered button cleared _was_hovered without
    # running the unhover callbacks, stranding whatever they toggle.
    btn = play.new_button("Go", x=0, y=0, width=100, height=50)
    # The constructor runs update() with the mouse still at its (0, 0)
    # default, so the button starts out hovered. Settle it outside *before*
    # registering the callbacks, so that closing-out does not record an event.
    mouse.x, mouse.y = 999, 999
    btn.update()
    events = []
    btn.when_hover(lambda: events.append("hover"))
    btn.when_unhover(lambda: events.append("unhover"))
    mouse.x, mouse.y = 0, 0
    btn.update()
    assert events == ["hover"]
    btn.disabled = True
    btn.update()
    assert events == ["hover", "unhover"]


# ── Checkbox.checked fires when_changed ───────────────────────────────────────


def test_checkbox_checked_setter_fires_when_changed():
    cb = play.new_checkbox(x=0, y=0)
    received = []
    cb.when_changed(received.append)
    cb.checked = True
    assert received == [True]


def test_checkbox_checked_setter_no_fire_when_unchanged():
    cb = play.new_checkbox(x=0, y=0, checked=True)
    received = []
    cb.when_changed(received.append)
    cb.checked = True
    assert received == []


# ── RadioGroup only reports real changes ──────────────────────────────────────


def test_radio_group_reselecting_same_option_does_not_fire():
    g = play.new_radio_group()
    play.new_radio_button("A", value="a", group=g, x=-50, y=0)
    r2 = play.new_radio_button("B", value="b", group=g, x=50, y=0)
    received = []
    g.when_changed(received.append)
    g._select(r2)
    g._select(r2)  # same option again — not a change
    assert received == ["b"]


def test_radio_group_selected_value_setter_no_fire_when_unchanged():
    g = play.new_radio_group()
    play.new_radio_button("A", value="a", group=g, x=-50, y=0, selected=True)
    received = []
    g.when_changed(received.append)
    g.selected_value = "a"
    assert received == []


# ── Dropdown only reports real changes ────────────────────────────────────────


def test_dropdown_reselecting_same_option_does_not_fire():
    dd = play.new_dropdown(options=["A", "B", "C"], selected_index=1)
    received = []
    dd.when_changed(lambda v, i: received.append((v, i)))
    dd._select(1)
    assert received == []


def test_dropdown_hidden_does_not_handle_clicks():
    # Regression: a hidden-but-open dropdown kept selecting invisible options.
    dd = play.new_dropdown(options=["A", "B", "C"], x=0, y=0, width=160, height=40)
    received = []
    dd.when_changed(lambda v, i: received.append((v, i)))
    click_at(0, 0, dd)  # open the menu
    assert dd.is_open is True
    dd.hide()
    assert dd.is_open is False  # hiding closes the menu
    click_at(0, -120, dd)  # would have been the 3rd option row
    assert received == []


# ── Slider ────────────────────────────────────────────────────────────────────


def test_slider_step_grid_is_anchored_to_min_value():
    # Regression: steps were snapped to multiples of `step` from zero, so a
    # range starting at 1 with step 2 produced 2, 4, 6 instead of 1, 3, 5.
    s = play.new_slider(min_value=1, max_value=11, value=1, step=2)
    # The reachable grid is 1, 3, 5, ... — every value is odd, never even.
    s.value = 4.4
    assert s.value == 5
    s.value = 8
    assert s.value == 9


def test_slider_min_value_setter_fires_when_changed():
    s = play.new_slider(min_value=0, max_value=100, value=50)
    received = []
    s.when_changed(received.append)
    s.min_value = 60
    assert s.value == 60
    assert received == [60]


def test_slider_max_value_setter_fires_when_changed():
    s = play.new_slider(min_value=0, max_value=100, value=80)
    received = []
    s.when_changed(received.append)
    s.max_value = 70
    assert s.value == 70
    assert received == [70]


def test_slider_bound_setter_without_clamp_does_not_fire():
    s = play.new_slider(min_value=0, max_value=100, value=50)
    received = []
    s.when_changed(received.append)
    s.max_value = 90  # 50 still in range
    assert received == []


# ── Tooltip drops a removed target ────────────────────────────────────────────


def test_tooltip_does_not_reappear_after_target_removed():
    target = play.new_box(color="red", x=200, y=0, width=100, height=100)
    tip = play.new_tooltip("Hi", target=target)
    mouse.x, mouse.y = 200, 0
    tip.update()
    assert tip.is_hidden is False
    target.remove()
    tip.update()
    assert tip.is_hidden is True
    tip.update()  # still hovering the now-empty area
    assert tip.is_hidden is True
