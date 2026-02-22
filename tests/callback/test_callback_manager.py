"""Tests for callback manager."""

import pytest



def test_callback_manager_exists():
    """Test that callback_manager exists."""
    import play
    from play.callback import callback_manager

    result = []

    @play.when_program_starts
    def check():
        result.append(callback_manager is not None)
        play.stop_program()

    play.start_program()

    assert result[0] is True


def test_callback_type_enum():
    """Test that all CallbackType enums exist."""
    import play
    from play.callback import CallbackType

    result = []

    @play.when_program_starts
    def check():
        expected_types = [
            "REPEAT_FOREVER",
            "WHEN_PROGRAM_START",
            "PRESSED_KEYS",
            "RELEASED_KEYS",
            "WHEN_CLICKED",
            "WHEN_CLICK_RELEASED",
            "WHEN_CLICKED_SPRITE",
            "WHEN_TOUCHING",
            "WHEN_STOPPED_TOUCHING",
            "WHEN_TOUCHING_WALL",
            "WHEN_STOPPED_TOUCHING_WALL",
            "WHEN_CONTROLLER_BUTTON_PRESSED",
            "WHEN_CONTROLLER_BUTTON_RELEASED",
            "WHEN_CONTROLLER_AXIS_MOVED",
            "WHEN_RESIZED",
            "WHEN_CLICK_RELEASED_SPRITE",
        ]
        for type_name in expected_types:
            result.append((type_name, hasattr(CallbackType, type_name)))
        play.stop_program()

    play.start_program()

    for type_name, exists in result:
        assert exists is True, f"CallbackType missing: {type_name}"


def test_add_callback():
    """Test adding a callback to the manager."""
    import play
    from play.callback import callback_manager, CallbackType

    result = []

    def my_callback():
        pass

    @play.when_program_starts
    def check():
        # Add a custom callback
        callback_manager.add_callback(CallbackType.REPEAT_FOREVER, my_callback)
        callbacks = callback_manager.get_callbacks(CallbackType.REPEAT_FOREVER)
        result.append(callbacks is not None)
        result.append(len(callbacks) > 0)
        play.stop_program()

    play.start_program()

    assert result[0] is True
    assert result[1] is True


def test_add_callback_with_discriminator():
    """Test adding a callback with discriminator."""
    import play
    from play.callback import callback_manager, CallbackType

    result = []

    def my_callback():
        pass

    @play.when_program_starts
    def check():
        callback_manager.add_callback(CallbackType.PRESSED_KEYS, my_callback, "space")
        callbacks = callback_manager.get_callback(CallbackType.PRESSED_KEYS, "space")
        result.append(callbacks is not None)
        play.stop_program()

    play.start_program()

    assert result[0] is True


def test_get_callbacks():
    """Test getting all callbacks of a type."""
    import play
    from play.callback import callback_manager, CallbackType

    result = []

    @play.when_program_starts
    def check():
        # WHEN_PROGRAM_START should have at least this callback
        callbacks = callback_manager.get_callbacks(CallbackType.WHEN_PROGRAM_START)
        result.append(callbacks is not None)
        play.stop_program()

    play.start_program()

    assert result[0] is True


def test_get_callback_with_list():
    """Test getting callbacks with list of types."""
    import play
    from play.callback import callback_manager, CallbackType

    result = []

    @play.when_program_starts
    def check():
        callbacks = callback_manager.get_callback(
            [CallbackType.WHEN_PROGRAM_START, CallbackType.REPEAT_FOREVER]
        )
        result.append(isinstance(callbacks, list))
        play.stop_program()

    play.start_program()

    assert result[0] is True


def test_run_callbacks():
    """Test running callbacks."""
    import play
    from play.callback import callback_manager, CallbackType

    callback_ran = [False]

    async def test_callback():
        callback_ran[0] = True

    @play.when_program_starts
    def setup():
        callback_manager.add_callback(CallbackType.REPEAT_FOREVER, test_callback)

    frame_count = [0]

    @play.repeat_forever
    def check():
        frame_count[0] += 1
        if frame_count[0] > 5:
            play.stop_program()

    play.start_program()

    assert callback_ran[0] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
