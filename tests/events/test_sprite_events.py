"""Clicking sprites: when_clicked, when_click_released and is_clicked."""

import pytest

import play
from tests.events.frames import mouse_down, mouse_move, mouse_up, play_frames


def _click(x, y, frames_held=1):
    """The frames of a click at (x, y): move there, press, hold, release."""
    return [
        [mouse_move(x, y)],
        [mouse_down(x, y)],
        *[[]] * frames_held,
        [mouse_up(x, y)],
    ]


@pytest.mark.parametrize(
    "register",
    [
        lambda sprites, callback: play.when_sprite_clicked(*sprites)(callback),
        lambda sprites, callback: [s.when_clicked(callback, True) for s in sprites],
    ],
    ids=["play.when_sprite_clicked", "call_with_sprite=True"],
)
def test_a_click_callback_is_told_which_sprite_was_clicked(register):
    left = play.new_box(x=-200, width=50, height=50)
    right = play.new_circle(x=200, radius=25)
    clicked = []
    register([left, right], lambda sprite: clicked.append(sprite))

    play_frames(*_click(200, 0), *_click(-200, 0))

    assert clicked == [right, left]


@pytest.mark.parametrize(
    "register",
    [
        lambda sprites, callback: play.when_sprite_click_released(*sprites)(callback),
        lambda sprites, callback: [
            s.when_click_released(callback, True) for s in sprites
        ],
    ],
    ids=["play.when_sprite_click_released", "call_with_sprite=True"],
)
def test_a_release_callback_is_told_which_sprite_was_released(register):
    left = play.new_box(x=-200, width=50, height=50)
    right = play.new_circle(x=200, radius=25)
    released = []
    register([left, right], lambda sprite: released.append(sprite))

    play_frames(*_click(-200, 0), *_click(200, 0))

    assert released == [left, right]


def test_click_callbacks_without_the_sprite_take_no_arguments():
    box = play.new_box(width=50, height=50)
    log = []
    box.when_clicked(lambda: log.append("clicked"))
    box.when_click_released(lambda: log.append("released"))

    play_frames(*_click(0, 0))

    assert log == ["clicked", "released"]


def test_a_click_beside_a_sprite_does_not_click_it():
    box = play.new_box(width=50, height=50)
    clicked = []
    box.when_clicked(lambda: clicked.append(True))

    play_frames(*_click(100, 0))

    assert clicked == []


def test_a_hidden_sprite_cannot_be_clicked():
    box = play.new_box(width=50, height=50)
    box.hide()
    log = []
    box.when_clicked(lambda: log.append("clicked"))
    box.when_click_released(lambda: log.append("released"))

    play_frames(*_click(0, 0))

    assert log == []


def test_is_clicked_is_true_only_in_the_frame_of_the_click():
    box = play.new_box(width=50, height=50)
    states = []
    play.repeat_forever(lambda: states.append(box.is_clicked))

    play_frames(*_click(0, 0, frames_held=3))

    assert states.count(True) == 1


def test_an_earlier_click_does_not_count_for_a_later_press_beside_the_sprite():
    box = play.new_box(width=100, height=100)
    released = []
    box.when_click_released(lambda: released.append(True))

    play_frames(
        [mouse_move(0, 0)],
        [mouse_down(0, 0)],
        [mouse_up(0, 0)],
        [mouse_move(300, 0)],
        [mouse_down(300, 0)],
        [mouse_move(0, 0)],
        [mouse_up(0, 0)],
    )

    assert released == [True]


@pytest.mark.parametrize(
    "frames",
    [
        [[mouse_move(0, 0)], [mouse_down(0, 0)], [], []],
        [
            [mouse_move(0, 0)],
            [mouse_down(0, 0)],
            [mouse_move(300, 0)],
            [mouse_up(300, 0)],
        ],
        [
            [mouse_move(300, 0)],
            [mouse_down(300, 0)],
            [mouse_move(0, 0)],
            [mouse_up(0, 0)],
        ],
    ],
    ids=["still held", "released beside it", "pressed beside it"],
)
def test_when_click_released_needs_a_press_and_a_release_on_the_sprite(frames):
    box = play.new_box(width=100, height=100)
    released = []
    box.when_click_released(lambda: released.append(True))

    play_frames(*frames)

    assert released == []
