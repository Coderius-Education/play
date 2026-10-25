"""A missing ``await`` gets one clear hint, wherever and however often it runs."""

import inspect
import logging
import sys
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


def test_a_call_kept_in_a_variable_is_hinted_at_its_own_line(caplog):
    @play.repeat_forever
    def blink():
        wait = play.timer(0.5)

    with caplog.at_level(logging.WARNING, logger="play"):
        _run_frames()

    source, first_line = inspect.getsourcelines(blink)
    line = first_line + next(i for i, text in enumerate(source) if "wait =" in text)
    hints = _hints(caplog)
    assert len(hints) == 1
    assert f"line {line} of file {__file__}" in hints[0]
    assert '"async def blink"' in hints[0]


def test_the_hint_is_shown_once_per_line_even_when_warnings_always_show(caplog):
    @play.repeat_forever
    def blink():
        play.timer(0.5)

    with warnings.catch_warnings():
        warnings.simplefilter("always")
        with caplog.at_level(logging.WARNING, logger="play"):
            _run_frames()

    assert len(_hints(caplog)) == 1


def test_start_program_puts_the_warning_settings_back():
    sys.set_coroutine_origin_tracking_depth(0)
    before = warnings.showwarning, sys.get_coroutine_origin_tracking_depth()

    _run_frames()

    assert (warnings.showwarning, sys.get_coroutine_origin_tracking_depth()) == before
