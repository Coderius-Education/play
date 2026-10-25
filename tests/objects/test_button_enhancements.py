"""Tests for enhanced Button features: click_color, disabled, click handlers."""

import pygame
import pytest
import play
from play.io.mouse import mouse
from play.io.screen import screen
from play.utils import color_name_to_rgb
from tests.conftest import (
    count_color,
    post_mouse_down,
    post_mouse_motion,
    post_mouse_up,
)


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def _click_in_the_game_loop():
    sx, sy = int(screen.width / 2), int(screen.height / 2)

    @play.when_program_starts
    async def driver():
        post_mouse_motion(sx, sy)
        await play.animate()
        post_mouse_down(sx, sy)
        await play.animate()
        post_mouse_up(sx, sy)
        await play.animate()
        play.stop_program()

    play.start_program()


def _image(sprite):
    return pygame.image.tobytes(sprite.image, "RGBA")


# ── click handlers ────────────────────────────────────────────────────────────


def test_a_click_handler_can_ask_for_the_button_it_belongs_to():
    btn = play.new_button("Go", x=0, y=0, width=100, height=50)
    seen = []
    btn.when_clicked(seen.append, call_with_sprite=True)

    _click_in_the_game_loop()

    assert seen == [btn]


def test_registering_a_handler_without_a_readable_signature_does_not_crash():
    btn = play.new_button()
    btn.when_clicked(min)


# ── click_color ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize("how", ["constructor", "setter"])
def test_a_held_button_shows_its_click_colour(how):
    navy = color_name_to_rgb("navy")
    if how == "constructor":
        btn = play.new_button(x=0, y=0, width=100, height=50, click_color="navy")
    else:
        btn = play.new_button(x=0, y=0, width=100, height=50)
        btn.click_color = "navy"
        assert btn.click_color == "navy"
    mouse.x, mouse.y = 0, 0
    btn.update()
    assert count_color(btn.image, navy) == 0

    mouse._is_clicked = True
    btn.update()
    assert count_color(btn.image, navy) > 0


def test_holding_the_mouse_elsewhere_does_not_press_the_button():
    btn = play.new_button(x=0, y=0, width=100, height=50, color="blue")
    mouse.x, mouse.y = 300, 200
    mouse._is_clicked = True
    btn.update()
    assert count_color(btn.image, color_name_to_rgb("blue")) > 0


def test_without_a_click_colour_a_held_button_darkens_its_hover_colour():
    hover = color_name_to_rgb("steelblue")
    darker = tuple(int(channel * 0.75) for channel in hover[:3])
    btn = play.new_button(x=0, y=0, width=100, height=50, hover_color="steelblue")
    mouse.x, mouse.y = 0, 0
    mouse._is_clicked = True
    btn.update()
    assert count_color(btn.image, darker) > 0
    assert count_color(btn.image, hover) == 0


# ── disabled state ────────────────────────────────────────────────────────────


def test_a_disabled_button_shows_its_disabled_colour_even_when_hovered():
    btn = play.new_button(
        x=0, y=0, width=100, height=50, hover_color="steelblue", disabled_color="silver"
    )
    btn.disabled = True
    mouse.x, mouse.y = 0, 0
    btn.update()
    assert count_color(btn.image, color_name_to_rgb("silver")) > 0
    assert count_color(btn.image, color_name_to_rgb("steelblue")) == 0


@pytest.mark.parametrize("disabled", [True, False])
def test_the_disabled_text_colour_is_used_only_while_disabled(disabled):
    btn = play.new_button(
        text="Stop", width=120, height=50, disabled=disabled, disabled_text_color="red"
    )
    assert (count_color(btn.image, (255, 0, 0)) > 0) is disabled


# ── clone ─────────────────────────────────────────────────────────────────────


def test_a_cloned_button_looks_like_the_original_resting_hovered_pressed_and_disabled():
    btn = play.new_button(
        "Go",
        x=0,
        y=0,
        width=120,
        height=40,
        color="blue",
        hover_color="green",
        click_color="orange",
        text_color="yellow",
        disabled_color="silver",
        disabled_text_color="red",
    )
    twin = btn.clone()
    for mouse_xy, held in (((999, 999), False), ((0, 0), False), ((0, 0), True)):
        mouse.x, mouse.y = mouse_xy
        mouse._is_clicked = held
        btn.update()
        twin.update()
        assert _image(twin) == _image(btn)

    btn.disabled = True
    btn.update()
    disabled_twin = btn.clone()
    disabled_twin.update()
    assert disabled_twin.disabled is True
    assert _image(disabled_twin) == _image(btn)


# ── property setters ─────────────────────────────────────────────────────────


def test_setting_the_text_colour_redraws_the_label():
    btn = play.new_button()
    btn.text_color = "green"
    assert btn.text_color == "green"
    btn.update()
    assert count_color(btn.image, color_name_to_rgb("green")) > 0


def test_hover_color_setter_reaches_the_rendered_button():
    yellow = color_name_to_rgb("yellow")
    btn = play.new_button(x=0, y=0, width=120, height=50)
    btn.hover_color = "yellow"
    assert btn.hover_color == "yellow"

    mouse.x, mouse.y = 999, 999  # not hovered: the new colour is not shown yet
    btn.update()
    assert count_color(btn.image, yellow) == 0

    mouse.x, mouse.y = 0, 0  # hovered: it is
    btn.update()
    assert count_color(btn.image, yellow) > 0


def test_disabled_color_setter_reaches_the_rendered_button():
    gray = color_name_to_rgb("gray")
    btn = play.new_button(x=0, y=0, width=120, height=50)
    btn.disabled_color = "gray"
    assert btn.disabled_color == "gray"

    mouse.x, mouse.y = 999, 999
    btn.update()
    assert count_color(btn.image, gray) == 0

    btn.disabled = True
    btn.update()
    assert count_color(btn.image, gray) > 0


def test_a_bigger_font_size_draws_a_bigger_label():
    red = (255, 0, 0)
    btn = play.new_button("Go", width=200, height=80, text_color="red")
    small = count_color(btn.image, red)
    btn.font_size = 40
    assert btn.font_size == 40
    btn.update()
    assert count_color(btn.image, red) > small


def test_the_label_is_centred_on_the_button():
    btn = play.new_button("I", width=120, height=60, text_color="red")
    red_rows = [
        y
        for y in range(btn.image.get_height())
        if any(btn.image.get_at((x, y))[:3] == (255, 0, 0) for x in range(120))
    ]
    red_columns = [
        x
        for x in range(btn.image.get_width())
        if any(btn.image.get_at((x, y))[:3] == (255, 0, 0) for y in range(60))
    ]
    assert (min(red_rows) + max(red_rows)) / 2 == pytest.approx(30, abs=3)
    assert (min(red_columns) + max(red_columns)) / 2 == pytest.approx(60, abs=3)
