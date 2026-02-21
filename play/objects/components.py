"""Components for the component-based Sprite design."""

import pygame
import pymunk

from ..callback import callback_manager, CallbackType
from ..callback.collision_callbacks import collision_registry, CollisionType, WallSide
from ..globals import globals_list
from ..utils.async_helpers import make_async
from ..callback.callback_helpers import run_async_callback

class EventComponent:
    """Manages event callbacks and collision detection checks for a sprite."""
    
    def __init__(self, sprite):
        self._sprite = sprite
        self._touching_callback = {}
        self._stopped_callback = {}
        self._dependent_sprites = []
        self._is_clicked = False
        
    @property
    def is_clicked(self):
        return self._is_clicked
        
    def when_clicked(self, callback, call_with_sprite=False):
        async_callback = make_async(callback)

        async def wrapper():
            wrapper.is_running = True
            if call_with_sprite:
                await run_async_callback(async_callback, ["sprite"], [], self._sprite)
            else:
                await run_async_callback(async_callback, [], [])
            wrapper.is_running = False

        wrapper.is_running = False
        callback_manager.add_callback(
            CallbackType.WHEN_CLICKED_SPRITE, wrapper, id(self._sprite)
        )
        return wrapper

    def when_click_released(self, callback, call_with_sprite=False):
        async_callback = make_async(callback)

        async def wrapper():
            wrapper.is_running = True
            if call_with_sprite:
                await run_async_callback(async_callback, ["sprite"], [], self._sprite)
            else:
                await run_async_callback(async_callback, [], [])
            wrapper.is_running = False

        wrapper.is_running = False
        callback_manager.add_callback(
            CallbackType.WHEN_CLICK_RELEASED_SPRITE, wrapper, id(self._sprite)
        )
        return wrapper

    def when_touching(self, *sprites_to_check):
        def decorator(func):
            async_callback = make_async(func)

            for target in sprites_to_check:
                collision_registry.register(
                    self._sprite,
                    target,
                    self._sprite.physics._pymunk_shape,
                    target.physics._pymunk_shape,
                    async_callback,
                    CollisionType.SPRITE,
                )

            async def wrapper():
                await run_async_callback(async_callback, [], [])

            for target in sprites_to_check:
                target.events._dependent_sprites.append(self._sprite)
                callback_manager.add_callback(
                    CallbackType.WHEN_TOUCHING, (wrapper, target), id(self._sprite)
                )
            return wrapper
        return decorator

    def when_stopped_touching(self, *sprites_to_check):
        def decorator(func):
            async_callback = make_async(func)

            for target in sprites_to_check:
                collision_registry.register(
                    self._sprite,
                    target,
                    self._sprite.physics._pymunk_shape,
                    target.physics._pymunk_shape,
                    async_callback,
                    CollisionType.SPRITE,
                    begin=False,
                )

            async def wrapper():
                await run_async_callback(async_callback, [], [])

            for target in sprites_to_check:
                target.events._dependent_sprites.append(self._sprite)
                callback_manager.add_callback(
                    CallbackType.WHEN_STOPPED_TOUCHING, (wrapper, target), id(self._sprite)
                )
            return wrapper
        return decorator

    def when_touching_wall(self, callback=None, *, wall=None):
        def decorator(func):
            async_callback = make_async(func)

            if wall is None:
                walls_to_register = globals_list.walls
            elif isinstance(wall, WallSide):
                walls_to_register = [w for w in globals_list.walls if w.wall_side == wall]
            else:
                walls_to_register = [w for w in globals_list.walls if w.wall_side in wall]

            for wall_segment in walls_to_register:
                wall_side = wall_segment.wall_side

                def make_wrapper(ws):
                    async def wrapper():
                        await run_async_callback(async_callback, [], ["wall"], ws)
                    return wrapper

                wrapper = make_wrapper(wall_side)

                collision_registry.register(
                    self._sprite,
                    None,
                    self._sprite.physics._pymunk_shape,
                    wall_segment,
                    wrapper,
                    CollisionType.WALL,
                )

                wrapper.wall_filter = wall
                callback_manager.add_callback(
                    CallbackType.WHEN_TOUCHING_WALL, (wrapper, wall_side), id(self._sprite)
                )
            return func

        if callback is not None:
            return decorator(callback)
        return decorator

    def when_stopped_touching_wall(self, callback=None, *, wall=None):
        def decorator(func):
            async_callback = make_async(func)

            if wall is None:
                walls_to_register = globals_list.walls
            elif isinstance(wall, WallSide):
                walls_to_register = [w for w in globals_list.walls if w.wall_side == wall]
            else:
                walls_to_register = [w for w in globals_list.walls if w.wall_side in wall]

            for wall_segment in walls_to_register:
                wall_side = wall_segment.wall_side

                def make_wrapper(ws):
                    async def wrapper():
                        await run_async_callback(async_callback, [], ["wall"], ws)
                    return wrapper

                wrapper = make_wrapper(wall_side)

                collision_registry.register(
                    self._sprite,
                    None,
                    self._sprite.physics._pymunk_shape,
                    wall_segment,
                    wrapper,
                    CollisionType.WALL,
                    begin=False,
                )

                wrapper.wall_filter = wall
                callback_manager.add_callback(
                    CallbackType.WHEN_STOPPED_TOUCHING_WALL, (wrapper, wall_side), id(self._sprite)
                )
            return func

        if callback is not None:
            return decorator(callback)
        return decorator

    def update_collisions(self):
        """Update sprite and wall collisions manually."""
        sprite = self._sprite
        # Sprite Collisions
        for callback, shape_b in callback_manager.get_callback(
            [CallbackType.WHEN_TOUCHING, CallbackType.WHEN_STOPPED_TOUCHING], id(sprite)
        ):
            if sprite.physics and shape_b.physics:
                continue

            if sprite.is_hidden or shape_b.is_hidden:
                continue

            collision_key = id(shape_b)

            if sprite.is_touching(shape_b):
                if collision_key not in self._touching_callback:
                    if callback.type == CallbackType.WHEN_TOUCHING:
                        self._touching_callback[collision_key] = callback
                    else:
                        self._touching_callback[collision_key] = True
                continue
            if collision_key in self._touching_callback:
                del self._touching_callback[collision_key]
                if callback.type == CallbackType.WHEN_STOPPED_TOUCHING:
                    self._stopped_callback[collision_key] = callback

        # Wall Collisions
        touching_walls = sprite.get_touching_walls()

        for callback_data in callback_manager.get_callback(
            [CallbackType.WHEN_TOUCHING_WALL, CallbackType.WHEN_STOPPED_TOUCHING_WALL], id(sprite)
        ):
            callback, wall_side = callback_data
            collision_key = (CollisionType.WALL, wall_side)

            if wall_side in touching_walls:
                if collision_key not in self._touching_callback:
                    if callback.type == CallbackType.WHEN_TOUCHING_WALL:
                        self._touching_callback[collision_key] = callback
                    else:
                        self._touching_callback[collision_key] = True
                continue
            if collision_key in self._touching_callback:
                del self._touching_callback[collision_key]
                if callback.type == CallbackType.WHEN_STOPPED_TOUCHING_WALL:
                    self._stopped_callback[collision_key] = callback
