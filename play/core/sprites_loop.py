"""This module contains the main loop for updating sprites and running their events."""

import math as _math

from .mouse_loop import mouse_state
from ..callback import callback_manager, CallbackType
from ..callback.callback_helpers import run_any_async_callback
from ..globals import globals_list
from ..io.mouse import mouse


async def update_sprites(do_events: bool = True):  # pylint: disable=too-many-branches
    """Update all sprites in the game loop.
    :param do_events: If True, run events for sprites. If False, only update positions.
    """
    globals_list.sprites_group.update()

    for sprite in globals_list.sprites_group.sprites():
        ######################################################
        # update sprites with results of physics simulation
        ######################################################
        if sprite.physics and sprite.physics.can_move:
            body = sprite.physics._pymunk_body
            angle = _math.degrees(body.angle)
            if (
                str(body.position.x) != "nan"
            ):  # this condition can happen when changing sprite.physics.can_move
                sprite._x = body.position.x
            if str(body.position.y) != "nan":
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
        # @sprite.when_clicked events
        #################################
        if (
            mouse.is_clicked
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
        if mouse_state.click_release_happened and mouse.is_touching(sprite):
            callback_manager.run_callbacks(
                CallbackType.WHEN_CLICK_RELEASED_SPRITE,
                callback_discriminator=id(sprite),
            )

    globals_list.sprites_group.update()
    globals_list.sprites_group.draw(globals_list.display)
