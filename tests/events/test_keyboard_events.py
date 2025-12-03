"""Tests for keyboard event decorators and functionality."""

import pytest
import sys
import pygame

sys.path.insert(0, ".")


def test_when_any_key_pressed_decorator():
    """Test play.when_any_key_pressed decorator."""
    import play

    callback_called = []

    @play.when_any_key_pressed
    def on_key(key):
        callback_called.append(key)

    # Verify callback was registered
    from play.callback import callback_manager, CallbackType

    callbacks = list(callback_manager.get_callback([CallbackType.PRESSED_KEYS], "any"))
    assert len(callbacks) > 0


def test_when_key_pressed_decorator():
    """Test play.when_key_pressed decorator with specific key."""
    import play

    callback_called = []

    @play.when_key_pressed("a")
    def on_key_a(key=None):
        callback_called.append(key)

    # Verify callback was registered
    from play.callback import callback_manager, CallbackType

    callbacks = list(callback_manager.get_callback([CallbackType.PRESSED_KEYS], "a"))
    assert len(callbacks) > 0


def test_when_key_pressed_multiple_keys():
    """Test play.when_key_pressed with multiple keys."""
    import play

    callback_called = []

    @play.when_key_pressed("a", "b", "c")
    def on_keys(key=None):
        callback_called.append(key)

    # Verify callbacks were registered for all keys
    from play.callback import callback_manager, CallbackType

    callbacks_a = list(callback_manager.get_callback([CallbackType.PRESSED_KEYS], "a"))
    callbacks_b = list(callback_manager.get_callback([CallbackType.PRESSED_KEYS], "b"))
    callbacks_c = list(callback_manager.get_callback([CallbackType.PRESSED_KEYS], "c"))

    assert len(callbacks_a) > 0
    assert len(callbacks_b) > 0
    assert len(callbacks_c) > 0


def test_when_any_key_released_decorator():
    """Test play.when_any_key_released decorator."""
    import play

    callback_called = []

    @play.when_any_key_released
    def on_release(key):
        callback_called.append(key)

    # Verify callback was registered
    from play.callback import callback_manager, CallbackType

    callbacks = list(callback_manager.get_callback([CallbackType.RELEASED_KEYS], "any"))
    assert len(callbacks) > 0


def test_when_key_released_decorator():
    """Test play.when_key_released decorator."""
    import play

    callback_called = []

    @play.when_key_released("space")
    def on_space_release(key=None):
        callback_called.append(key)

    # Verify callback was registered
    from play.callback import callback_manager, CallbackType

    callbacks = list(
        callback_manager.get_callback([CallbackType.RELEASED_KEYS], "space")
    )
    assert len(callbacks) > 0


def test_when_any_key_pressed_invalid_argument():
    """Test that when_any_key_pressed raises error with non-callable argument."""
    import play

    with pytest.raises(ValueError, match="doesn't use a list of keys"):

        @play.when_any_key_pressed("invalid")
        def bad_usage():
            pass


def test_when_any_key_released_invalid_argument():
    """Test that when_any_key_released raises error with non-callable argument."""
    import play

    with pytest.raises(ValueError, match="doesn't use a list of keys"):

        @play.when_any_key_released("invalid")
        def bad_usage():
            pass


def test_when_key_pressed_invalid_key_type():
    """Test that when_key_pressed validates key types."""
    import play

    with pytest.raises(ValueError, match="Key must be a string or a list of strings"):

        @play.when_key_pressed(123)
        def bad_usage():
            pass


def test_when_key_pressed_list_of_keys():
    """Test when_key_pressed with a list of keys (combo)."""
    import play

    callback_called = []

    @play.when_key_pressed(["a", "b"])
    def on_combo(key=None):
        callback_called.append(key)

    # Verify callback was registered
    from play.callback import callback_manager, CallbackType

    # List keys are hashed
    key_hash = hash(frozenset(["a", "b"]))
    callbacks = list(
        callback_manager.get_callback([CallbackType.PRESSED_KEYS], key_hash)
    )
    assert len(callbacks) > 0


def test_when_key_released_list_of_keys():
    """Test when_key_released with a list of keys."""
    import play

    callback_called = []

    @play.when_key_released(["ctrl", "c"])
    def on_combo_release(key=None):
        callback_called.append(key)

    # Verify callback was registered
    from play.callback import callback_manager, CallbackType

    key_hash = hash(frozenset(["ctrl", "c"]))
    callbacks = list(
        callback_manager.get_callback([CallbackType.RELEASED_KEYS], key_hash)
    )
    assert len(callbacks) > 0


def test_keyboard_state_initial():
    """Test keyboard state initial values."""
    from play.io.keypress import keyboard_state

    # Initially empty
    assert isinstance(keyboard_state.pressed, list)
    assert isinstance(keyboard_state.released, list)


def test_keyboard_state_clear():
    """Test that keyboard state can be cleared."""
    from play.io.keypress import keyboard_state

    # Add some released keys
    keyboard_state.released.append("a")
    keyboard_state.released.append("b")

    # Clear
    keyboard_state.clear()

    # Verify released is cleared
    assert len(keyboard_state.released) == 0


def test_key_num_to_name():
    """Test converting pygame key event to name."""
    from play.io.keypress import key_num_to_name

    # Create a fake key event
    class FakeKeyEvent:
        def __init__(self, key):
            self.key = key

    event = FakeKeyEvent(pygame.K_a)
    name = key_num_to_name(event)

    assert name == "a"


def test_key_num_to_name_special_keys():
    """Test converting special keys to names."""
    from play.io.keypress import key_num_to_name

    class FakeKeyEvent:
        def __init__(self, key):
            self.key = key

    # Test space
    event_space = FakeKeyEvent(pygame.K_SPACE)
    assert key_num_to_name(event_space) == "space"

    # Test return
    event_return = FakeKeyEvent(pygame.K_RETURN)
    assert key_num_to_name(event_return) == "return"

    # Test escape
    event_escape = FakeKeyEvent(pygame.K_ESCAPE)
    assert key_num_to_name(event_escape) == "escape"


def test_when_key_pressed_list_invalid_subkey():
    """Test that when_key_pressed validates subkeys in list."""
    import play

    with pytest.raises(ValueError, match="Key must be a string or a list of strings"):

        @play.when_key_pressed(["a", 123])
        def bad_usage():
            pass
