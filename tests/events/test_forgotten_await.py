"""A missing ``await`` gets one clear hint, wherever and however often it runs."""

import logging
import warnings

import pytest

import play


def _hints(caplog):
    return [
        r.getMessage()
        for r in caplog.records
        if r.levelno == logging.WARNING and "forgot" in r.getMessage()
    ]


def _run_frames(frames=40):
    counted = []

    @play.repeat_forever
    def count():
        counted.append(1)
        if len(counted) == frames:
            play.stop_program()

    play.start_program()


def _two_start_handlers_that_wait():
    @play.when_program_starts
    async def intro():
        await play.timer(0.01)

    @play.when_program_starts
    async def music():
        await play.timer(0.02)


def test_two_waiting_start_handlers_do_not_silence_the_hint(caplog):
    _two_start_handlers_that_wait()

    @play.repeat_forever
    async def blink():
        play.timer(0.5)

    with caplog.at_level(logging.WARNING, logger="play"):
        _run_frames()

    assert len(_hints(caplog)) == 1


def test_two_waiting_start_handlers_do_not_swallow_other_warnings():
    _two_start_handlers_that_wait()
    calls = []

    @play.repeat_forever
    def warn_once():
        calls.append(1)
        if len(calls) == 20:
            warnings.warn("a warning of the student's own")

    with pytest.warns(UserWarning, match="of the student's own"):
        _run_frames()


def test_a_plain_def_is_told_to_become_async(caplog):
    @play.repeat_forever
    def blink():
        play.timer(0.5)

    with caplog.at_level(logging.WARNING, logger="play"):
        _run_frames()

    hints = _hints(caplog)
    assert len(hints) == 1
    assert "await play.timer(...)" in hints[0]
    assert '"async def blink"' in hints[0]
    assert "async_func" not in hints[0]


def test_an_async_def_is_not_told_to_become_async(caplog):
    @play.when_program_starts
    async def blink():
        play.animate()

    with caplog.at_level(logging.WARNING, logger="play"):
        _run_frames()

    hints = _hints(caplog)
    assert len(hints) == 1
    assert "await play.animate(...)" in hints[0]
    assert "async def" not in hints[0]
