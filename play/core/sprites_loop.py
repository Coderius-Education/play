"""This module contains the main loop for updating sprites and running their events."""

import math as _math

from .mouse_loop import mouse_state
from ..callback import callback_manager, CallbackType
from ..callback.callback_helpers import run_any_async_callback
from ..globals import globals_list
from ..io.mouse import mouse

# Track which sprite was clicked for when_click_released events
_clicked_sprite_id = None  # pylint: disable=invalid-name


async def update_sprites(do_events: bool = True):  # pylint: disable=too-many-branches
    """Update all sprites in the game loop.
    :param do_events: If True, run events for sprites. If False, only update positions.
    """
    global _clicked_sprite_id

    globals_list.sprites_group.update()

    for sprite in globals_list.sprites_group.sprites():
        ######################################################
        # update sprites with results of physics simulation
        ######################################################
        if sprite.physics and sprite.physics.can_move:
            body = sprite.physics._pymunk_body
            angle = _math.degrees(body.angle)
            if not _math.isnan(
                body.position.x
            ):  # this condition can happen when changing sprite.physics.can_move
                sprite._x = body.position.x
            if not _math.isnan(body.position.y):
                sprite._y = body.position.y

            sprite.angle = angle
            sprite.physics._x_speed, sprite.physics._y_speed = body.velocity

        sprite._is_clicked = False
        if sprite.is_hidden:
            continue

        if not do_events and not sprite.physics:
            continue

        #################################
        # All @sprite.when_touching events
        #################################
        await run_any_async_callback(list(sprite._touching_callback.values()), [], [])

        await run_any_async_callback(list(sprite._stopped_callback.values()), [], [])
        sprite._stopped_callback = {}

        #################################
        # Track sprite clicks for when_click_released
        #################################
        if do_events and mouse.is_touching(sprite) and mouse_state.click_happened:
            # Track which sprite was clicked for when_click_released
            _clicked_sprite_id = id(sprite)

        #################################
        # @sprite.when_clicked events
        #################################
        if (
            do_events
            and mouse.is_clicked
            and mouse.is_touching(sprite)
            and mouse_state.click_happened
        ):
            sprite._is_clicked = True
            callback_manager.run_callbacks(
                CallbackType.WHEN_CLICKED_SPRITE, callback_discriminator=id(sprite)
            )

        #######################################
        # @sprite.when_click_released events
        #######################################
        if (
            do_events
            and mouse_state.click_release_happened
            and mouse.is_touching(sprite)
            and _clicked_sprite_id == id(sprite)
        ):
            callback_manager.run_callbacks(
                CallbackType.WHEN_CLICK_RELEASED_SPRITE,
                callback_discriminator=id(sprite),
            )

    # Clear the clicked sprite tracking after any release event
    # Only clear when we're processing events (do_events=True), not in physics loop
    if do_events and mouse_state.click_release_happened:
        _clicked_sprite_id = None

    globals_list.sprites_group.update()
    globals_list.sprites_group.draw(globals_list.display)
