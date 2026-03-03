"""Coverage tests for play.io.mouse — click callbacks, is_touching, is_clicked."""

import pytest
import play
from play.io.mouse import mouse
from play.callback import callback_manager, CallbackType


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_mouse_is_clicked_default():
    """Mouse should not be clicked by default."""
    assert mouse.is_clicked is False


def test_mouse_is_touching_sprite():
    """mouse.is_touching(sprite) should return True when mouse is over the sprite."""
    box = play.new_box(color="red", x=0, y=0, width=100, height=100)
    box.start_physics(obeys_gravity=False, can_move=False)

    # Move mouse to sprite center
    mouse.x = 0
    mouse.y = 0
    assert mouse.is_touching(box) is True


def test_mouse_is_touching_sprite_miss():
    """mouse.is_touching(sprite) should return False when mouse is far away."""
    box = play.new_box(color="red", x=0, y=0, width=10, height=10)
    box.start_physics(obeys_gravity=False, can_move=False)

    mouse.x = 500
    mouse.y = 500
    assert mouse.is_touching(box) is False


def test_mouse_when_clicked_registers():
    """mouse.when_clicked should register a callback."""

    @mouse.when_clicked
    def on_click():
        pass

    assert CallbackType.WHEN_CLICKED in callback_manager.callbacks


def test_mouse_when_click_released_registers():
    """mouse.when_click_released should register a callback."""

    @mouse.when_click_released
    def on_release():
        pass

    assert CallbackType.WHEN_CLICK_RELEASED in callback_manager.callbacks


def test_mouse_distance_to():
    """mouse.distance_to should return correct distance."""
    mouse.x = 3
    mouse.y = 4
    dist = mouse.distance_to(0, 0)
    assert abs(dist - 5.0) < 0.01
