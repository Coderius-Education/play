"""This module contains the main loop for updating sprites and running their events."""

import math as _math

from .mouse_loop import mouse_state
from ..callback import callback_manager, CallbackType
from ..callback.callback_helpers import run_any_async_callback
from ..globals import globals_list
from ..io.mouse import mouse

# Track which sprite was clicked for when_click_released events
_clicked_sprite_id = None  # pylint: disable=invalid-name


def update_sprite_physics(sprite):
    """Update a sprite's position and angle from its physics body.

    Syncs the sprite's x, y, angle, and speed from the pymunk physics simulation.
    NaN values from the physics body are ignored to handle edge cases when
    changing sprite.physics.can_move.
    """
    body = sprite.physics._pymunk_body
    angle = _math.degrees(body.angle)
    if not _math.isnan(body.position.x):
        sprite._x = body.position.x
    if not _math.isnan(body.position.y):
        sprite._y = body.position.y

    if not _math.isnan(angle):
        sprite.angle = angle
    sprite.physics._x_speed, sprite.physics._y_speed = body.velocity


async def run_sprite_callbacks(sprite):
    """Run touching and stopped callbacks for a sprite."""
    if hasattr(sprite, 'events'):
        await run_any_async_callback(list(sprite.events._touching_callback.values()), [], [])
        await run_any_async_callback(list(sprite.events._stopped_callback.values()), [], [])
        sprite.events._stopped_callback = {}


def handle_sprite_click(sprite):
    """Handle click tracking and when_clicked events for a sprite.

    Tracks which sprite was clicked (for later click-release detection)
    and fires when_clicked callbacks.
    """
    global _clicked_sprite_id

    touching_and_clicked = mouse.is_touching(sprite) and mouse_state.click_happened
    if touching_and_clicked:
        _clicked_sprite_id = id(sprite)

    if mouse.is_clicked and touching_and_clicked:
        if hasattr(sprite, 'events'):
            sprite.events._is_clicked = True
        callback_manager.run_callbacks(
            CallbackType.WHEN_CLICKED_SPRITE, callback_discriminator=id(sprite)
        )


def handle_sprite_click_released(sprite):
    """Handle when_click_released events for a sprite.

    Fires when the mouse button is released while touching the same sprite
    that was originally clicked.
    """
    if (
        mouse_state.click_release_happened
        and mouse.is_touching(sprite)
        and _clicked_sprite_id == id(sprite)
    ):
        callback_manager.run_callbacks(
            CallbackType.WHEN_CLICK_RELEASED_SPRITE,
            callback_discriminator=id(sprite),
        )


def clear_click_tracking():
    """Clear the clicked sprite tracking after a release event."""
    global _clicked_sprite_id
    _clicked_sprite_id = None


async def update_sprites(do_events: bool = True):
    """Update all sprites in the game loop.
    :param do_events: If True, run events for sprites. If False, only update positions.
    """
    globals_list.sprites_group.update()

    for sprite in globals_list.sprites_group.sprites():
        if sprite.physics and sprite.physics.can_move:
            update_sprite_physics(sprite)

        if hasattr(sprite, 'events'):
            sprite.events._is_clicked = False
        if sprite.is_hidden:
            continue

        if not do_events and not sprite.physics:
            continue

        await run_sprite_callbacks(sprite)

        if do_events:
            handle_sprite_click(sprite)
            handle_sprite_click_released(sprite)

    if do_events and mouse_state.click_release_happened:
        clear_click_tracking()

    globals_list.sprites_group.update()
    globals_list.sprites_group.draw(globals_list.display)
