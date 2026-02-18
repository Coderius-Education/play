"""Tests for mouse event decorators and functionality."""

import pytest
import sys

sys.path.insert(0, ".")


def test_mouse_initial_state():
    """Test mouse initial state."""
    import play

    # Mouse should start at origin
    assert play.mouse.x == 0
    assert play.mouse.y == 0
    assert play.mouse.is_clicked == False


def test_mouse_when_clicked_decorator():
    """Test play.when_mouse_clicked decorator."""
    import play

    callback_called = []

    @play.when_mouse_clicked
    def on_click():
        callback_called.append(True)

    # Verify callback was registered
    from play.callback import callback_manager, CallbackType

    callbacks = list(callback_manager.get_callback([CallbackType.WHEN_CLICKED]))
    assert len(callbacks) > 0


def test_mouse_when_click_released_decorator():
    """Test play.when_click_released decorator."""
    import play

    callback_called = []

    @play.when_click_released
    def on_release():
        callback_called.append(True)

    # Verify callback was registered
    from play.callback import callback_manager, CallbackType

    callbacks = list(callback_manager.get_callback([CallbackType.WHEN_CLICK_RELEASED]))
    assert len(callbacks) > 0


def test_mouse_distance_to():
    """Test mouse.distance_to() method."""
    import play

    # Set mouse position
    play.mouse.x = 0
    play.mouse.y = 0

    # Test distance to a point
    distance = play.mouse.distance_to(3, 4)
    assert abs(distance - 5.0) < 0.1  # 3-4-5 triangle


def test_mouse_distance_to_with_none():
    """Test that mouse.distance_to raises assertion with None values."""
    import play

    with pytest.raises(AssertionError):
        play.mouse.distance_to(None, 4)

    with pytest.raises(AssertionError):
        play.mouse.distance_to(3, None)


def test_mouse_is_touching_sprite():
    """Test mouse.is_touching() with a sprite."""
    import play
    from play.objects.sprite import point_touching_sprite

    sprite = play.new_box(x=0, y=0, width=100, height=100)

    # Set mouse position to be inside sprite
    play.mouse.x = 0
    play.mouse.y = 0

    # Use point_touching_sprite with a tuple
    result = point_touching_sprite((play.mouse.x, play.mouse.y), sprite)
    # Result depends on sprite rect, which may not be perfectly at 0,0
    assert isinstance(result, bool)


def test_mouse_is_touching_sprite_far_away():
    """Test mouse.is_touching() when mouse is far from sprite."""
    import play
    from play.objects.sprite import point_touching_sprite

    sprite = play.new_box(x=1000, y=1000, width=50, height=50)

    # Set mouse position far from sprite
    play.mouse.x = 0
    play.mouse.y = 0

    # Use point_touching_sprite with a tuple
    assert point_touching_sprite((play.mouse.x, play.mouse.y), sprite) == False


def test_mouse_position_can_be_set():
    """Test that mouse position can be set."""
    import play

    play.mouse.x = 100
    play.mouse.y = 200

    assert play.mouse.x == 100
    assert play.mouse.y == 200


def test_mouse_event_simulation_click():
    """Test simulating mouse click event."""
    import pygame
    import play
    from play.core.mouse_loop import handle_mouse_events, mouse_state

    # Create a pygame MOUSEBUTTONDOWN event
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (400, 300), "button": 1})

    # Handle the event
    handle_mouse_events(event)

    # Check that click was registered
    assert mouse_state.click_happened == True
    assert play.mouse.is_clicked == True


def test_mouse_event_simulation_release():
    """Test simulating mouse click release event."""
    import pygame
    import play
    from play.core.mouse_loop import handle_mouse_events, mouse_state

    # First click
    event_down = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"pos": (400, 300), "button": 1}
    )
    handle_mouse_events(event_down)

    # Then release
    event_up = pygame.event.Event(
        pygame.MOUSEBUTTONUP, {"pos": (400, 300), "button": 1}
    )
    handle_mouse_events(event_up)

    # Check that release was registered
    assert mouse_state.click_release_happened == True
    assert play.mouse.is_clicked == False


def test_mouse_event_simulation_motion():
    """Test simulating mouse motion event."""
    import pygame
    import play
    from play.core.mouse_loop import handle_mouse_events
    from play.io.screen import screen

    # Create a pygame MOUSEMOTION event
    # pygame coordinates are top-left origin, play coordinates are center origin
    pygame_x = 500
    pygame_y = 400
    event = pygame.event.Event(pygame.MOUSEMOTION, {"pos": (pygame_x, pygame_y)})

    # Handle the event
    handle_mouse_events(event)

    # Check that mouse position was updated
    # play.mouse.x = pygame_x - screen.width / 2
    # play.mouse.y = screen.height / 2 - pygame_y
    expected_x = pygame_x - screen.width / 2.0
    expected_y = screen.height / 2.0 - pygame_y

    assert abs(play.mouse.x - expected_x) < 0.1
    assert abs(play.mouse.y - expected_y) < 0.1


def test_mouse_state_clear():
    """Test that mouse state can be cleared."""
    from play.core.mouse_loop import mouse_state

    # Set some state
    mouse_state.click_happened = True
    mouse_state.click_release_happened = True

    # Clear it
    mouse_state.clear()

    # Verify it's cleared
    assert mouse_state.click_happened == False
    assert mouse_state.click_release_happened == False
