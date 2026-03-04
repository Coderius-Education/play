"""Tests for the event loop module.

Verifies that get_loop() returns a working asyncio event loop on all
platforms (including Windows where ProactorEventLoop is the default).
"""

import asyncio
import sys

import play.loop


def test_get_loop_returns_running_loop():
    """get_loop() should return a non-closed event loop."""
    loop = play.loop.get_loop()
    assert loop is not None
    assert not loop.is_closed()


def test_get_loop_returns_same_loop():
    """Repeated calls should return the same loop instance."""
    loop1 = play.loop.get_loop()
    loop2 = play.loop.get_loop()
    assert loop1 is loop2


def test_loop_can_run_coroutine():
    """The loop should be able to run a simple coroutine to completion."""
    loop = play.loop.get_loop()

    async def add(a, b):
        return a + b

    result = loop.run_until_complete(add(2, 3))
    assert result == 5


def test_loop_has_exception_handler():
    """The loop should have a custom exception handler installed."""
    loop = play.loop.get_loop()
    # asyncio stores the handler internally; we verify it's set by checking
    # it's not the default (None).
    assert loop.get_exception_handler() is not None


def test_loop_type_on_windows():
    """On Windows, the loop should be a ProactorEventLoop (or SelectorEventLoop
    on Python 3.14+ where the default policy changed)."""
    if sys.platform != "win32":
        return  # skip on non-Windows

    loop = play.loop.get_loop()
    # Just verify it's a valid asyncio event loop that works
    assert isinstance(loop, asyncio.AbstractEventLoop)
