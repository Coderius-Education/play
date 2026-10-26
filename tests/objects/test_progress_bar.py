"""Tests for the ProgressBar widget."""

import pytest
import play
from play.utils import color_name_to_rgb, load_font, render_text
from tests.conftest import count_color
from tests.objects.clone_checks import BUNDLED_FONT, appearance


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def _bar_pixels(bar, color="royalblue"):
    """How many pixels of *bar* are drawn in *color*."""
    return count_color(bar.image, color_name_to_rgb(color))


def test_progress_bar_creation():
    pb = play.new_progress_bar(min_value=0, max_value=100, value=50)
    assert pb.min_value == 0
    assert pb.max_value == 100
    assert pb.value == 50


@pytest.mark.parametrize(
    "low, high, value, expected",
    [
        (0, 200, 100, 0.5),
        (0, 100, 0, 0.0),
        (0, 100, 100, 1.0),
        (10, 20, 15, 0.5),
        (0, 0.8, 0.8, 1.0),
    ],
    ids=["half", "empty", "full", "offset_range", "fractional_range"],
)
def test_progress_bar_percentage(low, high, value, expected):
    pb = play.new_progress_bar(min_value=low, max_value=high, value=value)
    assert pb.percentage == pytest.approx(expected)


def test_progress_bar_percentage_zero_span():
    pb = play.new_progress_bar(min_value=5, max_value=5, value=5)
    assert pb.percentage == 0.0


@pytest.mark.parametrize("value, expected", [(150, 100), (-10, 0)])
def test_progress_bar_value_setter_clamps(value, expected):
    pb = play.new_progress_bar(min_value=0, max_value=100, value=50)
    pb.value = value
    assert pb.value == expected


def test_raising_the_value_redraws_a_longer_fill():
    pb = play.new_progress_bar(value=25)
    before = _bar_pixels(pb)
    pb.value = 75
    pb.update()
    assert _bar_pixels(pb) > before


def test_progress_bar_bar_color_setter():
    pb = play.new_progress_bar(bar_color="red")
    assert pb.bar_color == "red"
    pb.bar_color = "green"
    assert pb.bar_color == "green"
    pb.update()
    assert _bar_pixels(pb, "green") > 0
    assert _bar_pixels(pb, "red") == 0


def test_progress_bar_min_value_setter_clamps():
    pb = play.new_progress_bar(min_value=0, max_value=100, value=30)
    pb.min_value = 50
    assert pb.value == 50  # clamped up


def test_progress_bar_max_value_setter_clamps():
    pb = play.new_progress_bar(min_value=0, max_value=100, value=80)
    pb.max_value = 60
    assert pb.value == 60  # clamped down


def test_a_progress_bar_is_drawn_at_its_width_and_height():
    assert play.new_progress_bar(width=150, height=30).image.get_size() == (150, 30)


def test_the_fill_covers_the_same_fraction_of_the_bar_as_the_value():
    full = _bar_pixels(play.new_progress_bar(value=100, border_radius=0))
    half = _bar_pixels(play.new_progress_bar(value=50, border_radius=0))
    empty = _bar_pixels(play.new_progress_bar(value=0, border_radius=0))
    assert empty == 0
    assert full == (200 - 2) * (24 - 2)
    assert half / full == pytest.approx(0.5, abs=0.02)


def test_progress_bar_show_label_draws_pixels():
    # The percentage label must actually be drawn on the surface.
    label_rgb = color_name_to_rgb("black")
    without = play.new_progress_bar(value=50, show_label=False, label_color="black")
    with_lbl = play.new_progress_bar(value=50, show_label=True, label_color="black")
    assert count_color(with_lbl.image, label_rgb) > count_color(
        without.image, label_rgb
    )


def _opaque_pixels(surface):
    """How many pixels of *surface* are fully opaque."""
    return sum(
        surface.get_at((x, y)).a == 255
        for x in range(surface.get_width())
        for y in range(surface.get_height())
    )


@pytest.mark.parametrize("value, label", [(50, "50%"), (100, "100%"), (7, "7%")])
def test_the_label_shows_the_percentage(value, label):
    expected = render_text(load_font(None, 14), label, True, (0, 0, 0))
    pb = play.new_progress_bar(value=value, show_label=True, label_color="black")
    assert count_color(pb.image, (0, 0, 0)) == _opaque_pixels(expected)


def test_a_cloned_progress_bar_looks_like_the_original():
    pb = play.new_progress_bar(
        min_value=10,
        max_value=90,
        value=30,
        x=30,
        y=20,
        width=150,
        height=30,
        bar_color="red",
        background_color="yellow",
        border_color="green",
        border_width=3,
        border_radius=9,
        transparency=70,
        anchor="top-left",
        layer=12,
        show_label=True,
        label_color="blue",
        font_size=24,
        font=BUNDLED_FONT,
    )
    c = pb.clone()
    assert (c.min_value, c.max_value, c.value, c.bar_color) == (10, 90, 30, "red")
    assert appearance(c) == appearance(pb)
