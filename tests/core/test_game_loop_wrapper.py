"""Tests for listen_to_failure decorator."""

import asyncio
import pytest
import sys

sys.path.insert(0, ".")


def test_listen_to_failure_sync_function_returns_value():
    """Test that a sync function's return value passes through."""
    from play.core.game_loop_wrapper import listen_to_failure

    @listen_to_failure()
    def add(a, b):
        return a + b

    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(add(2, 3))
    loop.close()

    assert result == 5


def test_listen_to_failure_async_function_returns_value():
    """Test that an async function's return value passes through."""
    from play.core.game_loop_wrapper import listen_to_failure

    @listen_to_failure()
    async def add(a, b):
        return a + b

    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(add(2, 3))
    loop.close()

    assert result == 5


def test_listen_to_failure_sync_exception_is_raised():
    """Test that a sync function's exception is re-raised."""
    from play.core.game_loop_wrapper import listen_to_failure

    @listen_to_failure()
    def fail():
        raise ValueError("sync error")

    loop = asyncio.new_event_loop()
    with pytest.raises(ValueError, match="sync error"):
        loop.run_until_complete(fail())
    loop.close()


def test_listen_to_failure_async_exception_is_raised():
    """Test that an async function's exception is re-raised."""
    from play.core.game_loop_wrapper import listen_to_failure

    @listen_to_failure()
    async def fail():
        raise ValueError("async error")

    loop = asyncio.new_event_loop()
    with pytest.raises(ValueError, match="async error"):
        loop.run_until_complete(fail())
    loop.close()


def test_listen_to_failure_stops_loop_on_exception():
    """Test that the event loop is stopped when an exception occurs."""
    from play.core.game_loop_wrapper import listen_to_failure
    from play.loop import loop as _loop

    stopped = [False]
    original_stop = _loop.stop

    def mock_stop():
        stopped[0] = True

    _loop.stop = mock_stop

    @listen_to_failure()
    async def fail():
        raise RuntimeError("boom")

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(fail())
    except RuntimeError:
        pass
    loop.close()

    _loop.stop = original_stop

    assert stopped[0] is True, "loop.stop() should have been called"


def test_listen_to_failure_logs_exception(caplog):
    """Test that the exception is logged with critical level."""
    import logging
    from play.core.game_loop_wrapper import listen_to_failure

    @listen_to_failure()
    async def fail():
        raise RuntimeError("log me")

    loop = asyncio.new_event_loop()
    with caplog.at_level(logging.CRITICAL):
        try:
            loop.run_until_complete(fail())
        except RuntimeError:
            pass
    loop.close()

    assert any("log me" in record.message for record in caplog.records)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
