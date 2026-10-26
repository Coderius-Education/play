"""listen_to_failure: the game loop's error goes on, is shown once and stops the program."""

import logging

import pytest

from play.core.game_loop_wrapper import listen_to_failure
from play.globals import globals_list, ProgramState
from play.loop import get_loop


def _add(a, b):
    """Return the sum of *a* and *b*."""
    return a + b


async def _add_async(a, b):
    """Return the sum of *a* and *b*, as a coroutine."""
    return a + b


def _fail():
    """Raise a ValueError."""
    raise ValueError("sync error")


async def _fail_async():
    """Raise a ValueError, as a coroutine."""
    raise ValueError("async error")


@pytest.mark.parametrize("function", [_add, _add_async], ids=["def", "async def"])
def test_a_wrapped_function_returns_its_value(function):
    assert get_loop().run_until_complete(listen_to_failure()(function)(2, 3)) == 5


@pytest.mark.parametrize(
    "function, message",
    [(_fail, "sync error"), (_fail_async, "async error")],
    ids=["def", "async def"],
)
def test_an_error_is_passed_on_shown_and_stops_the_program(function, message, caplog):
    globals_list.program_state = ProgramState.RUNNING

    with caplog.at_level(logging.CRITICAL, logger="play"):
        with pytest.raises(ValueError, match=message):
            get_loop().run_until_complete(listen_to_failure()(function)())

    assert message in caplog.text
    assert globals_list.program_state is ProgramState.STOPPED


def test_only_the_first_of_two_errors_is_shown(caplog):
    with caplog.at_level(logging.CRITICAL, logger="play"):
        for function in (_fail, _fail_async):
            with pytest.raises(ValueError):
                get_loop().run_until_complete(listen_to_failure()(function)())

    shown = [r.getMessage() for r in caplog.records if r.levelno == logging.CRITICAL]
    assert len(shown) == 1
    assert "sync error" in shown[0]
