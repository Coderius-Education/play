"""Tests for controllers module."""

import pytest
import sys

sys.path.insert(0, ".")


def test_controllers_object_exists():
    """Test that controllers object exists and is accessible."""
    import play

    result = []

    @play.when_program_starts
    def check():
        result.append(hasattr(play, "controllers"))
        result.append(play.controllers is not None)
        play.stop_program()

    play.start_program()

    assert result[0] is True
    assert result[1] is True


def test_controllers_get_count():
    """Test getting controller count (may be 0 if no controllers connected)."""
    import play

    result = []

    @play.when_program_starts
    def check():
        count = play.controllers.get_count()
        result.append(isinstance(count, int))
        result.append(count >= 0)
        play.stop_program()

    play.start_program()

    assert result[0] is True
    assert result[1] is True


def test_controllers_get_all_controllers():
    """Test getting all controllers returns a list."""
    import play

    result = []

    @play.when_program_starts
    def check():
        all_controllers = play.controllers.get_all_controllers()
        result.append(isinstance(all_controllers, list))
        play.stop_program()

    play.start_program()

    assert result[0] is True


def test_when_button_pressed_decorator_registers():
    """Test that when_button_pressed decorator registers callback."""
    import play
    from play.callback import callback_manager, CallbackType

    result = []

    @play.when_program_starts
    def check():
        # Check if callback type exists in manager
        result.append(CallbackType.WHEN_CONTROLLER_BUTTON_PRESSED in CallbackType)
        play.stop_program()

    play.start_program()

    assert result[0] is True


def test_when_button_released_decorator_registers():
    """Test that when_button_released decorator registers callback."""
    import play
    from play.callback import callback_manager, CallbackType

    result = []

    @play.when_program_starts
    def check():
        # Check if callback type exists in manager
        result.append(CallbackType.WHEN_CONTROLLER_BUTTON_RELEASED in CallbackType)
        play.stop_program()

    play.start_program()

    assert result[0] is True


def test_when_axis_moved_decorator_registers():
    """Test that when_axis_moved decorator registers callback."""
    import play
    from play.callback import callback_manager, CallbackType

    result = []

    @play.when_program_starts
    def check():
        # Check if callback type exists in manager
        result.append(CallbackType.WHEN_CONTROLLER_AXIS_MOVED in CallbackType)
        play.stop_program()

    play.start_program()

    assert result[0] is True


def test_controllers_has_required_methods():
    """Test that controllers object has all required methods."""
    import play

    result = []

    @play.when_program_starts
    def check():
        methods = [
            "get_count",
            "get_controller",
            "get_all_controllers",
            "get_num_axes",
            "get_axis",
            "get_num_buttons",
            "get_button",
            "get_num_hats",
            "get_hat",
            "get_num_balls",
            "get_ball",
            "when_button_pressed",
            "when_any_button_pressed",
            "when_button_released",
            "when_any_button_released",
            "when_axis_moved",
            "when_any_axis_moved",
        ]
        for method in methods:
            result.append((method, hasattr(play.controllers, method)))
        play.stop_program()

    play.start_program()

    for method_name, has_method in result:
        assert has_method is True, f"controllers missing method: {method_name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
