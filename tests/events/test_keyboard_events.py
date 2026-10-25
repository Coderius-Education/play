"""Key presses and releases, through the real game loop."""

import itertools
import logging

import pygame
import pytest

import play
from play.io.keypress import key_num_to_name, keyboard_state
from tests.events.frames import key_down, key_up, play_frames


def test_when_any_key_pressed_is_told_which_key_went_down():
    pressed = []
    play.when_any_key_pressed(lambda key: pressed.append(key))

    play_frames([key_down(pygame.K_a)], [key_down(pygame.K_SPACE)])

    assert pressed == ["a", "space"]


def test_when_key_pressed_fires_for_each_of_its_keys_and_no_other():
    pressed = []

    @play.when_key_pressed("a", "b", "c")
    def on_key(key):
        pressed.append(key)

    play_frames([key_down(pygame.K_a)], [key_down(pygame.K_d)], [key_down(pygame.K_c)])

    assert pressed == ["a", "c"]


def test_when_key_pressed_may_leave_out_the_key_parameter():
    pressed = []
    play.when_key_pressed("space")(lambda: pressed.append(True))

    play_frames([key_down(pygame.K_SPACE)])

    assert pressed == [True]


def test_a_held_key_fires_when_key_pressed_once_even_when_the_keyboard_repeats_it():
    pressed = []
    play.when_key_pressed("a")(lambda: pressed.append(True))

    play_frames([key_down(pygame.K_a)], [], [], [key_down(pygame.K_a)], [])

    assert pressed == [True]


def test_a_key_pressed_again_after_its_release_fires_again():
    pressed = []
    play.when_key_pressed("a")(lambda: pressed.append(True))

    play_frames([key_down(pygame.K_a)], [key_up(pygame.K_a)], [key_down(pygame.K_a)])

    assert pressed == [True, True]


def test_when_any_key_released_is_told_which_key_went_up():
    released = []
    play.when_any_key_released(lambda key: released.append(key))

    play_frames(
        [key_down(pygame.K_a)],
        [key_down(pygame.K_b)],
        [key_up(pygame.K_b)],
        [key_up(pygame.K_a)],
    )

    assert released == ["b", "a"]


def test_when_key_released_fires_on_the_release_not_the_press():
    events = []
    play.when_key_released("space")(lambda key: events.append(("released", key)))

    @play.repeat_forever
    def watch():
        if play.key_is_pressed("space"):
            events.append("held")

    play_frames([key_down(pygame.K_SPACE)], [key_up(pygame.K_SPACE)], [])

    assert events == ["held", ("released", "space")]


def test_a_release_of_a_key_that_was_never_pressed_is_not_reported():
    released = []
    play.when_any_key_released(lambda key: released.append(key))

    play_frames([key_up(pygame.K_z)])

    assert released == []


def test_the_mode_key_is_not_reported_as_a_key():
    log = []
    play.when_any_key_pressed(lambda key: log.append(("pressed", key)))
    play.when_any_key_released(lambda key: log.append(("released", key)))

    play_frames([key_down(pygame.K_MODE)], [key_up(pygame.K_MODE)])

    assert log == []


def test_key_is_pressed_is_true_while_any_of_the_keys_is_held():
    seen = []

    @play.repeat_forever
    def watch():
        seen.append(play.key_is_pressed("up", "w"))

    play_frames([], [key_down(pygame.K_w)], [], [key_up(pygame.K_w)])

    assert [held for held, _ in itertools.groupby(seen)] == [False, True, False]


@pytest.mark.parametrize(
    "modifier", [pygame.KMOD_LCTRL, pygame.KMOD_LMETA], ids=["ctrl", "command"]
)
def test_ctrl_or_command_q_ends_the_game(modifier, monkeypatch):
    frames = []
    play.repeat_forever(lambda: frames.append(1))
    monkeypatch.setattr(pygame.key, "get_mods", lambda: modifier)

    play_frames([key_down(pygame.K_q)], *[[]] * 20)

    assert len(frames) < 5


def test_q_on_its_own_does_not_end_the_game():
    frames = []
    play.repeat_forever(lambda: frames.append(1))

    play_frames([key_down(pygame.K_q)], [], [])

    assert len(frames) >= 5


def test_a_callback_without_the_key_parameter_is_told_what_it_needs(caplog):
    @play.when_any_key_pressed
    def on_key():
        pass

    with caplog.at_level(logging.CRITICAL, logger="play"):
        play_frames([key_down(pygame.K_a)])

    assert "must take in 1 argument(s)" in caplog.text
    assert "Required: ['key']" in caplog.text


@pytest.mark.parametrize(
    "decorator", [play.when_any_key_pressed, play.when_any_key_released]
)
def test_any_key_decorators_reject_a_key_in_brackets(decorator):
    with pytest.raises(ValueError, match="doesn't use a list of keys"):
        decorator("a")


@pytest.mark.parametrize("decorator", [play.when_key_pressed, play.when_key_released])
@pytest.mark.parametrize("keys", [(123,), (["a", 123],)], ids=["number", "in a list"])
def test_a_key_that_is_not_a_string_is_rejected(decorator, keys):
    with pytest.raises(ValueError, match="Key must be a string or a list of strings"):
        decorator(*keys)


def test_clearing_a_frame_keeps_the_held_keys():
    keyboard_state.pressed.add("a")
    keyboard_state.pressed_this_frame.add("a")
    keyboard_state.released.add("b")

    keyboard_state.clear()

    assert keyboard_state.pressed == {"a"}
    assert keyboard_state.pressed_this_frame == set()
    assert keyboard_state.released == set()


class _KeyEvent:  # pylint: disable=too-few-public-methods
    def __init__(self, key):
        self.key = key


@pytest.mark.parametrize(
    "key, name",
    [
        (pygame.K_a, "a"),
        (pygame.K_SPACE, "space"),
        (pygame.K_RETURN, "return"),
        (pygame.K_ESCAPE, "escape"),
        (pygame.K_LEFT, "left"),
    ],
)
def test_keys_are_named_as_students_write_them(key, name):
    assert key_num_to_name(_KeyEvent(key)) == name


def test_two_keyboard_states_do_not_share_their_keys():
    from play.io.keypress import KeyboardState

    first, second = KeyboardState(), KeyboardState()
    first.pressed.add("a")
    first.released.add("b")

    assert "a" not in second.pressed
    assert "b" not in second.released
