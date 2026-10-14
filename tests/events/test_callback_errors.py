"""What happens when the code a student wrote raises.

This matters more here than in most libraries. The audience is beginners, and
the failure they will hit constantly is a typo inside a callback. If that
vanishes silently the game simply does nothing and there is no thread to pull.

It is not a hypothetical risk: pymunk swallows exceptions raised inside the
collision handlers *play itself* registers, printing a traceback across the
cffi boundary and carrying on, which is why the test suite needs a recorder to
notice them at all. These tests pin the behaviour for the callbacks a student
writes, which take a different path.

They also pin that the first error stops the game, wherever it is raised:
a plain or async callback, the game loop or an event (#239).
"""

import logging

import pygame
import pytest

import play
from tests.conftest import post_key_down, post_key_up, post_mouse_down, post_mouse_up


def _criticals(caplog):
    return [r for r in caplog.records if r.levelno >= logging.CRITICAL]


def _mentions(caplog, text):
    return any(text in r.getMessage() for r in _criticals(caplog))


def test_an_error_in_when_program_starts_is_reported(caplog):
    """A typo in start-up code must say so, not leave a game that does nothing."""

    @play.when_program_starts
    async def boom():
        raise ValueError("typo in when_program_starts")

    @play.when_program_starts
    async def stopper():
        for _ in range(20):
            await play.animate()
        play.stop_program()

    with caplog.at_level(logging.CRITICAL, logger="play"):
        play.start_program()

    assert _mentions(caplog, "typo in when_program_starts"), [
        r.getMessage() for r in _criticals(caplog)
    ]


def test_a_start_up_error_stops_the_program(caplog):
    frames = []

    @play.when_program_starts
    async def boom():
        raise ValueError("typo in when_program_starts")

    @play.repeat_forever
    def count():
        frames.append(1)
        if len(frames) == 60:
            play.stop_program()

    with caplog.at_level(logging.CRITICAL, logger="play"):
        play.start_program()

    assert len(frames) < 5


def test_an_error_in_a_collision_callback_is_reported(caplog):
    """The path where silence would be worst.

    play's own collision handlers run inside pymunk, which eats exceptions.
    A student's when_touching callback is dispatched from the game loop
    instead, so it has to surface — otherwise a typo in the one place every
    beginner writes code produces a game that quietly does nothing.
    """
    touched = []

    ball = play.new_circle(color="black", x=-150, y=0, radius=10)
    block = play.new_box(color="blue", x=0, y=0, width=40, height=400)
    ball.start_physics(
        obeys_gravity=False, x_speed=200, y_speed=0, friction=0, mass=10, bounciness=1.0
    )
    block.start_physics(
        obeys_gravity=False, can_move=False, friction=0, mass=10, bounciness=1.0
    )

    @ball.when_touching(block)
    def on_touch():
        touched.append(1)
        raise ValueError("typo in when_touching")

    @play.when_program_starts
    async def budget():
        for _ in range(300):
            await play.animate()
        play.stop_program()

    with caplog.at_level(logging.CRITICAL, logger="play"):
        play.start_program()

    assert touched, "the ball never reached the block, so nothing was raised"
    assert _mentions(caplog, "typo in when_touching"), [
        r.getMessage() for r in _criticals(caplog)
    ]


def test_an_error_in_repeat_forever_is_reported(caplog):
    """The other place beginners put most of their code."""
    ran = []

    @play.repeat_forever
    async def boom():
        ran.append(1)
        raise ValueError("typo in repeat_forever")

    @play.when_program_starts
    async def budget():
        for _ in range(60):
            await play.animate()
        play.stop_program()

    with caplog.at_level(logging.CRITICAL, logger="play"):
        play.start_program()

    assert ran, "the repeat_forever callback never ran"
    assert _mentions(caplog, "typo in repeat_forever"), [
        r.getMessage() for r in _criticals(caplog)
    ]


def test_a_raising_callback_does_not_hang_the_program(caplog):
    """However the error is handled, start_program() has to return.

    A student whose game locks up has no error to read and no way out but to
    kill the process.
    """

    @play.repeat_forever
    async def boom():
        raise ValueError("typo in repeat_forever")

    @play.when_program_starts
    async def budget():
        for _ in range(60):
            await play.animate()
        play.stop_program()

    with caplog.at_level(logging.CRITICAL, logger="play"):
        play.start_program()  # the assertion is that this returns at all


def _count_frames_until_stopped(frames=60):
    counted = []

    @play.repeat_forever
    def count():
        counted.append(1)
        if len(counted) == frames:
            play.stop_program()

    play.start_program()
    return len(counted)


def test_an_async_repeat_forever_error_stops_the_game_with_one_traceback(capsys):
    @play.repeat_forever
    async def broken():
        raise ValueError("typo in async repeat_forever")

    frames = _count_frames_until_stopped()

    assert frames < 5
    assert capsys.readouterr().err.count("ValueError: typo in async") == 1


def _press_space_after_a_few_frames():
    @play.when_program_starts
    async def press():
        for _ in range(3):
            await play.animate()
        post_key_down(pygame.K_SPACE)
        await play.animate()
        post_key_up(pygame.K_SPACE)


def _click_after_a_few_frames():
    @play.when_program_starts
    async def click():
        for _ in range(3):
            await play.animate()
        post_mouse_down(400, 300)
        await play.animate()
        post_mouse_up(400, 300)


@pytest.mark.parametrize("is_async", [False, True], ids=["def", "async def"])
@pytest.mark.parametrize("event", ["key", "click"])
def test_an_error_in_an_event_callback_stops_the_game(event, is_async):
    if event == "key":
        register, trigger = (
            play.when_key_pressed("space"),
            _press_space_after_a_few_frames,
        )
    else:
        register, trigger = play.new_box().when_clicked, _click_after_a_few_frames

    if is_async:

        async def broken():
            raise ValueError("typo in an event callback")

    else:

        def broken():
            raise ValueError("typo in an event callback")

    register(broken)
    trigger()

    assert _count_frames_until_stopped() < 10


def test_an_error_right_after_stop_program_is_still_shown(capsys):
    @play.when_program_starts
    async def finish():
        await play.animate()
        play.stop_program()
        raise ValueError("typo after stop_program")

    play.start_program()

    assert "typo after stop_program" in capsys.readouterr().err


def test_after_an_error_no_frame_runs_and_no_second_error_is_shown(capsys, caplog):
    failed = []
    frames_after_the_error = []

    @play.when_key_pressed("space")
    def first():
        failed.append(True)
        raise ValueError("first error")

    @play.repeat_forever
    def second():
        if failed:
            frames_after_the_error.append(1)
            raise ValueError("second error")

    _press_space_after_a_few_frames()
    with caplog.at_level(logging.CRITICAL, logger="play"):
        _count_frames_until_stopped()

    shown = capsys.readouterr().err + caplog.text
    assert "first error" in shown
    assert "second error" not in shown
    assert frames_after_the_error == []
