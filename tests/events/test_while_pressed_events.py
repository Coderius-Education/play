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


def test_while_key_pressed_fires_every_frame_without_keydown_repeat():
    """Test that while_key_pressed fires on every game frame while a key is held,
    NOT just when KEYDOWN events occur.

    Previously, pygame.key.set_repeat(200, 16) was used to drive while_key_pressed
    via repeated KEYDOWN events. This caused a 200ms delay before the first repeat,
    then 16ms intervals — so 'key press 1 to key press 2' took 200ms while
    'key press 2 to key press 3' only took 16ms (issue #160).

    The fix: while_key_pressed is driven by keyboard_state.pressed (frame-based),
    not by KEYDOWN repeat events. This test verifies the callback fires on every
    handle_keyboard() call while a key remains in keyboard_state.pressed.
    """
    import asyncio
    import pygame
    from play.io.keypress import keyboard_state
    from play.core.keyboard_loop import handle_keyboard_events, handle_keyboard
    from play.callback import callback_manager, CallbackType
    from play.loop import get_loop
    import play

    loop = get_loop()
    fired_count = [0]

    @play.while_key_pressed("right")
    def on_right_held(key=None):
        fired_count[0] += 1

    # Simulate initial KEYDOWN
    down = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT})
    handle_keyboard_events(down)
    assert "right" in keyboard_state.pressed
    assert (
        fired_count[0] == 0
    )  # handle_keyboard_events alone does not fire the callback

    # Run handle_keyboard multiple times WITHOUT any new KEYDOWN events
    # (simulating held key across multiple game frames)
    for _ in range(5):
        loop.run_until_complete(handle_keyboard())
        loop.run_until_complete(asyncio.sleep(0))  # let fire_async_callback tasks run
        keyboard_state.pressed_this_frame.clear()
        keyboard_state.released.clear()

    assert fired_count[0] == 5, (
        f"while_key_pressed should fire every frame while key is held, "
        f"got {fired_count[0]} fires in 5 frames"
    )

    # Clean up
    keyboard_state.pressed.clear()


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
    import pygame
    from play.loop import get_loop
    from play.core.mouse_loop import handle_mouse_events, handle_mouse_loop, mouse_state
    from play.io.mouse import mouse

    loop = get_loop()
    fired_count = 0

    @play.mouse.while_pressed
    def on_held():
        nonlocal fired_count
        fired_count += 1

    # Frame 1: MOUSEBUTTONDOWN — click_happened=True, _is_clicked=True
    event_down = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"pos": (0, 0), "button": 1}
    )
    handle_mouse_events(event_down)
    assert mouse._is_clicked is True
    loop.run_until_complete(handle_mouse_loop())
    loop.run_until_complete(asyncio.sleep(0))
    assert fired_count == 1

    # Simulate next frame: clear per-frame state (click_happened becomes False)
    mouse_state.clear()
    assert mouse_state.click_happened is False
    assert mouse._is_clicked is True  # still held

    # Frame 2: no new event — but _is_clicked is True, so loop should still call handle_mouse_loop
    loop.run_until_complete(handle_mouse_loop())
    loop.run_until_complete(asyncio.sleep(0))
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


def test_while_button_pressed_chord_registers_with_frozenset_hash():
    """Test that while_button_pressed with a list of buttons registers using
    hash(frozenset(button)) as the discriminator key."""
    from play.io.controllers import controllers
    from play.callback import callback_manager, CallbackType

    chord = [1, 2]

    @controllers.while_button_pressed(0, chord)
    def on_chord_held(button=None):
        pass

    expected_key = hash(frozenset(chord))
    callbacks = list(
        callback_manager.get_callback(
            [CallbackType.WHILE_CONTROLLER_BUTTON_PRESSED], expected_key
        )
    )
    assert len(callbacks) > 0, "Chord callback should be registered with frozenset hash"


def test_while_button_pressed_chord_fires_only_on_exact_match():
    """Test that a chord (list[int]) while_button_pressed callback fires only when
    exactly those buttons are held — not a superset, not a subset.

    Chord semantics: the callback fires when hash(frozenset(held_buttons)) ==
    hash(frozenset(registered_chord)), i.e. held == {1, 2} exactly.
    """
    import asyncio
    import pygame
    from play.io.controllers import controllers
    from play.core.controller_loop import (
        controller_state,
        handle_controller_events,
        handle_controller,
    )
    from play.callback import callback_manager, CallbackType

    controller_state.buttons_pressed.clear()
    controller_state.buttons_pressed_this_frame.clear()
    controller_state.buttons_released.clear()

    fired_buttons = []

    @controllers.while_button_pressed(0, [1, 2])
    def on_chord_held(button=None):
        fired_buttons.append(button)

    from play.loop import get_loop

    loop = get_loop()

    # --- Exact match: only buttons 1 and 2 held ---
    for btn in (1, 2):
        e = pygame.event.Event(pygame.JOYBUTTONDOWN, {"instance_id": 0, "button": btn})
        handle_controller_events(e)

    loop.run_until_complete(handle_controller())
    loop.run_until_complete(asyncio.sleep(0))
    assert len(fired_buttons) > 0, "Chord callback should fire when exactly {1,2} held"

    fired_buttons.clear()
    controller_state.clear()

    # --- Superset: buttons 1, 2, and 3 held — chord should NOT fire ---
    e3 = pygame.event.Event(pygame.JOYBUTTONDOWN, {"instance_id": 0, "button": 3})
    handle_controller_events(e3)

    loop.run_until_complete(handle_controller())
    loop.run_until_complete(asyncio.sleep(0))
    assert (
        len(fired_buttons) == 0
    ), "Chord callback should NOT fire when a superset of buttons is held"

    # Clean up
    controller_state.buttons_pressed.clear()
    controller_state.buttons_pressed_this_frame.clear()
    chord_key = hash(frozenset([1, 2]))
    callback_manager.remove_callbacks(
        CallbackType.WHILE_CONTROLLER_BUTTON_PRESSED, chord_key
    )


def test_while_button_pressed_invalid_button_raises():
    """Test that while_button_pressed raises ValueError for non-int button types."""
    from play.io.controllers import controllers

    with pytest.raises(ValueError, match="Button must be an integer"):

        @controllers.while_button_pressed(0, "bad_button")
        def on_held(button=None):
            pass


def test_controller_state_any_false_after_all_buttons_released():
    """Test that ControllerState.any() returns False once all held buttons are
    released and the frame is cleared — verifying the empty-set cleanup fix."""
    import pygame
    from play.core.controller_loop import controller_state, handle_controller_events

    controller_state.buttons_pressed.clear()
    controller_state.buttons_released.clear()

    # Press two buttons
    for btn in (0, 1):
        e = pygame.event.Event(pygame.JOYBUTTONDOWN, {"instance_id": 0, "button": btn})
        handle_controller_events(e)

    assert controller_state.any(), "any() should be True while buttons held"

    # Release both buttons
    for btn in (0, 1):
        e = pygame.event.Event(pygame.JOYBUTTONUP, {"instance_id": 0, "button": btn})
        handle_controller_events(e)

    controller_state.clear()  # next frame — clears buttons_released

    assert (
        not controller_state.any()
    ), "any() should be False after all buttons released and frame cleared"

    # Clean up
    controller_state.buttons_pressed.clear()
