"""Unit tests for play.api.events functions."""

import pytest
from unittest.mock import patch, MagicMock

import play
from play.api.events import (
    when_program_starts,
    repeat_forever,
    when_sprite_clicked,
    when_sprite_click_released,
    when_any_key_pressed,
    when_key_pressed,
    when_any_key_released,
    when_key_released,
    when_mouse_clicked,
    when_click_released,
)
from play.callback import callback_manager, CallbackType


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_when_program_starts():
    """Test that when_program_starts registers a callback."""

    @when_program_starts
    def dummy_func():
        pass

    assert CallbackType.WHEN_PROGRAM_START in callback_manager.callbacks
    assert len(callback_manager.callbacks[CallbackType.WHEN_PROGRAM_START]) == 1


def test_repeat_forever():
    """Test that repeat_forever registers a callback and sets is_running properly."""
    # The clean_play_state fixture pre-registers a safety-stop callback, so count
    # the existing entries before registering ours.
    before = len(callback_manager.callbacks.get(CallbackType.REPEAT_FOREVER, []))

    @repeat_forever
    def dummy_func():
        pass

    assert CallbackType.REPEAT_FOREVER in callback_manager.callbacks
    assert len(callback_manager.callbacks[CallbackType.REPEAT_FOREVER]) == before + 1

    # Check that our wrapper has the is_running attribute initialized to False
    wrapper = callback_manager.callbacks[CallbackType.REPEAT_FOREVER][-1]
    assert hasattr(wrapper, "is_running")
    assert wrapper.is_running is False


def test_when_sprite_clicked():
    """Test when_sprite_clicked decorator."""
    mock_sprite = MagicMock()

    @when_sprite_clicked(mock_sprite)
    def dummy_func(sprite):
        pass

    mock_sprite.when_clicked.assert_called_once_with(dummy_func, call_with_sprite=True)


def test_when_sprite_click_released():
    """Test when_sprite_click_released decorator."""
    mock_sprite = MagicMock()

    @when_sprite_click_released(mock_sprite)
    def dummy_func(sprite):
        pass

    mock_sprite.when_click_released.assert_called_once_with(
        dummy_func, call_with_sprite=True
    )


@patch("play.api.events._when_any_key")
def test_when_any_key_pressed(mock_when_any_key):
    """Test when_any_key_pressed delegates to _when_any_key correctly."""

    def dummy_func(key):
        pass

    result = when_any_key_pressed(dummy_func)

    mock_when_any_key.assert_called_once_with(dummy_func, released=False)
    assert result == mock_when_any_key.return_value


def test_when_any_key_pressed_invalid():
    """Test when_any_key_pressed raises ValueError on invalid input."""
    with pytest.raises(ValueError, match="doesn't use a list of keys"):
        # Passing a string instead of a callable (common mistake users make)
        when_any_key_pressed("a")


@patch("play.api.events._when_key")
def test_when_key_pressed(mock_when_key):
    """Test when_key_pressed delegates to _when_key correctly."""

    @when_key_pressed("a", "b")
    def dummy_func(key):
        pass

    mock_when_key.assert_called_once_with("a", "b", released=False)


@patch("play.api.events._when_any_key")
def test_when_any_key_released(mock_when_any_key):
    """Test when_any_key_released delegates to _when_any_key correctly."""

    def dummy_func(key):
        pass

    result = when_any_key_released(dummy_func)

    mock_when_any_key.assert_called_once_with(dummy_func, released=True)
    assert result == mock_when_any_key.return_value


def test_when_any_key_released_invalid():
    """Test when_any_key_released raises ValueError on invalid input."""
    with pytest.raises(ValueError, match="doesn't use a list of keys"):
        when_any_key_released("a")


@patch("play.api.events._when_key")
def test_when_key_released(mock_when_key):
    """Test when_key_released delegates to _when_key correctly."""

    @when_key_released("a", "b")
    def dummy_func(key):
        pass

    mock_when_key.assert_called_once_with("a", "b", released=True)


@patch("play.api.events.mouse")
def test_when_mouse_clicked(mock_mouse):
    """Test when_mouse_clicked delegates to mouse.when_clicked."""

    def dummy_func():
        pass

    result = when_mouse_clicked(dummy_func)

    mock_mouse.when_clicked.assert_called_once_with(dummy_func)
    assert result == mock_mouse.when_clicked.return_value


@patch("play.api.events.mouse")
def test_when_click_released(mock_mouse):
    """Test when_click_released delegates to mouse.when_click_released."""

    def dummy_func():
        pass

    result = when_click_released(dummy_func)

    mock_mouse.when_click_released.assert_called_once_with(dummy_func)
    assert result == mock_mouse.when_click_released.return_value
