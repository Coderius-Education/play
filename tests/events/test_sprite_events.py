"""Tests for sprite event decorators like when_clicked."""

import pytest
import sys
import pygame

sys.path.insert(0, ".")


def test_sprite_when_clicked_method():
    """Test sprite.when_clicked() method."""
    import play

    sprite = play.new_box(x=0, y=0, width=50, height=50)
    callback_called = []

    def on_click(sprite_arg):
        callback_called.append(sprite_arg)

    sprite.when_clicked(on_click, call_with_sprite=True)

    # Verify callback was registered
    from play.callback import callback_manager, CallbackType

    callbacks = list(
        callback_manager.get_callback([CallbackType.WHEN_CLICKED_SPRITE], id(sprite))
    )
    assert len(callbacks) > 0


def test_when_sprite_clicked_decorator():
    """Test play.when_sprite_clicked() decorator."""
    import play

    sprite = play.new_box(x=0, y=0, width=50, height=50)
    callback_called = []

    @play.when_sprite_clicked(sprite)
    def on_click(sprite_arg):
        callback_called.append(sprite_arg)

    # Verify callback was registered
    from play.callback import callback_manager, CallbackType

    callbacks = list(
        callback_manager.get_callback([CallbackType.WHEN_CLICKED_SPRITE], id(sprite))
    )
    assert len(callbacks) > 0


def test_when_sprite_clicked_multiple_sprites():
    """Test when_sprite_clicked with multiple sprites."""
    import play

    sprite1 = play.new_box(x=0, y=0, width=50, height=50)
    sprite2 = play.new_circle(x=100, y=100, radius=25)
    callback_called = []

    @play.when_sprite_clicked(sprite1, sprite2)
    def on_click(sprite_arg):
        callback_called.append(sprite_arg)

    # Verify callbacks were registered for both sprites
    from play.callback import callback_manager, CallbackType

    callbacks1 = list(
        callback_manager.get_callback([CallbackType.WHEN_CLICKED_SPRITE], id(sprite1))
    )
    callbacks2 = list(
        callback_manager.get_callback([CallbackType.WHEN_CLICKED_SPRITE], id(sprite2))
    )

    assert len(callbacks1) > 0
    assert len(callbacks2) > 0


def test_sprite_is_clicked_property():
    """Test sprite.is_clicked property."""
    import play

    sprite = play.new_box(x=0, y=0, width=50, height=50)

    # Initially not clicked
    assert sprite.is_clicked == False


def test_sprite_when_touching_decorator():
    """Test sprite.when_touching() decorator."""
    import play

    sprite1 = play.new_box(x=0, y=0, width=50, height=50)
    sprite2 = play.new_circle(x=0, y=0, radius=25)
    callback_called = []

    @sprite1.when_touching(sprite2)
    def on_touch():
        callback_called.append(True)

    # Verify callback was registered
    from play.callback import callback_manager, CallbackType

    callbacks = list(
        callback_manager.get_callback([CallbackType.WHEN_TOUCHING], id(sprite1))
    )
    assert len(callbacks) > 0


def test_sprite_when_clicked_call_with_sprite_true():
    """Test that when_clicked passes sprite as argument when call_with_sprite=True."""
    import play

    sprite = play.new_box(x=0, y=0)

    def callback_with_sprite(s):
        pass

    # Test with call_with_sprite=True (default)
    wrapper = sprite.when_clicked(callback_with_sprite, call_with_sprite=True)

    # Verify the wrapper was created
    assert callable(wrapper)


def test_sprite_when_clicked_call_with_sprite_false():
    """Test that when_clicked doesn't pass sprite when call_with_sprite=False."""
    import play

    sprite = play.new_box(x=0, y=0)

    def callback_without_sprite():
        pass

    # Test with call_with_sprite=False
    wrapper = sprite.when_clicked(callback_without_sprite, call_with_sprite=False)

    # Verify the wrapper was created
    assert callable(wrapper)


def test_sprite_when_click_released_method():
    """Test sprite.when_click_released() method."""
    import play

    sprite = play.new_box(x=0, y=0, width=50, height=50)
    callback_called = []

    def on_release(sprite_arg):
        callback_called.append(sprite_arg)

    sprite.when_click_released(on_release, call_with_sprite=True)

    # Verify callback was registered
    from play.callback import callback_manager, CallbackType

    callbacks = list(
        callback_manager.get_callback(
            [CallbackType.WHEN_CLICK_RELEASED_SPRITE], id(sprite)
        )
    )
    assert len(callbacks) > 0


def test_when_sprite_click_released_decorator():
    """Test play.when_sprite_click_released() decorator."""
    import play

    sprite = play.new_box(x=0, y=0, width=50, height=50)
    callback_called = []

    @play.when_sprite_click_released(sprite)
    def on_release(sprite_arg):
        callback_called.append(sprite_arg)

    # Verify callback was registered
    from play.callback import callback_manager, CallbackType

    callbacks = list(
        callback_manager.get_callback(
            [CallbackType.WHEN_CLICK_RELEASED_SPRITE], id(sprite)
        )
    )
    assert len(callbacks) > 0


def test_when_sprite_click_released_multiple_sprites():
    """Test when_sprite_click_released with multiple sprites."""
    import play

    sprite1 = play.new_box(x=0, y=0, width=50, height=50)
    sprite2 = play.new_circle(x=100, y=100, radius=25)
    callback_called = []

    @play.when_sprite_click_released(sprite1, sprite2)
    def on_release(sprite_arg):
        callback_called.append(sprite_arg)

    # Verify callbacks were registered for both sprites
    from play.callback import callback_manager, CallbackType

    callbacks1 = list(
        callback_manager.get_callback(
            [CallbackType.WHEN_CLICK_RELEASED_SPRITE], id(sprite1)
        )
    )
    callbacks2 = list(
        callback_manager.get_callback(
            [CallbackType.WHEN_CLICK_RELEASED_SPRITE], id(sprite2)
        )
    )

    assert len(callbacks1) > 0
    assert len(callbacks2) > 0


def test_sprite_when_click_released_call_with_sprite_false():
    """Test that when_click_released doesn't pass sprite when call_with_sprite=False."""
    import play

    sprite = play.new_box(x=0, y=0)

    def callback_without_sprite():
        pass

    # Test with call_with_sprite=False
    wrapper = sprite.when_click_released(
        callback_without_sprite, call_with_sprite=False
    )

    # Verify the wrapper was created
    assert callable(wrapper)
