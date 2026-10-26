"""Degenerate constructor values and inputs a student will plausibly hit.

Small widths, empty option lists, zero limits and non-ASCII labels — this is
a Dutch-language teaching library, so accented characters are the norm rather
than an exotic case, and several widgets size their hit-shape from
``font.size(label)``.
"""

import pygame
import pytest
import play
from play.io.mouse import mouse
from tests.conftest import click_at


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_narrow_slider_is_still_draggable():
    # Regression: the default 12px thumb on a 20px track made track_width
    # negative, so every drag pinned the value to min_value.
    s = play.new_slider(min_value=0, max_value=100, value=0, x=0, y=0, width=20)
    click_at(0, 0, s, hold=True)
    mouse.x = 40  # well past the right edge
    s.update()
    assert s.value == 100
    mouse.x = -40
    s.update()
    assert s.value == 0
    mouse._is_clicked = False


@pytest.mark.parametrize("width, height", [(20, 38), (200, 44)])
def test_a_thumb_is_shrunk_only_when_it_would_not_fit_the_track(width, height):
    s = play.new_slider(x=0, y=0, width=width, height=20, thumb_radius=12)
    assert s.image.get_size() == (width, height)


def test_max_length_zero_rejects_all_input():
    ti = play.new_text_input(max_length=0)
    ti._handle_text_input("a")
    assert ti.value == ""


def test_max_length_zero_truncates_the_initial_value():
    ti = play.new_text_input(value="preset", max_length=0)
    assert ti.value == ""


def test_empty_dropdown_opens_and_closes_without_error():
    dd = play.new_dropdown(options=[], x=0, y=0, width=160, height=40)
    assert dd.selected_value is None
    click_at(0, 0, dd)  # open
    assert dd.is_open is True
    dd.update()  # render an open menu with no rows
    click_at(0, 0, dd)  # close
    assert dd.is_open is False


def test_clicking_where_options_would_be_selects_nothing():
    dd = play.new_dropdown(options=[], x=0, y=0, width=160, height=40)
    received = []
    dd.when_changed(lambda v, i: received.append((v, i)))
    click_at(0, 0, dd)
    click_at(0, -60, dd)  # where the first row would sit
    assert received == []
    assert dd.selected_value is None


def test_options_emptied_at_runtime_clears_the_selection():
    dd = play.new_dropdown(options=["A", "B"], selected_index=1, x=0, y=0)
    dd.options = []
    assert dd.selected_value is None


def test_checkbox_label_cleared_shrinks_the_widget():
    cb = play.new_checkbox(label="A very long label indeed", x=0, y=0, size_px=24)
    wide = cb.width
    cb.label = ""
    assert cb.width < wide
    assert cb.width == 24  # back to the bare box


@pytest.mark.parametrize("label", ["Geluid aan", "Café", "Grüße", "€10", "Ω"])
def test_widgets_accept_non_ascii_labels(label):
    cb = play.new_checkbox(label=label, x=0, y=-60, size_px=24)
    rb = play.new_radio_button(
        label, value="v", group=play.new_radio_group(), x=0, y=60
    )
    cb.update()
    rb.update()
    assert cb.label == label
    assert cb.image.get_width() > 24 + 10
    assert rb.image.get_width() > 22 + 10
    click_at(cb.image.get_width() / 2 - 2, -60, cb, rb)
    click_at(rb.image.get_width() / 2 - 2, 60, cb, rb)
    assert cb.checked is True
    assert rb.selected is True


def test_non_ascii_text_input_round_trips():
    ti = play.new_text_input(value="")
    ti._handle_text_input("Grüße")
    assert ti.value == "Grüße"
    ti._handle_keydown(
        pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_LEFT, "mod": 0})
    )
    ti._handle_text_input("!")
    assert ti.value == "Grüß!e"
