"""play's event loop: one per process, and it reports what goes wrong in its tasks."""

import asyncio
import logging

import pytest

import play.loop
from play.globals import globals_list, ProgramState


def _criticals(caplog):
    return [r.getMessage() for r in caplog.records if r.levelno >= logging.CRITICAL]


def test_get_loop_hands_out_one_open_loop():
    loop = play.loop.get_loop()

    assert not loop.is_closed()
    assert play.loop.get_loop() is loop


def test_the_loop_runs_a_coroutine_to_its_end():
    async def add(a, b):
        await asyncio.sleep(0)
        return a + b

    assert play.loop.get_loop().run_until_complete(add(2, 3)) == 5


def test_a_forked_process_gets_a_loop_of_its_own(monkeypatch):
    parents = play.loop.get_loop()
    monkeypatch.setattr(play.loop, "_loop", parents)
    monkeypatch.setattr(play.loop, "_creator_pid", play.loop._creator_pid)
    monkeypatch.setattr(play.loop.os, "getpid", lambda: -12345)

    childs = play.loop.get_loop()

    try:
        assert childs is not parents
        assert play.loop.get_loop() is childs
    finally:
        childs.close()


def _raised(message):
    """A ValueError that was really raised, so it has a traceback."""
    try:
        raise ValueError(message)
    except ValueError as error:
        return error


def test_an_error_in_a_task_is_shown_once_with_its_traceback_and_stops_the_program(
    caplog,
):
    globals_list.program_state = ProgramState.RUNNING
    loop = play.loop.get_loop()

    with caplog.at_level(logging.CRITICAL, logger="play"):
        for message in ("first typo", "second typo"):
            loop.call_exception_handler(
                {
                    "message": "Task exception was never retrieved",
                    "exception": _raised(message),
                }
            )

    shown = _criticals(caplog)
    assert len(shown) == 1
    assert "Traceback" in shown[0]
    assert "ValueError: first typo" in shown[0]
    assert globals_list.program_state is ProgramState.STOPPED


def test_destroyed_pending_task_is_not_reported_as_critical(caplog):
    """Tasks alive at interpreter shutdown must not shout CRITICAL at the user.

    asyncio hands "Task was destroyed but it is pending!" to the loop's
    exception handler, which used to log it as CRITICAL — after the program had
    already finished, about something the user cannot act on.
    """
    loop = play.loop.get_loop()

    with caplog.at_level(logging.DEBUG, logger="play"):
        loop.call_exception_handler(
            {"message": "Task was destroyed but it is pending!"}
        )

    assert _criticals(caplog) == []


def test_real_async_failures_are_still_reported_and_stop_the_program(caplog):
    """The quiet path above must not swallow genuine errors."""
    globals_list.program_state = ProgramState.RUNNING

    with caplog.at_level(logging.DEBUG, logger="play"):
        play.loop.get_loop().call_exception_handler(
            {"message": "Some other asyncio problem", "future": None}
        )

    assert _criticals(caplog) == ["Some other asyncio problem"]
    assert globals_list.program_state is ProgramState.STOPPED


def test_a_task_made_after_the_program_stopped_never_runs():
    ran = []

    async def late():
        ran.append(True)

    globals_list.program_state = ProgramState.STOPPED
    task = play.loop.create_task(late())

    with pytest.raises(asyncio.CancelledError):
        play.loop.get_loop().run_until_complete(task)
    assert ran == []
