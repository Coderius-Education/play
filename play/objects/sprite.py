"""This module contains the base sprite class for all objects in the game."""

import math as _math
import warnings as _warnings

import pygame
import pymunk as _pymunk

from ..callback import callback_manager, CallbackType
from ..callback.callback_helpers import run_async_callback
from ..callback.collision_callbacks import collision_registry, CollisionType, WallSide
from ..globals import globals_list
from ..io.screen import screen
from ..physics import physics_space, Physics as _Physics
from ..utils import clamp as _clamp, is_called_from_pygame
from ..utils.async_helpers import make_async


def point_touching_sprite(point, sprite):
    """Check if a point is touching a sprite using pymunk collision detection.
    :param point: The point (x, y tuple) to check if it's touching the sprite.
    :param sprite: The sprite to check if it's touching the point.
    :return: Whether the point is touching the sprite."""
    point_info = sprite.physics._pymunk_shape.point_query(point)
    return point_info.distance <= 0


_should_ignore_update = [
    "_should_recompute",
    "rect",
    "_image",
]


class Sprite(
    pygame.sprite.Sprite
):  # pylint: disable=attribute-defined-outside-init, too-many-public-methods
    def __init__(self, image=None):
        self._size = None
        self._x = None
        self._y = None
        self._angle = None
        self._transparency = None

        self._dependent_sprites = []
        self._touching_callback = {}
        self._stopped_callback = {}

        self._image = image
        self.physics = None
        self._is_clicked = False
        self._is_hidden = False
        self._should_recompute = True

        self.rect = None

        super().__init__()
        globals_list.sprites_group.add(self)

    def __setattr__(self, name, value):
        # ignore if it's in the ignored list or if the variable doesn't change
        if name not in _should_ignore_update and getattr(self, name, value) != value:
            self._should_recompute = True
            for sprite in self._dependent_sprites:
                sprite._should_recompute = True
        super().__setattr__(name, value)

    def is_touching_wall(self) -> bool:
        """Check if the sprite is touching the edge of the screen.
        :return: Whether the sprite is touching the edge of the screen."""
        return len(self.get_touching_walls()) > 0

    def get_touching_walls(self) -> list:
        """Get a list of WallSide values for walls the sprite is currently touching.
        :return: A list of WallSide enum values."""
        touching = []
        for wall in globals_list.walls:
            try:
                contact_set = self.physics._pymunk_shape.shapes_collide(wall)
                if contact_set and len(contact_set.points) > 0:
                    touching.append(wall.wall_side)
            except (AssertionError, AttributeError):
                continue
        return touching

    def update(self):  # pylint: disable=too-many-branches
        """Update the sprite."""
        if not self._should_recompute:
            return

        # Check if we are touching any other sprites
        for callback, shape_b in callback_manager.get_callback(
            [CallbackType.WHEN_TOUCHING, CallbackType.WHEN_STOPPED_TOUCHING],
            id(self),
        ):
            # Pymunk collision registry handles physics-enabled sprite collisions
            # This manual check is only a backup
            if self.physics and shape_b.physics:
                continue

            if self.is_hidden or shape_b.is_hidden:
                continue

            collision_key = id(shape_b)

            if self.is_touching(shape_b):
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

        # Get which walls are currently being touched
        touching_walls = self.get_touching_walls()

        for callback_data in callback_manager.get_callback(
            [CallbackType.WHEN_TOUCHING_WALL, CallbackType.WHEN_STOPPED_TOUCHING_WALL],
            id(self),
        ):
            # callback_data is now a tuple (wrapper, wall_side)
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

        if self._is_hidden:
            self._image = pygame.Surface((0, 0), pygame.SRCALPHA)
        self._should_recompute = False

    @property
    def is_clicked(self):
        """Get whether the sprite is clicked.
        :return: Whether the sprite is clicked."""
        return self._is_clicked

    @property
    def x(self):
        """Get the x-coordinate of the sprite.
        :return: The x-coordinate of the sprite."""
        return self._x

    @x.setter
    def x(self, _x):
        """Set the x-coordinate of the sprite.
        :param _x: The x-coordinate of the sprite."""
        self._x = _x
        self.physics._pymunk_body.position = self._x, self._y
        if self.physics._pymunk_body.body_type == _pymunk.Body.STATIC:
            physics_space.reindex_static()

    @property
    def y(self):
        """Get the y-coordinate of the sprite.
        :return: The y-coordinate of the sprite."""
        return self._y

    @y.setter
    def y(self, _y):
        """Set the y-coordinate of the sprite.
        :param _y: The y-coordinate of the sprite."""
        self._y = _y
        self.physics._pymunk_body.position = self._x, self._y
        if self.physics._pymunk_body.body_type == _pymunk.Body.STATIC:
            physics_space.reindex_static()

    @property
    def transparency(self):
        """Get the transparency of the sprite.
        :return: The transparency of the sprite."""
        return self._transparency

    @transparency.setter
    def transparency(self, alpha):
        """Set the transparency of the sprite.
        :param alpha: The transparency of the sprite."""
        if not isinstance(alpha, float) and not isinstance(alpha, int):
            raise ValueError(
                f"""Looks like you're trying to set {self}'s transparency to '{alpha}', which isn't a number.
Try looking in your code for where you're setting transparency for {self} and change it a number.
"""
            )
        if alpha > 100 or alpha < 0:
            _warnings.warn(
                f"""The transparency setting for {self} is being set to {alpha} and it should be between 0 and 100.
You might want to look in your code where you're setting transparency and make sure it's between 0 and 100.  """,
                Warning,
            )

        self._transparency = _clamp(alpha, 0, 100)

    @property
    def image(self):
        """Get the image of the sprite.
        :return: The image of the sprite."""
        return self._image

    @image.setter
    def image(self, image_filename):
        """Set the image of the sprite.
        :param image_filename: The filename of the image to set."""
        self._image = image_filename

    @property
    def angle(self):
        """Get the angle of the sprite.
        :return: The angle of the sprite."""
        return self._angle

    @angle.setter
    def angle(self, _angle):
        """Set the angle of the sprite.
        :param _angle: The angle of the sprite."""
        self._angle = _angle
        self.physics._pymunk_body.angle = _math.radians(_angle)

    @property
    def size(self):
        """Get the size of the sprite.
        :return: The size of the sprite."""
        return self._size

    @size.setter
    def size(self, percent):
        """Set the size of the sprite.
        :param percent: The size of the sprite as a percentage."""
        self._should_recompute = True
        self._size = percent
        self.physics._remove()
        self.physics._make_pymunk()

    def hide(self):
        """Hide the sprite."""
        if self._is_hidden:
            return
        self._is_hidden = True
        self.physics.pause()

    def show(self):
        """Show the sprite."""
        if not self._is_hidden:
            return
        self._is_hidden = False
        self.physics.unpause()

    @property
    def is_hidden(self):
        """Get whether the sprite is hidden.
        :return: Whether the sprite is hidden."""
        return self._is_hidden

    @is_hidden.setter
    def is_hidden(self, hide):
        """Set whether the sprite is hidden.
        :param hide: Whether the sprite is hidden."""
        if hide:
            self.hide()
        else:
            self.show()

    @property
    def is_shown(self):
        """Get whether the sprite is shown.
        :return: Whether the sprite is shown."""
        return not self._is_hidden

    @is_shown.setter
    def is_shown(self, show):
        """Set whether the sprite is shown.
        :param show: Whether the sprite is shown."""
        if show:
            self.show()
        else:
            self.hide()

    def is_touching(self, sprite_or_point):
        """Check if the sprite is touching another sprite or a point.
        :param sprite_or_point: The sprite or point to check if it's touching.
        :return: Whether the sprite is touching the other sprite or point."""
        if isinstance(sprite_or_point, Sprite):
            try:
                contact_set = self.physics._pymunk_shape.shapes_collide(
                    sprite_or_point.physics._pymunk_shape
                )
                return len(contact_set.points) > 0
            except (AssertionError, AttributeError):
                # Fallback: shapes might not be in a valid state for collision check
                return False
        # For point collision, use pymunk's point_query
        point_info = self.physics._pymunk_shape.point_query(sprite_or_point)
        return point_info.distance <= 0

    def distance_to(self, x, y=None):
        """Calculate the distance to a point or sprite.
        :param x: The x-coordinate of the point.
        :param y: The y-coordinate of the point.
        :return: The distance to the point or sprite."""
        assert not x is None

        try:
            # x can either be a number or a sprite. If it's a sprite:
            x1 = x.x
            y1 = x.y
        except AttributeError:
            x1 = x
            y1 = y

        dx = self.x - x1
        dy = self.y - y1

        return _math.sqrt(dx**2 + dy**2)

    def info(self):
        """Print a short summary of this sprite."""
        sprite_type = self.__class__.__name__
        color = getattr(self, "_color", "unknown")

        # Get size info based on sprite type
        if sprite_type == "Circle":
            size_info = f"radius={getattr(self, 'radius', 0)}"
        elif hasattr(self, "width") and hasattr(self, "height"):
            size_info = f"width={self.width}, height={self.height}"
        else:
            size_info = ""

        hidden = " (hidden)" if self._is_hidden else ""

        print(f"Hi, I'm a {sprite_type}!")
        print(f"  Color: {color}")
        print(f"  Position: x={self.x}, y={self.y}")
        if size_info:
            print(f"  Size: {size_info}")
        print(f"  Angle: {self.angle}°{hidden}")

    def physics_info(self):
        """Print a summary of this sprite's physics properties."""
        if not self.physics:
            print("This sprite has no physics enabled.")
            return

        body_type = self.physics._pymunk_body.body_type

        # Dutch names for body types
        type_names = {
            _pymunk.Body.DYNAMIC: ("DYNAMIC", "VRIJ"),
            _pymunk.Body.KINEMATIC: ("KINEMATIC", "GESTUURD"),
            _pymunk.Body.STATIC: ("STATIC", "VAST"),
        }
        eng_name, nl_name = type_names.get(body_type, ("UNKNOWN", "ONBEKEND"))

        print(f"Physics: {eng_name} ({nl_name})")
        print(
            f"can_move={self.physics.can_move},stable={self.physics.stable},obeys_gravity={self.physics.obeys_gravity}"
        )
        print(f"  Speed: x={self.physics.x_speed}, y={self.physics.y_speed}")
        print(f"  Mass: {self.physics.mass}, Bounciness: {self.physics.bounciness}")

        # Collision info
        print("\nCollision behavior:")
        if body_type == _pymunk.Body.DYNAMIC:
            print("  ✓ Collides with DYNAMIC (VRIJ)")
            print("  ✓ Collides with KINEMATIC (GESTUURD)")
            print("  ✓ Collides with STATIC (VAST)")
        elif body_type == _pymunk.Body.KINEMATIC:
            print("  ✓ Collides with DYNAMIC (VRIJ)")
            print("  ✗ Passes through KINEMATIC (GESTUURD)")
            print("  ✗ Passes through STATIC (VAST)")
        else:  # STATIC
            print("  ✓ Collides with DYNAMIC (VRIJ)")
            print("  ✗ Passes through KINEMATIC (GESTUURD)")
            print("  ✗ Passes through STATIC (VAST)")

    def remove(self):
        """Remove the sprite from the screen."""
        if not self.alive():
            return
        self.physics._remove()
        globals_list.sprites_group.remove(self)

    def add(self, *groups):
        """Add the sprite to groups (pygame internal method).
        Warning: This is a pygame internal method. Use at your own risk."""
        if not is_called_from_pygame():
            _warnings.warn(
                "The 'add' method is a pygame internal method and should not be called directly. "
                "Sprites are automatically added to the sprite group when created.",
                UserWarning,
                stacklevel=2,
            )
        super().add(*groups)

    def add_internal(self, group):
        """Add the sprite to a group internally (pygame internal method).
        Warning: This is a pygame internal method. Use at your own risk."""
        if not is_called_from_pygame():
            _warnings.warn(
                "The 'add_internal' method is a pygame internal method and should not be called directly.",
                UserWarning,
                stacklevel=2,
            )
        super().add_internal(group)

    def remove_internal(self, group):
        """Remove the sprite from a group internally (pygame internal method).
        Warning: This is a pygame internal method. Use at your own risk."""
        if not is_called_from_pygame():
            _warnings.warn(
                "The 'remove_internal' method is a pygame internal method and should not be called directly. "
                "Use the 'remove' method instead.",
                UserWarning,
                stacklevel=2,
            )
        super().remove_internal(group)

    @property
    def width(self):
        """Get the width of the sprite.
        :return: The width of the sprite."""
        return self.rect.width

    @property
    def height(self):
        """Get the height of the sprite.
        :return: The height of the sprite."""
        return self.rect.height

    @property
    def right(self):
        """Get the right of the sprite.
        :return: The right of the sprite."""
        return self.x + self.width / 2

    @right.setter
    def right(self, x):
        """Set the right of the sprite to a x-coordinate.
        :param x: The x-coordinate to set the right of the sprite to."""
        self.x = x - self.width / 2

    @property
    def left(self):
        """Get the left of the sprite.
        :return: The left of the sprite."""
        return self.x - self.width / 2

    @left.setter
    def left(self, x):
        """Set the left of the sprite to a x-coordinate.
        :param x: The x-coordinate to set the left of the sprite to."""
        self.x = x + self.width / 2

    @property
    def top(self):
        """Get the top of the sprite.
        :return: The top of the sprite."""
        return self.y + self.height / 2

    @top.setter
    def top(self, y):
        """Set the top of the sprite to a y-coordinate.
        :param y: The y-coordinate to set the top of the sprite to."""
        self.y = y - self.height / 2

    @property
    def bottom(self):
        """Get the bottom of the sprite.
        :return: The bottom of the sprite."""
        return self.y - self.height / 2

    @bottom.setter
    def bottom(self, y):
        """Set the bottom of the sprite to a y-coordinate.
        :param y: The y-coordinate to set the bottom of the sprite to."""
        self.y = y + self.height / 2

    def _pygame_x(self):
        return self.x + (screen.width / 2.0) - (self.rect.width / 2.0)

    def _pygame_y(self):
        return (screen.height / 2.0) - self.y - (self.rect.height / 2.0)

    # @decorator
    def when_clicked(self, callback, call_with_sprite=False):
        """Run a function when the sprite is clicked.
        :param callback: The function to run.
        :param call_with_sprite: Whether to call the function with the sprite as an argument.
        """
        async_callback = make_async(callback)

        async def wrapper():
            wrapper.is_running = True
            if call_with_sprite:
                await run_async_callback(
                    async_callback,
                    ["sprite"],
                    [],
                    self,
                )
            else:
                await run_async_callback(
                    async_callback,
                    [],
                    [],
                )
            wrapper.is_running = False

        wrapper.is_running = False
        callback_manager.add_callback(
            CallbackType.WHEN_CLICKED_SPRITE, wrapper, id(self)
        )
        return wrapper

    # @decorator
    def when_click_released(self, callback, call_with_sprite=False):
        """Run a function when the sprite click is released.
        :param callback: The function to run.
        :param call_with_sprite: Whether to call the function with the sprite as an argument.
        """
        async_callback = make_async(callback)

        async def wrapper():
            wrapper.is_running = True
            if call_with_sprite:
                await run_async_callback(
                    async_callback,
                    ["sprite"],
                    [],
                    self,
                )
            else:
                await run_async_callback(
                    async_callback,
                    [],
                    [],
                )
            wrapper.is_running = False

        wrapper.is_running = False
        callback_manager.add_callback(
            CallbackType.WHEN_CLICK_RELEASED_SPRITE, wrapper, id(self)
        )
        return wrapper

    def when_touching(self, *sprites):
        """Run a function when the sprite is touching another sprite.
        :param sprites: The sprites to check if they're touching.
        BEWARE: This function will yield the game loop until the given function returns.
        """

        def decorator(func):
            async_callback = make_async(func)

            for sprite in sprites:
                collision_registry.register(
                    self,
                    sprite,
                    self.physics._pymunk_shape,
                    sprite.physics._pymunk_shape,
                    async_callback,
                    CollisionType.SPRITE,
                )

            async def wrapper():
                await run_async_callback(
                    async_callback,
                    [],
                    [],
                )

            for sprite in sprites:

                async def wrapper_func():
                    await wrapper()

                sprite._dependent_sprites.append(self)
                callback_manager.add_callback(
                    CallbackType.WHEN_TOUCHING, (wrapper_func, sprite), id(self)
                )
            return wrapper

        return decorator

    def when_stopped_touching(self, *sprites):
        """Run a function when the sprite is no longer touching another sprite.
        :param sprites: The sprites to check if they're touching.
        """

        def decorator(func):
            async_callback = make_async(func)

            for sprite in sprites:
                collision_registry.register(
                    self,
                    sprite,
                    self.physics._pymunk_shape,
                    sprite.physics._pymunk_shape,
                    async_callback,
                    CollisionType.SPRITE,
                    begin=False,
                )

            async def wrapper():
                await run_async_callback(
                    async_callback,
                    [],
                    [],
                )

            for sprite in sprites:

                async def wrapper_func():
                    await wrapper()

                sprite._dependent_sprites.append(self)
                callback_manager.add_callback(
                    CallbackType.WHEN_STOPPED_TOUCHING, (wrapper_func, sprite), id(self)
                )
            return wrapper

        return decorator

    def when_touching_wall(self, callback=None, *, wall=None):
        """Run a function when the sprite is touching the edge of the screen.
        :param callback: The function to run.
        :param wall: Optional WallSide or list of WallSides to filter which walls trigger the callback.
        BEWARE: This function will yield the game loop until the given function returns.
        """

        def decorator(func):
            async_callback = make_async(func)

            # Determine which walls to register for
            if wall is None:
                walls_to_register = globals_list.walls
            elif isinstance(wall, WallSide):
                walls_to_register = [
                    w for w in globals_list.walls if w.wall_side == wall
                ]
            else:
                # Assume it's a list of WallSides
                walls_to_register = [
                    w for w in globals_list.walls if w.wall_side in wall
                ]

            # Create per-wall wrappers that pass the wall_side to the callback
            for wall_segment in walls_to_register:
                wall_side = wall_segment.wall_side

                def make_wrapper(ws):
                    async def wrapper():
                        await run_async_callback(
                            async_callback,
                            [],
                            ["wall"],
                            ws,
                        )

                    return wrapper

                wrapper = make_wrapper(wall_side)

                collision_registry.register(
                    self,
                    None,
                    self.physics._pymunk_shape,
                    wall_segment,
                    wrapper,
                    CollisionType.WALL,
                )

                wrapper.wall_filter = wall
                callback_manager.add_callback(
                    CallbackType.WHEN_TOUCHING_WALL, (wrapper, wall_side), id(self)
                )
            return func

        # Handle both @sprite.when_touching_wall and @sprite.when_touching_wall(wall=...)
        if callback is not None:
            return decorator(callback)
        return decorator

    def when_stopped_touching_wall(self, callback=None, *, wall=None):
        """Run a function when the sprite is no longer touching the edge of the screen.
        :param callback: The function to run.
        :param wall: Optional WallSide or list of WallSides to filter which walls trigger the callback.
        """

        def decorator(func):
            async_callback = make_async(func)

            # Determine which walls to register for
            if wall is None:
                walls_to_register = globals_list.walls
            elif isinstance(wall, WallSide):
                walls_to_register = [
                    w for w in globals_list.walls if w.wall_side == wall
                ]
            else:
                # Assume it's a list of WallSides
                walls_to_register = [
                    w for w in globals_list.walls if w.wall_side in wall
                ]

            # Create per-wall wrappers that pass the wall_side to the callback
            for wall_segment in walls_to_register:
                wall_side = wall_segment.wall_side

                def make_wrapper(ws):
                    async def wrapper():
                        await run_async_callback(
                            async_callback,
                            [],
                            ["wall"],
                            ws,
                        )

                    return wrapper

                wrapper = make_wrapper(wall_side)

                collision_registry.register(
                    self,
                    None,
                    self.physics._pymunk_shape,
                    wall_segment,
                    wrapper,
                    CollisionType.WALL,
                    begin=False,
                )

                wrapper.wall_filter = wall
                callback_manager.add_callback(
                    CallbackType.WHEN_STOPPED_TOUCHING_WALL,
                    (wrapper, wall_side),
                    id(self),
                )
            return func

        # Handle both @sprite.when_stopped_touching_wall and @sprite.when_stopped_touching_wall(wall=...)
        if callback is not None:
            return decorator(callback)
        return decorator

    def _common_properties(self):
        # used with inheritance to clone
        return {
            "x": self.x,
            "y": self.y,
            "size": self.size,
            "transparency": self.transparency,
            "angle": self.angle,
        }

    def clone(self):
        """Clone the sprite.
        :return: The cloned sprite."""
        return self.__class__(image=self.image)

    def _check_no_collision_callbacks(self):
        """Raise RuntimeError if any collision callbacks reference this sprite."""
        callback_types = [
            CallbackType.WHEN_TOUCHING,
            CallbackType.WHEN_TOUCHING_WALL,
            CallbackType.WHEN_STOPPED_TOUCHING,
            CallbackType.WHEN_STOPPED_TOUCHING_WALL,
        ]
        registered = [
            ctype
            for ctype in callback_types
            if callback_manager.get_callback(ctype, id(self))
        ]
        if registered:
            names = ", ".join(ctype.name for ctype in registered)
            raise RuntimeError(
                f"{self!r} already has collision callbacks registered ({names}). "
                f"Call start_physics() before registering callbacks like "
                f"when_touching or when_touching_wall, not after."
            )

        sprite_callback_types = [
            CallbackType.WHEN_TOUCHING,
            CallbackType.WHEN_STOPPED_TOUCHING,
        ]
        for dependent in self._dependent_sprites:
            dep_id = id(dependent)
            for ctype in sprite_callback_types:
                callbacks = callback_manager.get_callback(ctype, dep_id) or []
                if any(s is self for _, s in callbacks):
                    raise RuntimeError(
                        f"Cannot call start_physics() on {self!r} because "
                        f"{dependent!r} has a {ctype.name} callback referencing it. "
                        f"Call start_physics() on all sprites before registering "
                        f"collision callbacks."
                    )

    def start_physics(
        self,
        can_move=True,
        stable=False,
        x_speed=0,
        y_speed=0,
        obeys_gravity=True,
        bounciness=1.0,
        mass=10,
        friction=0,
    ):
        """Start the physics simulation for this sprite.

        Must be called before registering any collision callbacks
        (when_touching, when_touching_wall, etc.). If callbacks have already
        been registered, call start_physics first and then register them.

        :param can_move: Whether the object can move.
        :param stable: Whether the object is stable.
        :param x_speed: The x-speed of the object.
        :param y_speed: The y-speed of the object.
        :param obeys_gravity: Whether the object obeys gravity.
        :param bounciness: The bounciness of the object.
        :param mass: The mass of the object.
        :param friction: The friction of the object.
        """
        self._check_no_collision_callbacks()

        # Remove existing physics if it exists
        if self.physics:
            self.physics._remove()

        self.physics = _Physics(
            self,
            can_move,
            stable,
            x_speed,
            y_speed,
            obeys_gravity,
            bounciness,
            mass,
            friction,
        )

    def stop_physics(self):
        """Resets the physics to the starting situation, removing all collision callbacks."""
        callback_types = [
            CallbackType.WHEN_TOUCHING,
            CallbackType.WHEN_TOUCHING_WALL,
            CallbackType.WHEN_STOPPED_TOUCHING,
            CallbackType.WHEN_STOPPED_TOUCHING_WALL,
        ]
        for ctype in callback_types:
            callback_manager.remove_callbacks(ctype, id(self))
        self.start_physics(stable=True, obeys_gravity=False)
