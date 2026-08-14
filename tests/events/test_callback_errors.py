"""What happens when the code a student wrote raises.

This matters more here than in most libraries. The audience is beginners, and
the failure they will hit constantly is a typo inside a callback. If that
vanishes silently the game simply does nothing and there is no thread to pull.

It is not a hypothetical risk: pymunk swallows exceptions raised inside the
collision handlers *play itself* registers, printing a traceback across the
cffi boundary and carrying on, which is why the test suite needs a recorder to
notice them at all. These tests pin the behaviour for the callbacks a student
writes, which take a different path.

They also pin something inconsistent: an error in when_program_starts leaves
the program running, while an error reaching the game loop stops it. Both are
defensible, but they should change on purpose rather than by accident.
"""

import logging

import play


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


def test_the_program_keeps_running_after_a_start_up_error(caplog):
    """One broken start-up callback must not take the others down with it."""
    ran = []

    @play.when_program_starts
    async def boom():
        raise ValueError("typo in when_program_starts")

    @play.when_program_starts
    async def other():
        for _ in range(10):
            await play.animate()
        ran.append("other")
        play.stop_program()

    with caplog.at_level(logging.CRITICAL, logger="play"):
        play.start_program()

    assert ran == ["other"], "a second start-up callback should still have run"


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
