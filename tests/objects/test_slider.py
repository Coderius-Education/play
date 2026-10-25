"""Tests for the Slider widget."""

import pygame
import pytest
import play
from play.io.mouse import mouse
from play.utils import color_name_to_rgb, load_font, render_text
from tests.conftest import click_at, count_color


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def _image(sprite):
    return pygame.image.tobytes(sprite.image, "RGBA")


def test_slider_creation():
    s = play.new_slider(min_value=0, max_value=100, value=50)
    assert s.min_value == 0
    assert s.max_value == 100
    assert s.value == 50


@pytest.mark.parametrize("value, expected", [(200, 10), (1, 5)])
def test_slider_clamps_initial_value(value, expected):
    s = play.new_slider(min_value=5, max_value=10, value=value)
    assert s.value == expected


def test_slider_value_setter_clamps():
    s = play.new_slider(min_value=0, max_value=100, value=50)
    s.value = 150
    assert s.value == 100
    s.value = -10
    assert s.value == 0


def test_slider_when_changed_rejects_async():
    s = play.new_slider()
    with pytest.raises(TypeError):

        @s.when_changed
        async def bad(v):
            pass


def test_disabling_a_slider_dims_it_and_enabling_restores_it():
    s = play.new_slider()
    enabled = _image(s)
    s.disabled = True
    assert s.disabled is True
    s.update()
    assert _image(s) != enabled
    s.disabled = False
    s.update()
    assert _image(s) == enabled


@pytest.mark.parametrize("x, expected", [(-95, 0), (95, 100)])
def test_a_slider_can_be_grabbed_at_either_end_of_its_track(x, expected):
    s = play.new_slider(min_value=0, max_value=100, value=50, x=0, y=0, width=200)
    click_at(x, 0, s, hold=True)
    assert s.value == expected


def test_a_slider_is_drawn_at_its_track_size_plus_the_thumb():
    s = play.new_slider(width=200, height=20, thumb_radius=12)
    assert s.image.get_size() == (200, 44)


# ── drag interaction ──────────────────────────────────────────────────────────
# The 800x600 test display puts x=0 at screen centre. For a slider at x=0 with
# width=200 and thumb_radius=12, the usable track spans mouse.x ∈ [-88, +88],
# so mouse.x=-88 → min, mouse.x=+88 → max, mouse.x=0 → midpoint.


def _start_drag(slider):
    click_at(0, 0, slider, hold=True)


def test_slider_drag_to_far_right_sets_max():
    s = play.new_slider(min_value=0, max_value=100, value=50, x=0, y=0, width=200)
    _start_drag(s)
    mouse.x = 88
    s.update()
    assert s.value == 100


def test_slider_drag_to_far_left_sets_min():
    s = play.new_slider(min_value=0, max_value=100, value=50, x=0, y=0, width=200)
    _start_drag(s)
    mouse.x = -88
    s.update()
    assert s.value == 0


def test_dragging_a_slider_maps_the_mouse_linearly_onto_the_range():
    s = play.new_slider(min_value=0, max_value=100, value=0, x=0, y=0, width=200)
    _start_drag(s)
    mouse.x = 44
    s.update()
    assert s.value == pytest.approx(75)


def test_a_slider_away_from_the_centre_drags_relative_to_its_own_track():
    s = play.new_slider(min_value=0, max_value=100, value=50, x=200, y=100, width=200)
    click_at(200, 100, s, hold=True)
    assert s.value == pytest.approx(50)
    mouse.x = 200 + 88
    s.update()
    assert s.value == 100


def test_slider_drag_stops_on_mouse_release():
    s = play.new_slider(min_value=0, max_value=100, value=50, x=0, y=0, width=200)
    _start_drag(s)
    mouse._is_clicked = False  # released
    mouse.x = 88
    s.update()
    assert s.value == 50  # not dragging → unchanged


def test_a_drag_reports_each_new_value_once():
    s = play.new_slider(min_value=0, max_value=100, value=50, x=0, y=0, width=200)
    seen = []
    s.when_changed(seen.append)
    _start_drag(s)
    mouse.x = 88
    s.update()
    s.update()
    assert seen == [100]


@pytest.mark.parametrize("mouse_x, expected", [(-35, 25), (-17, 50)])
def test_slider_step_quantizes_dragged_value(mouse_x, expected):
    s = play.new_slider(
        min_value=0, max_value=100, value=0, x=0, y=0, width=200, step=25
    )
    _start_drag(s)
    mouse.x = mouse_x
    s.update()
    assert s.value == expected


def test_slider_no_drag_without_prior_grab():
    # Moving the mouse over the slider without a click must not change the value.
    s = play.new_slider(min_value=0, max_value=100, value=50, x=0, y=0, width=200)
    mouse.x, mouse.y = 88, 0
    s.update()
    assert s.value == 50


def test_holding_the_mouse_down_and_moving_onto_a_slider_does_not_drag_it():
    s = play.new_slider(min_value=0, max_value=100, value=50, x=0, y=0, width=200)
    click_at(0, 200, s, hold=True)
    mouse.x, mouse.y = 88, 0
    s.update()
    assert s.value == 50


def _thumb_mean_x(surface, rgb):
    """Mean x of pixels matching *rgb* (the thumb colour), or None if absent."""
    tr, tg, tb = rgb[:3]
    xs = []
    for x in range(surface.get_width()):
        for y in range(surface.get_height()):
            c = surface.get_at((x, y))
            if c.r == tr and c.g == tg and c.b == tb and c.a != 0:
                xs.append(x)
    return sum(xs) / len(xs) if xs else None


@pytest.mark.parametrize("value, centre", [(0, 12), (50, 100), (100, 188)])
def test_the_thumb_sits_on_the_track_where_the_value_is(value, centre):
    s = play.new_slider(
        min_value=0,
        max_value=100,
        value=value,
        width=200,
        thumb_radius=12,
        thumb_color="red",
        fill_color="blue",
        track_color="lightgray",
    )
    assert _thumb_mean_x(s.image, color_name_to_rgb("red")) == pytest.approx(
        centre, abs=1
    )


def test_slider_show_value_widens_image():
    # Regression: show_value must include the label in the surface, not clip it
    # off the right edge.
    plain = play.new_slider(width=200, value=100, show_value=False)
    labelled = play.new_slider(width=200, value=100, show_value=True)
    assert labelled.image.get_width() > plain.image.get_width()


def test_a_slider_showing_its_value_is_still_dragged_by_its_track():
    s = play.new_slider(
        min_value=0, max_value=100, value=50, x=0, y=0, width=200, show_value=True
    )
    assert s.rect.left == play.screen.width / 2 - 100
    _start_drag(s)
    assert s.value == pytest.approx(50)
    mouse.x = 88
    s.update()
    assert s.value == 100


def _visible_pixels(surface):
    return sum(
        surface.get_at((x, y)).a > 0
        for x in range(surface.get_width())
        for y in range(surface.get_height())
    )


@pytest.mark.parametrize("value, label", [(50.0, "50"), (12.5, "12.5"), (7, "7")])
def test_the_value_label_drops_a_trailing_point_zero(value, label):
    expected = render_text(load_font(None, 16), label, True, (0, 0, 0))
    s = play.new_slider(value=value, show_value=True, value_color="black")
    assert count_color(s.image, (0, 0, 0)) == _visible_pixels(expected)


def test_a_cloned_slider_looks_and_steps_like_the_original():
    s = play.new_slider(
        min_value=10,
        max_value=90,
        value=40,
        step=20,
        track_color="yellow",
        fill_color="green",
        thumb_color="red",
        show_value=True,
    )
    c = s.clone()
    assert (c.min_value, c.max_value, c.value) == (10, 90, 40)
    assert _image(c) == _image(s)
    c.value = 45
    assert c.value == 50


def test_slider_fractional_range_renders_full_fill():
    # Regression: max(1, span) drew the thumb/fill halfway for sub-1 ranges.
    s = play.new_slider(
        min_value=0,
        max_value=0.5,
        value=0.5,
        fill_color="red",
        thumb_color="blue",
        track_color="lightgray",
    )
    filled = count_color(s.image, (255, 0, 0))
    # At value == max the fill spans (nearly) the whole 200px track.
    assert filled > 150 * s._height


def test_slider_value_setter_skips_callback_when_unchanged():
    # Regression: the setter fired when_changed even when the value did not
    # actually change, so a handler writing back to slider.value recursed.
    s = play.new_slider(min_value=0, max_value=100, value=50)
    fired = []
    s.when_changed(fired.append)
    s.value = 50  # unchanged — no callback
    assert fired == []
    s.value = 150  # clamps to 100 — one callback
    s.value = 150  # still 100 — no second callback
    assert fired == [100]


def test_slider_value_setter_safe_for_write_back_handlers():
    # A handler that writes back to slider.value (e.g. rounding) must not
    # recurse infinitely.
    s = play.new_slider(min_value=0, max_value=100, value=0)

    @s.when_changed
    def _round(value):
        s.value = round(value)

    s.value = 33.4
    assert s.value == 33
