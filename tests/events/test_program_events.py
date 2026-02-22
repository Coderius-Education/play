"""Tests for program event decorators like when_program_starts and repeat_forever."""

import pytest



def test_when_program_starts_decorator():
    """Test play.when_program_starts decorator."""
    import play

    callback_called = []

    @play.when_program_starts
    def on_start():
        callback_called.append(True)

    # Verify callback was registered
    from play.callback import callback_manager, CallbackType

    callbacks = list(callback_manager.get_callback([CallbackType.WHEN_PROGRAM_START]))
    assert len(callbacks) > 0


def test_repeat_forever_decorator():
    """Test play.repeat_forever decorator."""
    import play

    callback_called = []

    @play.repeat_forever
    def loop():
        callback_called.append(True)

    # Verify callback was registered
    from play.callback import callback_manager, CallbackType

    callbacks = list(callback_manager.get_callback([CallbackType.REPEAT_FOREVER]))
    assert len(callbacks) > 0


def test_when_program_starts_returns_function():
    """Test that when_program_starts returns the original function."""
    import play

    def my_function():
        return "test"

    decorated = play.when_program_starts(my_function)

    # Should return the original function
    assert decorated == my_function


def test_repeat_forever_returns_function():
    """Test that repeat_forever returns the original function."""
    import play

    def my_function():
        return "test"

    decorated = play.repeat_forever(my_function)

    # Should return the original function
    assert decorated == my_function


def test_when_program_starts_multiple_callbacks():
    """Test that multiple when_program_starts callbacks can be registered."""
    import play

    callback_called = []

    @play.when_program_starts
    def first():
        callback_called.append(1)

    @play.when_program_starts
    def second():
        callback_called.append(2)

    # Verify both callbacks were registered
    from play.callback import callback_manager, CallbackType

    callbacks = list(callback_manager.get_callback([CallbackType.WHEN_PROGRAM_START]))
    assert len(callbacks) >= 2


def test_repeat_forever_multiple_callbacks():
    """Test that multiple repeat_forever callbacks can be registered."""
    import play

    callback_called = []

    @play.repeat_forever
    def first():
        callback_called.append(1)

    @play.repeat_forever
    def second():
        callback_called.append(2)

    # Verify both callbacks were registered
    from play.callback import callback_manager, CallbackType

    callbacks = list(callback_manager.get_callback([CallbackType.REPEAT_FOREVER]))
    assert len(callbacks) >= 2


def test_when_program_starts_with_async_function():
    """Test when_program_starts with an async function."""
    import play

    @play.when_program_starts
    async def async_start():
        return "async"

    # Should still register the callback
    from play.callback import callback_manager, CallbackType

    callbacks = list(callback_manager.get_callback([CallbackType.WHEN_PROGRAM_START]))
    assert len(callbacks) > 0


def test_repeat_forever_with_async_function():
    """Test repeat_forever with an async function."""
    import play

    @play.repeat_forever
    async def async_loop():
        return "async"

    # Should still register the callback
    from play.callback import callback_manager, CallbackType

    callbacks = list(callback_manager.get_callback([CallbackType.REPEAT_FOREVER]))
    assert len(callbacks) > 0
