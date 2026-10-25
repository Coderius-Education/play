"""Tests for the Checkbox widget."""

import pygame
import pytest
import play
from play.io.mouse import mouse
from play.utils import color_name_to_rgb
from tests.conftest import click_at, count_color


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def _image(sprite):
    return pygame.image.tobytes(sprite.image, "RGBA")


def test_checkbox_creation():
    cb = play.new_checkbox(label="Enable sound", checked=True)
    assert cb.checked is True
    assert cb.label == "Enable sound"
    assert play.new_checkbox().checked is False


def test_each_click_toggles_the_checkbox_and_reports_the_new_state():
    cb = play.new_checkbox(x=0, y=0, size_px=24)
    results = []
    cb.when_changed(results.append)
    click_at(0, 0, cb)
    assert cb.checked is True
    click_at(0, 0, cb)
    assert cb.checked is False
    assert results == [True, False]


def test_checkbox_hover_border_reacts():
    cb = play.new_checkbox(x=0, y=0, size_px=24, hover_border_color="red")
    mouse.x, mouse.y = 500, 500
    cb.update()
    assert count_color(cb.image, (255, 0, 0)) == 0
    mouse.x, mouse.y = 0, 0
    cb.update()
    assert count_color(cb.image, (255, 0, 0)) > 0
    mouse.x, mouse.y = 500, 500
    cb.update()
    assert count_color(cb.image, (255, 0, 0)) == 0


def test_disabled_checkbox_ignores_hover():
    cb = play.new_checkbox(x=0, y=0, size_px=24, disabled=True)
    mouse.x, mouse.y = 500, 500
    cb.update()
    away = _image(cb)
    mouse.x, mouse.y = 0, 0
    cb.update()
    assert _image(cb) == away


def test_checkbox_when_changed_rejects_async():
    cb = play.new_checkbox()
    with pytest.raises(TypeError):

        @cb.when_changed
        async def bad(v):
            pass


def test_a_disabled_checkbox_ignores_clicks_and_reports_nothing():
    cb = play.new_checkbox(x=0, y=0, size_px=24, disabled=True)
    results = []
    cb.when_changed(results.append)
    click_at(0, 0, cb)
    assert cb.checked is False
    assert results == []


def test_disabling_a_checkbox_dims_it_and_enabling_restores_it():
    cb = play.new_checkbox(x=0, y=0, size_px=24)
    mouse.x, mouse.y = 500, 500
    cb.update()
    enabled = _image(cb)
    cb.disabled = True
    assert cb.disabled is True
    cb.update()
    assert _image(cb) != enabled
    cb.disabled = False
    cb.update()
    assert _image(cb) == enabled


def test_checkbox_checked_setter():
    check_rgb = color_name_to_rgb("royalblue")
    cb = play.new_checkbox(check_color="royalblue")
    cb.checked = True
    assert cb.checked is True
    cb.update()
    assert count_color(cb.image, check_rgb) > 0
    cb.checked = False
    assert cb.checked is False
    cb.update()
    assert count_color(cb.image, check_rgb) == 0


def test_checkbox_label_setter():
    cb = play.new_checkbox(label="old")
    before = _image(cb)
    cb.label = "new"
    assert cb.label == "new"
    cb.update()
    assert _image(cb) != before


def test_a_checkbox_without_a_label_is_a_square_of_size_px():
    assert play.new_checkbox(size_px=30).image.get_size() == (30, 30)


def test_a_label_makes_the_checkbox_wider_than_its_box():
    cb = play.new_checkbox("Enable", size_px=24)
    assert cb.image.get_width() > 24 + 10
    assert cb.image.get_height() == 24


def test_checkbox_checkmark_only_when_checked():
    # The check-colour fill must appear only when checked.
    check_rgb = color_name_to_rgb("royalblue")
    unchecked = play.new_checkbox(check_color="royalblue", checked=False)
    checked = play.new_checkbox(check_color="royalblue", checked=True)
    assert count_color(unchecked.image, check_rgb) == 0
    assert count_color(checked.image, check_rgb) > 0


def test_checkbox_click_off_centre_within_box_toggles():
    # A click on the label side of the widget (off the centre) still toggles —
    # guards against a too-small or mis-placed hit-shape.
    cb = play.new_checkbox("Enable", x=0, y=0, size_px=24)
    # The widget is wider than tall (box + label); nudge the click off-centre but
    # still inside the widget rect.
    half_w = cb.image.get_width() / 2
    click_at(half_w - 4, 0, cb)
    assert cb.checked is True


def test_checkbox_click_outside_does_not_toggle():
    cb = play.new_checkbox("Enable", x=0, y=0, size_px=24)
    click_at(300, 300, cb)  # far outside
    assert cb.checked is False


def test_a_cloned_checkbox_looks_and_behaves_like_the_original():
    cb = play.new_checkbox(
        label="X",
        checked=True,
        disabled=True,
        color="yellow",
        check_color="green",
        label_color="red",
    )
    c = cb.clone()
    assert c.label == "X"
    assert c.checked is True
    assert c.disabled is True
    assert _image(c) == _image(cb)


def test_checkbox_label_setter_resizes_widget_and_hit_shape():
    # Regression: a longer label was clipped and its area unclickable because
    # the width and physics hit-shape were never recomputed.
    cb = play.new_checkbox(label="Hi", x=0, y=0, size_px=24)
    old_width = cb.width
    cb.label = "A much longer label than before"
    assert cb.width > old_width
    # The label area (right of the box) is now clickable.
    click_at(old_width + 40, 0, cb)
    assert cb.checked is True
