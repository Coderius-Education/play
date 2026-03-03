"""Test the module-level event decorators in play.api.events.

These are the play.when_sprite_clicked(), play.when_sprite_click_released(),
play.when_mouse_clicked, and play.when_click_released forms — the module-level
equivalents of the sprite/mouse method decorators.
"""

import pytest
import play
from play.callback import callback_manager, CallbackType


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_when_sprite_clicked_registers_callback():
    """play.when_sprite_clicked(sprite) should register a click callback."""
    box = play.new_box(color="red", x=0, y=0, width=10, height=10)
    called = []

    @play.when_sprite_clicked(box)
    def on_click(sprite):
        called.append(sprite)

    assert CallbackType.WHEN_CLICKED_SPRITE in callback_manager.callbacks


def test_when_sprite_clicked_multiple_sprites():
    """play.when_sprite_clicked can register on multiple sprites at once."""
    box1 = play.new_box(color="red", x=0, y=0, width=10, height=10)
    box2 = play.new_box(color="blue", x=20, y=0, width=10, height=10)

    @play.when_sprite_clicked(box1, box2)
    def on_click(sprite):
        pass

    cbs = callback_manager.callbacks[CallbackType.WHEN_CLICKED_SPRITE]
    assert len(cbs) >= 2


def test_when_sprite_click_released_registers_callback():
    """play.when_sprite_click_released(sprite) should register a release callback."""
    box = play.new_box(color="red", x=0, y=0, width=10, height=10)

    @play.when_sprite_click_released(box)
    def on_release(sprite):
        pass

    assert CallbackType.WHEN_CLICK_RELEASED_SPRITE in callback_manager.callbacks


def test_when_mouse_clicked_registers_callback():
    """play.when_mouse_clicked should register a mouse click callback."""

    @play.when_mouse_clicked
    def on_click():
        pass

    assert CallbackType.WHEN_CLICKED in callback_manager.callbacks


def test_when_click_released_registers_callback():
    """play.when_click_released should register a mouse release callback."""

    @play.when_click_released
    def on_release():
        pass

    assert CallbackType.WHEN_CLICK_RELEASED in callback_manager.callbacks


def test_when_program_starts_registers_callback():
    """play.when_program_starts should register a WHEN_PROGRAM_START callback."""

    @play.when_program_starts
    def on_start():
        pass

    assert CallbackType.WHEN_PROGRAM_START in callback_manager.callbacks


def test_repeat_forever_registers_callback():
    """play.repeat_forever should register a REPEAT_FOREVER callback."""

    @play.repeat_forever
    def tick():
        pass

    assert CallbackType.REPEAT_FOREVER in callback_manager.callbacks


def test_when_any_key_pressed_not_callable_raises():
    """play.when_any_key_pressed with a non-callable should raise ValueError."""
    with pytest.raises(ValueError):
        play.when_any_key_pressed("not a function")


def test_when_any_key_released_not_callable_raises():
    """play.when_any_key_released with a non-callable should raise ValueError."""
    with pytest.raises(ValueError):
        play.when_any_key_released("not a function")


def test_when_key_pressed_registers_callback():
    """play.when_key_pressed('a') should register a PRESSED_KEYS callback."""

    @play.when_key_pressed("a")
    def on_a(key):
        pass

    assert CallbackType.PRESSED_KEYS in callback_manager.callbacks


def test_when_key_released_registers_callback():
    """play.when_key_released('a') should register a RELEASED_KEYS callback."""

    @play.when_key_released("a")
    def on_a(key):
        pass

    assert CallbackType.RELEASED_KEYS in callback_manager.callbacks
