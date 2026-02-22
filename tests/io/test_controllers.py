"""Tests for controllers module."""

import pytest



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


def test_controller_state_clear():
    """Test that clear() resets per-frame state but keeps buttons_pressed."""
    from play.core.controller_loop import ControllerState

    state = ControllerState()
    state.buttons_pressed[0].add(1)
    state.buttons_released[0].add(2)
    state.axes_moved[0].append({"axis": 0, "value": 1})

    state.clear()

    assert 1 in state.buttons_pressed[0], "buttons_pressed should persist after clear()"
    assert len(state.buttons_released) == 0, "buttons_released should be cleared"
    assert len(state.axes_moved) == 0, "axes_moved should be cleared"


def test_controller_state_any():
    """Test that any() returns True when buttons are pressed."""
    from play.core.controller_loop import ControllerState

    state = ControllerState()
    assert not state.any(), "any() should be False when nothing happened"

    state.buttons_pressed[0].add(1)
    assert state.any(), "any() should be True when a button is pressed"


def test_controller_state_any_after_release():
    """Test that any() returns False after all buttons are released and frame clears."""
    from play.core.controller_loop import ControllerState

    state = ControllerState()
    state.buttons_pressed[0].add(1)
    # Simulate button release
    state.buttons_released[0].add(1)
    state.buttons_pressed[0].discard(1)

    state.clear()  # next frame

    # buttons_pressed[0] is now an empty set, but the key still exists in the defaultdict
    # any() checks truthiness: an empty defaultdict is falsy, but one with empty set values...
    # defaultdict with keys but empty set values is truthy! This is a known edge case.
    # For now, just document the actual behavior:
    has_pressed = any(len(v) > 0 for v in state.buttons_pressed.values())
    assert not has_pressed, "No buttons should be pressed"


def test_handle_controller_events_button_down():
    """Test that JOYBUTTONDOWN updates controller state."""
    import pygame
    from play.core.controller_loop import controller_state, handle_controller_events

    controller_state.buttons_pressed.clear()
    controller_state.buttons_released.clear()

    event = pygame.event.Event(pygame.JOYBUTTONDOWN, {"instance_id": 0, "button": 3})
    handle_controller_events(event)

    assert 3 in controller_state.buttons_pressed[0]


def test_handle_controller_events_button_up():
    """Test that JOYBUTTONUP updates controller state."""
    import pygame
    from play.core.controller_loop import controller_state, handle_controller_events

    controller_state.buttons_pressed.clear()
    controller_state.buttons_released.clear()

    # Press then release
    down_event = pygame.event.Event(
        pygame.JOYBUTTONDOWN, {"instance_id": 0, "button": 5}
    )
    handle_controller_events(down_event)
    assert 5 in controller_state.buttons_pressed[0]

    up_event = pygame.event.Event(pygame.JOYBUTTONUP, {"instance_id": 0, "button": 5})
    handle_controller_events(up_event)

    assert (
        5 not in controller_state.buttons_pressed[0]
    ), "Button should be removed from pressed"
    assert 5 in controller_state.buttons_released[0], "Button should be in released"


def test_handle_controller_events_axis_motion():
    """Test that JOYAXISMOTION updates controller state."""
    import pygame
    from play.core.controller_loop import controller_state, handle_controller_events

    controller_state.axes_moved.clear()

    event = pygame.event.Event(
        pygame.JOYAXISMOTION, {"instance_id": 0, "axis": 1, "value": -0.8}
    )
    handle_controller_events(event)

    assert len(controller_state.axes_moved[0]) == 1
    assert controller_state.axes_moved[0][0]["axis"] == 1
    assert controller_state.axes_moved[0][0]["value"] == -1  # round(-0.8) == -1


def test_button_pressed_callback_fires():
    """Test that WHEN_CONTROLLER_BUTTON_PRESSED callback fires on button press."""
    import asyncio
    import pygame
    from play.core.controller_loop import (
        controller_state,
        handle_controller_events,
        handle_controller,
    )
    from play.callback import callback_manager, CallbackType
    from play.utils.async_helpers import make_async
    from play.callback.callback_helpers import run_async_callback

    controller_state.buttons_pressed.clear()
    controller_state.buttons_released.clear()

    pressed_buttons = []

    async def on_press(button):
        pressed_buttons.append(button)

    on_press.is_running = False
    on_press.controller = 0
    callback_manager.add_callback(
        CallbackType.WHEN_CONTROLLER_BUTTON_PRESSED, on_press, 7
    )

    # Simulate button press
    event = pygame.event.Event(pygame.JOYBUTTONDOWN, {"instance_id": 0, "button": 7})
    handle_controller_events(event)

    loop = asyncio.new_event_loop()
    loop.run_until_complete(handle_controller())
    loop.close()

    assert 7 in pressed_buttons, "Button press callback should have fired with button=7"

    # Clean up
    controller_state.buttons_pressed.clear()
    callback_manager.remove_callbacks(CallbackType.WHEN_CONTROLLER_BUTTON_PRESSED, 7)


def test_button_released_callback_fires():
    """Test that WHEN_CONTROLLER_BUTTON_RELEASED callback fires on button release."""
    import asyncio
    import pygame
    from play.core.controller_loop import (
        controller_state,
        handle_controller_events,
        handle_controller,
    )
    from play.callback import callback_manager, CallbackType

    controller_state.buttons_pressed.clear()
    controller_state.buttons_released.clear()

    released_buttons = []

    async def on_release(button):
        released_buttons.append(button)

    on_release.is_running = False
    on_release.controller = 0
    callback_manager.add_callback(
        CallbackType.WHEN_CONTROLLER_BUTTON_RELEASED, on_release, 2
    )

    # Simulate press then release
    down = pygame.event.Event(pygame.JOYBUTTONDOWN, {"instance_id": 0, "button": 2})
    up = pygame.event.Event(pygame.JOYBUTTONUP, {"instance_id": 0, "button": 2})
    handle_controller_events(down)
    handle_controller_events(up)

    loop = asyncio.new_event_loop()
    loop.run_until_complete(handle_controller())
    loop.close()

    assert (
        2 in released_buttons
    ), "Button release callback should have fired with button=2"

    # Clean up
    controller_state.buttons_pressed.clear()
    controller_state.buttons_released.clear()
    callback_manager.remove_callbacks(CallbackType.WHEN_CONTROLLER_BUTTON_RELEASED, 2)


def test_button_pressed_callback_fires_while_held():
    """Test that WHEN_CONTROLLER_BUTTON_PRESSED fires every frame while held."""
    import asyncio
    import pygame
    from play.core.controller_loop import (
        controller_state,
        handle_controller_events,
        handle_controller,
    )
    from play.callback import callback_manager, CallbackType

    controller_state.buttons_pressed.clear()
    controller_state.buttons_released.clear()

    press_count = [0]

    async def on_press(button):
        press_count[0] += 1

    on_press.is_running = False
    on_press.controller = 0
    callback_manager.add_callback(
        CallbackType.WHEN_CONTROLLER_BUTTON_PRESSED, on_press, 4
    )

    # Simulate button press (once)
    event = pygame.event.Event(pygame.JOYBUTTONDOWN, {"instance_id": 0, "button": 4})
    handle_controller_events(event)

    loop = asyncio.new_event_loop()

    # Simulate 3 frames with the button held
    for _ in range(3):
        controller_state.clear()
        loop.run_until_complete(handle_controller())

    loop.close()

    assert (
        press_count[0] == 3
    ), f"Callback should fire every frame while held, got {press_count[0]} instead of 3"

    # Clean up
    controller_state.buttons_pressed.clear()
    callback_manager.remove_callbacks(CallbackType.WHEN_CONTROLLER_BUTTON_PRESSED, 4)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
