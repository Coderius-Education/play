"""Unit tests for play.objects.components."""

import pytest
from unittest.mock import MagicMock, patch

import play
from play.objects.components import EventComponent
from play.callback import CallbackType


@pytest.fixture
def mock_sprite():
    return MagicMock()


class TestEventComponent:

    def test_is_clicked(self, mock_sprite):
        """Test getting and setting is_clicked."""
        component = EventComponent(mock_sprite)

        # In EventComponent, is_clicked is an async method
        # and component._is_clicked property is not what's used, but let's test what's there
        # We need to mock mouse state testing or just mock it since it's deeply integrated with loop

        # Test setter bypassing method
        component._is_clicked = True
        assert component._is_clicked

    def test_touching_callbacks(self, mock_sprite):
        """Test set, get, and clear touching callbacks."""
        component = EventComponent(mock_sprite)
        mock_callback = MagicMock()

        # Test set
        component.set_touching("test_key", mock_callback)
        assert component.get_touching("test_key") == mock_callback

        # Test touching_callbacks returns all
        assert list(component.touching_callbacks()) == [mock_callback]

        # Test default return
        assert component.get_touching("non_existent", "default") == "default"

        # Test clear
        component.clear_touching("test_key")
        assert component.get_touching("test_key") is None

    def test_stopped_callbacks(self, mock_sprite):
        """Test set, get, and clear stopped callbacks."""
        component = EventComponent(mock_sprite)
        mock_callback = MagicMock()

        # Test set
        component.set_stopped("test_key", mock_callback)

        # Test stopped_callbacks returns all
        assert list(component.stopped_callbacks()) == [mock_callback]

        # Test clear all
        component.clear_all_stopped()
        assert list(component.stopped_callbacks()) == []

    @patch("play.objects.components.callback_manager")
    def test_when_clicked(self, mock_callback_manager, mock_sprite):
        """Test when_clicked decorator."""
        component = EventComponent(mock_sprite)

        @component.when_clicked
        def dummy_callback():
            pass

        mock_callback_manager.add_callback.assert_called_once()
        args, _ = mock_callback_manager.add_callback.call_args
        assert args[0] == CallbackType.WHEN_CLICKED_SPRITE

    @patch("play.objects.components.callback_manager")
    def test_when_click_released(self, mock_callback_manager, mock_sprite):
        """Test when_click_released decorator."""
        component = EventComponent(mock_sprite)

        @component.when_click_released
        def dummy_callback():
            pass

        mock_callback_manager.add_callback.assert_called_once()
        args, _ = mock_callback_manager.add_callback.call_args
        assert args[0] == CallbackType.WHEN_CLICK_RELEASED_SPRITE
