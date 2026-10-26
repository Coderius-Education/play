"""while_..._pressed callbacks fire in every frame the key, mouse or button is held."""

import pygame
import pytest

import play
from play.io.controllers import controllers
from tests.events.frames import (
    button_down,
    button_up,
    key_down,
    key_up,
    mouse_down,
    mouse_up,
    play_frames,
)

TWO_MORE_FRAMES = [[], []]


def test_while_key_pressed_fires_in_every_frame_the_key_is_held():
    held = []
    play.while_key_pressed("right")(lambda key: held.append(key))

    play_frames(
        [key_down(pygame.K_RIGHT)], *TWO_MORE_FRAMES, [key_up(pygame.K_RIGHT)], []
    )

    assert held == ["right"] * 3


def test_while_key_pressed_fires_for_each_of_its_keys_that_is_held():
    held = []
    play.while_key_pressed("left", "right")(lambda key: held.append(key))

    play_frames(
        [key_down(pygame.K_LEFT)],
        [key_down(pygame.K_RIGHT), key_down(pygame.K_UP)],
        [key_up(pygame.K_LEFT)],
        [key_up(pygame.K_RIGHT)],
    )

    assert sorted(held) == ["left", "left", "right", "right"]


def test_while_any_key_pressed_is_told_which_key_is_held():
    held = []
    play.while_any_key_pressed(lambda key: held.append(key))

    play_frames([key_down(pygame.K_a)], [], [key_up(pygame.K_a)])

    assert held == ["a", "a"]


def test_while_key_pressed_may_leave_out_the_key_parameter():
    held = []
    play.while_key_pressed("space")(lambda: held.append(True))

    play_frames([key_down(pygame.K_SPACE)], [key_up(pygame.K_SPACE)])

    assert held == [True]


def test_a_held_key_fires_when_key_pressed_once_and_while_key_pressed_every_frame():
    log = []
    play.when_key_pressed("a")(lambda: log.append("pressed"))
    play.while_key_pressed("a")(lambda: log.append("held"))

    play_frames([key_down(pygame.K_a)], *TWO_MORE_FRAMES, [key_up(pygame.K_a)])

    assert sorted(log) == ["held", "held", "held", "pressed"]


def test_a_while_callback_that_is_still_waiting_is_not_started_again():
    started = []

    @play.while_key_pressed("a")
    async def slow():
        started.append(True)
        await play.timer(10)

    play_frames([key_down(pygame.K_a)], *TWO_MORE_FRAMES, [key_up(pygame.K_a)])

    assert started == [True]


def test_while_any_key_pressed_rejects_a_key_in_brackets():
    with pytest.raises(ValueError, match="doesn't use a list of keys"):
        play.while_any_key_pressed("a")


@pytest.mark.parametrize("keys", [(123,), (["a", 123],)], ids=["number", "in a list"])
def test_while_key_pressed_rejects_a_key_that_is_not_a_string(keys):
    with pytest.raises(ValueError, match="Key must be a string or a list of strings"):
        play.while_key_pressed(*keys)


def test_while_mouse_pressed_fires_in_every_frame_the_button_is_held():
    held = []
    play.while_mouse_pressed(lambda: held.append(True))

    play_frames([mouse_down()], *TWO_MORE_FRAMES, [mouse_up()], [])

    assert held == [True] * 3


def test_while_button_pressed_fires_in_every_frame_the_button_is_held():
    held = []
    controllers.while_button_pressed(0, 2)(lambda button: held.append(button))

    play_frames(
        [button_down(1)], [button_down(2)], *TWO_MORE_FRAMES, [button_up(2)], []
    )

    assert held == [2] * 3


def test_while_any_button_pressed_is_told_which_button_is_held():
    held = []
    controllers.while_any_button_pressed(0)(lambda button: held.append(button))

    play_frames([button_down(4)], [button_up(4)])

    assert held == [4]


def test_while_button_pressed_hears_its_own_controller_only():
    held = []
    controllers.while_button_pressed(1, 0, 1)(lambda button: held.append(button))

    play_frames(
        [button_down(0, instance_id=0)],
        [button_up(0, instance_id=0)],
        [button_down(1, instance_id=1)],
        [button_up(1, instance_id=1)],
    )

    assert held == [1]


def test_a_button_combination_is_held_while_all_its_buttons_are_held():
    held = []
    controllers.while_button_pressed(0, [1, 2])(lambda button: held.append(button))

    play_frames(
        [button_down(1)],
        [button_down(2)],
        [button_down(3)],
        [button_up(1)],
        [],
    )

    assert held == [{1, 2}, {1, 2}]


@pytest.mark.parametrize(
    "buttons", [("A",), ([1, "B"],)], ids=["name", "name in a list"]
)
def test_while_button_pressed_rejects_a_button_that_is_not_a_number(buttons):
    with pytest.raises(ValueError, match="Button must be an integer"):
        controllers.while_button_pressed(0, *buttons)
