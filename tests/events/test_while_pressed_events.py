"""Tests for while_pressed continuous input event decorators."""

import pytest


@pytest.fixture(autouse=True)
def clear_while_pressed_callbacks():
    """Clear while_pressed callback state before and after each test."""
    from play.callback import callback_manager, CallbackType

    callback_manager.remove_callbacks(CallbackType.WHILE_KEY_PRESSED)
    callback_manager.remove_callbacks(CallbackType.WHILE_MOUSE_PRESSED)
    callback_manager.remove_callbacks(CallbackType.WHILE_CONTROLLER_BUTTON_PRESSED)
    yield
    callback_manager.remove_callbacks(CallbackType.WHILE_KEY_PRESSED)
    callback_manager.remove_callbacks(CallbackType.WHILE_MOUSE_PRESSED)
    callback_manager.remove_callbacks(CallbackType.WHILE_CONTROLLER_BUTTON_PRESSED)


def test_while_key_pressed_decorator():
    """Test play.while_key_pressed decorator registers callback."""
    import play

    @play.while_key_pressed("a")
    def on_a_held(key=None):
        pass

    from play.callback import callback_manager, CallbackType

    callbacks = list(
        callback_manager.get_callback([CallbackType.WHILE_KEY_PRESSED], "a")
    )
    assert len(callbacks) > 0


def test_while_key_pressed_multiple_keys():
    """Test play.while_key_pressed with multiple keys."""
    import play

    @play.while_key_pressed("left", "right")
    def on_held(key=None):
        pass

    from play.callback import callback_manager, CallbackType

    callbacks_left = list(
        callback_manager.get_callback([CallbackType.WHILE_KEY_PRESSED], "left")
    )
    callbacks_right = list(
        callback_manager.get_callback([CallbackType.WHILE_KEY_PRESSED], "right")
    )
    assert len(callbacks_left) > 0
    assert len(callbacks_right) > 0


def test_while_any_key_pressed_decorator():
    """Test play.while_any_key_pressed decorator registers callback."""
    import play

    @play.while_any_key_pressed
    def on_any_held(key):
        pass

    from play.callback import callback_manager, CallbackType

    callbacks = list(
        callback_manager.get_callback([CallbackType.WHILE_KEY_PRESSED], "any")
    )
    assert len(callbacks) > 0


def test_while_any_key_pressed_invalid_argument():
    """Test that while_any_key_pressed raises error with non-callable."""
    import play

    with pytest.raises(ValueError, match="doesn't use a list of keys"):

        @play.while_any_key_pressed("invalid")
        def bad_usage():
            pass


def test_while_key_pressed_invalid_key_type():
    """Test that while_key_pressed validates key types."""
    import play

    with pytest.raises(ValueError, match="Key must be a string or a list of strings"):

        @play.while_key_pressed(123)
        def bad_usage():
            pass


def test_while_key_pressed_uses_pressed_not_pressed_this_frame():
    """Test that WHILE_KEY_PRESSED uses keyboard_state.pressed (held keys),
    whereas PRESSED_KEYS uses keyboard_state.pressed_this_frame (new keys only).
    This verifies the key distinction between the two callback types."""
    import pygame
    from play.io.keypress import keyboard_state
    from play.core.keyboard_loop import handle_keyboard_events
    from play.callback import CallbackType

    # Simulate key held down for two frames
    down = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
    handle_keyboard_events(down)

    # After first KEYDOWN, key is in both pressed and pressed_this_frame
    assert "space" in keyboard_state.pressed
    assert "space" in keyboard_state.pressed_this_frame

    # Clear per-frame state (as the game loop does between frames)
    keyboard_state.clear()

    # After clearing, key is still in pressed (held) but NOT in pressed_this_frame
    assert "space" in keyboard_state.pressed
    assert "space" not in keyboard_state.pressed_this_frame

    # PRESSED_KEYS (when_key_pressed) would NOT fire — pressed_this_frame is empty
    # WHILE_KEY_PRESSED would STILL fire — pressed is not empty
    # This is the intended behavior difference

    # Clean up simulated keyboard state so it doesn't leak into subsequent tests
    keyboard_state.pressed.clear()
    keyboard_state.pressed_this_frame.clear()


def test_while_mouse_pressed_decorator():
    """Test play.while_mouse_pressed decorator registers callback."""
    import play

    @play.while_mouse_pressed
    def on_mouse_held():
        pass

    from play.callback import callback_manager, CallbackType

    callbacks = list(callback_manager.get_callback([CallbackType.WHILE_MOUSE_PRESSED]))
    assert len(callbacks) > 0


def test_while_mouse_pressed_is_tied_to_is_clicked():
    """Test that while_mouse_pressed is driven by mouse._is_clicked state.

    The mouse_loop checks mouse._is_clicked each frame to decide whether to
    fire WHILE_MOUSE_PRESSED callbacks — unlike WHEN_CLICKED which is only
    triggered on the frame the click event occurs.
    """
    import pygame
    from play.io.mouse import mouse
    from play.core.mouse_loop import handle_mouse_events, mouse_state

    # Simulate click down
    event_down = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"pos": (400, 300), "button": 1}
    )
    handle_mouse_events(event_down)
    assert mouse._is_clicked is True

    # Clear per-frame state (as game loop does between frames)
    mouse_state.clear()
    assert mouse_state.click_happened is False

    # Mouse is still held — while_mouse_pressed should fire (is_clicked still True)
    assert mouse._is_clicked is True

    # Simulate release
    event_up = pygame.event.Event(
        pygame.MOUSEBUTTONUP, {"pos": (400, 300), "button": 1}
    )
    handle_mouse_events(event_up)
    assert mouse._is_clicked is False


def test_while_mouse_pressed_fires_on_held_frames():
    """Test that WHILE_MOUSE_PRESSED fires on frames where mouse is held
    but no new click event occurred (click_happened is False).

    This verifies the game loop condition includes mouse._is_clicked so that
    handle_mouse_loop is called even when mouse_state.click_happened is False.
    """
    import asyncio
    import play
    from play.core.mouse_loop import handle_mouse_events, handle_mouse_loop, mouse_state
    from play.io.mouse import mouse

    fired_count = 0

    @play.mouse.while_pressed
    def on_held():
        nonlocal fired_count
        fired_count += 1

    import pygame

    # Frame 1: MOUSEBUTTONDOWN — click_happened=True, _is_clicked=True
    event_down = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"pos": (0, 0), "button": 1}
    )
    handle_mouse_events(event_down)
    assert mouse._is_clicked is True
    asyncio.get_event_loop().run_until_complete(handle_mouse_loop())
    assert fired_count == 1

    # Simulate next frame: clear per-frame state (click_happened becomes False)
    mouse_state.clear()
    assert mouse_state.click_happened is False
    assert mouse._is_clicked is True  # still held

    # Frame 2: no new event — but _is_clicked is True, so loop should still call handle_mouse_loop
    asyncio.get_event_loop().run_until_complete(handle_mouse_loop())
    assert fired_count == 2  # fired again on held frame

    # Clean up
    event_up = pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": (0, 0), "button": 1})
    handle_mouse_events(event_up)


def test_controllers_while_button_pressed_decorator():
    """Test controllers.while_button_pressed decorator registers callback."""
    from play.io.controllers import controllers
    from play.callback import callback_manager, CallbackType

    @controllers.while_button_pressed(0, 0)
    def on_button_held(button=None):
        pass

    callbacks = list(
        callback_manager.get_callback([CallbackType.WHILE_CONTROLLER_BUTTON_PRESSED], 0)
    )
    assert len(callbacks) > 0


def test_controllers_while_any_button_pressed_decorator():
    """Test controllers.while_any_button_pressed decorator registers callback."""
    from play.io.controllers import controllers
    from play.callback import callback_manager, CallbackType

    @controllers.while_any_button_pressed(0)
    def on_any_button_held(button=None):
        pass

    callbacks = list(
        callback_manager.get_callback(
            [CallbackType.WHILE_CONTROLLER_BUTTON_PRESSED], "any"
        )
    )
    assert len(callbacks) > 0
