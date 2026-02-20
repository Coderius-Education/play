"""Tests for the extracted helper functions in sprites_loop."""

import asyncio
import math
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

import sys

sys.path.insert(0, ".")


def _make_sprite(x=0.0, y=0.0, angle=0.0, velocity=(0.0, 0.0)):
    """Create a mock sprite with a physics body."""
    sprite = MagicMock()
    body = MagicMock()
    body.position.x = x
    body.position.y = y
    body.angle = math.radians(angle)
    body.velocity = velocity
    sprite.physics._pymunk_body = body
    sprite._x = 0.0
    sprite._y = 0.0
    sprite.angle = 0.0
    sprite.physics._x_speed = 0.0
    sprite.physics._y_speed = 0.0
    return sprite


def _import_sprites_loop():
    from play.core.sprites_loop import (
        update_sprite_physics,
        run_sprite_callbacks,
        handle_sprite_click,
        handle_sprite_click_released,
        clear_click_tracking,
    )
    from play.core import sprites_loop

    return (
        sprites_loop,
        update_sprite_physics,
        run_sprite_callbacks,
        handle_sprite_click,
        handle_sprite_click_released,
        clear_click_tracking,
    )


class TestUpdateSpritePhysics:
    def test_syncs_position_from_body(self):
        _, update_sprite_physics, *_ = _import_sprites_loop()
        sprite = _make_sprite(x=10.0, y=20.0)
        update_sprite_physics(sprite)
        assert sprite._x == 10.0
        assert sprite._y == 20.0

    def test_syncs_angle_from_body(self):
        _, update_sprite_physics, *_ = _import_sprites_loop()
        sprite = _make_sprite(angle=45.0)
        update_sprite_physics(sprite)
        assert sprite.angle == pytest.approx(45.0)

    def test_syncs_velocity(self):
        _, update_sprite_physics, *_ = _import_sprites_loop()
        sprite = _make_sprite(velocity=(5.0, -3.0))
        update_sprite_physics(sprite)
        assert sprite.physics._x_speed == 5.0
        assert sprite.physics._y_speed == -3.0

    def test_ignores_nan_x(self):
        _, update_sprite_physics, *_ = _import_sprites_loop()
        sprite = _make_sprite(x=float("nan"), y=20.0)
        sprite._x = 99.0
        update_sprite_physics(sprite)
        assert sprite._x == 99.0  # unchanged
        assert sprite._y == 20.0

    def test_ignores_nan_y(self):
        _, update_sprite_physics, *_ = _import_sprites_loop()
        sprite = _make_sprite(x=10.0, y=float("nan"))
        sprite._y = 99.0
        update_sprite_physics(sprite)
        assert sprite._x == 10.0
        assert sprite._y == 99.0  # unchanged


class TestRunSpriteCallbacks:
    def test_runs_touching_and_stopped_callbacks(self):
        _, _, run_sprite_callbacks, *_ = _import_sprites_loop()
        sprite = MagicMock()
        touching_cb = MagicMock()
        stopped_cb = MagicMock()
        sprite._touching_callback = {"a": touching_cb}
        sprite._stopped_callback = {"b": stopped_cb}

        with patch(
            "play.core.sprites_loop.run_any_async_callback", new_callable=AsyncMock
        ) as mock_run:
            asyncio.run(run_sprite_callbacks(sprite))
            assert mock_run.call_count == 2
            mock_run.assert_any_call([touching_cb], [], [])
            mock_run.assert_any_call([stopped_cb], [], [])

    def test_clears_stopped_callbacks(self):
        _, _, run_sprite_callbacks, *_ = _import_sprites_loop()
        sprite = MagicMock()
        sprite._touching_callback = {}
        sprite._stopped_callback = {"b": MagicMock()}

        with patch(
            "play.core.sprites_loop.run_any_async_callback", new_callable=AsyncMock
        ):
            asyncio.run(run_sprite_callbacks(sprite))
            assert sprite._stopped_callback == {}


class TestHandleSpriteClick:
    def setup_method(self):
        sprites_loop, *_ = _import_sprites_loop()
        sprites_loop._clicked_sprite_id = None

    @patch("play.core.sprites_loop.callback_manager")
    @patch("play.core.sprites_loop.mouse_state")
    @patch("play.core.sprites_loop.mouse")
    def test_tracks_clicked_sprite(self, mock_mouse, mock_state, _mock_cb):
        sprites_loop, _, _, handle_sprite_click, *_ = _import_sprites_loop()
        sprite = MagicMock()
        sprite._is_clicked = False
        mock_mouse.is_touching.return_value = True
        mock_state.click_happened = True
        mock_mouse.is_clicked = True

        handle_sprite_click(sprite)

        assert sprites_loop._clicked_sprite_id == id(sprite)

    @patch("play.core.sprites_loop.callback_manager")
    @patch("play.core.sprites_loop.mouse_state")
    @patch("play.core.sprites_loop.mouse")
    def test_fires_when_clicked_callback(self, mock_mouse, mock_state, mock_cb):
        sprites_loop, _, _, handle_sprite_click, *_ = _import_sprites_loop()
        sprite = MagicMock()
        sprite._is_clicked = False
        mock_mouse.is_touching.return_value = True
        mock_state.click_happened = True
        mock_mouse.is_clicked = True

        handle_sprite_click(sprite)

        assert sprite._is_clicked is True
        mock_cb.run_callbacks.assert_called_once_with(
            sprites_loop.CallbackType.WHEN_CLICKED_SPRITE,
            callback_discriminator=id(sprite),
        )

    @patch("play.core.sprites_loop.callback_manager")
    @patch("play.core.sprites_loop.mouse_state")
    @patch("play.core.sprites_loop.mouse")
    def test_no_click_when_not_touching(self, mock_mouse, mock_state, mock_cb):
        _, _, _, handle_sprite_click, *_ = _import_sprites_loop()
        sprite = MagicMock()
        sprite._is_clicked = False
        mock_mouse.is_touching.return_value = False
        mock_state.click_happened = True
        mock_mouse.is_clicked = True

        handle_sprite_click(sprite)

        assert sprite._is_clicked is False
        mock_cb.run_callbacks.assert_not_called()

    @patch("play.core.sprites_loop.callback_manager")
    @patch("play.core.sprites_loop.mouse_state")
    @patch("play.core.sprites_loop.mouse")
    def test_no_click_when_no_click_happened(self, mock_mouse, mock_state, mock_cb):
        _, _, _, handle_sprite_click, *_ = _import_sprites_loop()
        sprite = MagicMock()
        sprite._is_clicked = False
        mock_mouse.is_touching.return_value = True
        mock_state.click_happened = False
        mock_mouse.is_clicked = True

        handle_sprite_click(sprite)

        assert sprite._is_clicked is False
        mock_cb.run_callbacks.assert_not_called()


class TestHandleSpriteClickReleased:
    def setup_method(self):
        sprites_loop, *_ = _import_sprites_loop()
        sprites_loop._clicked_sprite_id = None

    @patch("play.core.sprites_loop.callback_manager")
    @patch("play.core.sprites_loop.mouse_state")
    @patch("play.core.sprites_loop.mouse")
    def test_fires_release_on_same_sprite(self, mock_mouse, mock_state, mock_cb):
        sprites_loop, _, _, _, handle_sprite_click_released, _ = _import_sprites_loop()
        sprite = MagicMock()
        sprites_loop._clicked_sprite_id = id(sprite)
        mock_state.click_release_happened = True
        mock_mouse.is_touching.return_value = True

        handle_sprite_click_released(sprite)

        mock_cb.run_callbacks.assert_called_once_with(
            sprites_loop.CallbackType.WHEN_CLICK_RELEASED_SPRITE,
            callback_discriminator=id(sprite),
        )

    @patch("play.core.sprites_loop.callback_manager")
    @patch("play.core.sprites_loop.mouse_state")
    @patch("play.core.sprites_loop.mouse")
    def test_no_release_on_different_sprite(self, mock_mouse, mock_state, mock_cb):
        sprites_loop, _, _, _, handle_sprite_click_released, _ = _import_sprites_loop()
        sprite = MagicMock()
        other = MagicMock()
        sprites_loop._clicked_sprite_id = id(other)
        mock_state.click_release_happened = True
        mock_mouse.is_touching.return_value = True

        handle_sprite_click_released(sprite)

        mock_cb.run_callbacks.assert_not_called()

    @patch("play.core.sprites_loop.callback_manager")
    @patch("play.core.sprites_loop.mouse_state")
    @patch("play.core.sprites_loop.mouse")
    def test_no_release_when_not_touching(self, mock_mouse, mock_state, mock_cb):
        sprites_loop, _, _, _, handle_sprite_click_released, _ = _import_sprites_loop()
        sprite = MagicMock()
        sprites_loop._clicked_sprite_id = id(sprite)
        mock_state.click_release_happened = True
        mock_mouse.is_touching.return_value = False

        handle_sprite_click_released(sprite)

        mock_cb.run_callbacks.assert_not_called()

    @patch("play.core.sprites_loop.callback_manager")
    @patch("play.core.sprites_loop.mouse_state")
    @patch("play.core.sprites_loop.mouse")
    def test_no_release_when_no_release_happened(
        self, mock_mouse, mock_state, mock_cb
    ):
        sprites_loop, _, _, _, handle_sprite_click_released, _ = _import_sprites_loop()
        sprite = MagicMock()
        sprites_loop._clicked_sprite_id = id(sprite)
        mock_state.click_release_happened = False
        mock_mouse.is_touching.return_value = True

        handle_sprite_click_released(sprite)

        mock_cb.run_callbacks.assert_not_called()


class TestClearClickTracking:
    def test_clears_clicked_sprite_id(self):
        sprites_loop, _, _, _, _, clear_click_tracking = _import_sprites_loop()
        sprites_loop._clicked_sprite_id = 12345
        clear_click_tracking()
        assert sprites_loop._clicked_sprite_id is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
