"""when_program_starts and repeat_forever, through the real game loop."""

import logging

import pytest

import play


def _stop_after(frames):
    """Register a repeat_forever that stops the program in its *frames*-th frame."""
    counted = []

    @play.repeat_forever
    def stopper():
        counted.append(1)
        if len(counted) == frames:
            play.stop_program()


def test_when_program_starts_runs_once_before_the_first_frame():
    log = []
    play.when_program_starts(lambda: log.append("start"))
    play.repeat_forever(lambda: log.append("frame"))
    _stop_after(3)

    play.start_program()

    assert log == ["start", "frame", "frame", "frame"]


def test_an_async_when_program_starts_runs_its_setup_before_the_first_frame():
    log = []

    @play.when_program_starts
    async def setup():
        log.append("setup")
        await play.timer(0)
        log.append("after the wait")

    play.repeat_forever(lambda: log.append("frame"))
    _stop_after(3)

    play.start_program()

    assert log[0] == "setup"
    assert "after the wait" in log


def test_several_start_and_frame_callbacks_run_in_the_order_they_were_written():
    log = []
    play.when_program_starts(lambda: log.append("start 1"))
    play.when_program_starts(lambda: log.append("start 2"))
    play.repeat_forever(lambda: log.append("frame 1"))
    play.repeat_forever(lambda: log.append("frame 2"))
    _stop_after(2)

    play.start_program()

    assert log == ["start 1", "start 2", "frame 1", "frame 2", "frame 1", "frame 2"]


@pytest.mark.parametrize("decorator", [play.when_program_starts, play.repeat_forever])
def test_the_decorated_function_can_still_be_called(decorator):
    @decorator
    def greet():
        return "hello"

    assert greet() == "hello"


def test_a_callback_that_takes_an_argument_it_will_never_get_is_reported(caplog):
    @play.repeat_forever
    def move(sprite):
        pass

    with caplog.at_level(logging.CRITICAL, logger="play"):
        play.start_program()

    assert "must not take in any arguments" in caplog.text


def test_timer_returns_true_once_the_time_has_passed():
    results = []

    @play.when_program_starts
    async def wait():
        results.append(await play.timer(0.01))
        play.stop_program()

    play.start_program()

    assert results == [True]
