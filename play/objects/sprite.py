"""This module contains the base sprite class for all objects in the game."""

import math as _math
import warnings as _warnings

import pygame
import pymunk as _pymunk

from ..api.auto_start import _schedule_auto_start
from ..callback import callback_manager, CallbackType
from ..callback.collision_callbacks import collision_registry
from ..globals import globals_list
from ..io.screen import screen
from ..physics import physics_space, Physics as _Physics
from ..utils import clamp as _clamp, is_called_from_pygame
from .components import EventComponent


def point_touching_sprite(point, sprite):
    """Check if a point is touching a sprite using pymunk collision detection.
    :param point: The point (x, y tuple) to check if it's touching the sprite.
    :param sprite: The sprite to check if it's touching the point.
    :return: Whether the point is touching the sprite."""
    point_info = sprite.physics._pymunk_shape.point_query(point)
    return point_info.distance <= 0


_should_ignore_update = frozenset(
    {
        "_should_recompute",
        "rect",
        "_image",
    }
)


class Sprite(pygame.sprite.Sprite):  # pylint: disable=too-many-public-methods
    def __init__(self, image=None, x=0, y=0, anchor=None, layer=0):
        # Subclasses set their own field values BEFORE calling super().__init__() so
        # that start_physics() can use the correct dimensions.  The hasattr guards
        # provide fallback defaults when Sprite is instantiated directly.
        if not hasattr(self, "_size"):
            self._size = 100
        if not hasattr(self, "_angle"):
            self._angle = 0
        if not hasattr(self, "_transparency"):
            self._transparency = 100

        # Anchor/layer attrs bypass __setattr__ to avoid triggering _should_recompute.
        # Set unconditionally — subclass pre-sets (Text) are intentionally overwritten here;
        # Text passes the same values so the result is identical.
        object.__setattr__(self, "_layer", layer)
        object.__setattr__(self, "_anchor", anchor)
        object.__setattr__(self, "_anchor_ox", x)
        object.__setattr__(self, "_anchor_oy", y)

        # _x/_y: use anchor-aware defaults unless the subclass already set them
        # (Text sets these before calling super() because it calls update() first).
        if not hasattr(self, "_x"):
            self._x = 0 if anchor else x
        if not hasattr(self, "_y"):
            self._y = 0 if anchor else y

        if not hasattr(self, "events"):
            self.events = EventComponent(self)
        self.physics = None

        if getattr(self, "_image", None) is None:
            self._image = image
        if not hasattr(self, "_is_hidden"):
            self._is_hidden = False
        self._should_recompute = True

        if getattr(self, "rect", None) is None:
            self.rect = pygame.Rect(0, 0, 0, 0)

        # Pygame sprite initializes internal variables but clobbers rect and image, so we back it up
        _backup_rect = self.rect
        _backup_image = getattr(self, "_image", None)

        super().__init__()
        globals_list.sprites_group.add(self, layer=self._layer)

        self.rect = _backup_rect
        if _backup_image is not None:
            self._image = _backup_image

        self.start_physics(stable=True, obeys_gravity=False)

        _schedule_auto_start()

    def __setattr__(self, name, value):
        # ignore if it's in the ignored list or if the variable doesn't change
        if name not in _should_ignore_update and getattr(self, name, value) != value:
            self._should_recompute = True
            if hasattr(self, "events"):
                for sprite in self.events._dependent_sprites:
                    sprite._should_recompute = True
        super().__setattr__(name, value)

    @property
    def layer(self):
        """The render layer this sprite belongs to (higher = drawn on top)."""
        return self._layer

    @layer.setter
    def layer(self, value):
        """Move the sprite to a different render layer."""
        object.__setattr__(self, "_layer", value)
        globals_list.sprites_group.change_layer(self, value)

    def _apply_anchor(self):
        """Recompute x/y from the anchor + offsets and current screen dimensions.

        ox/oy are pixel distances from the anchored screen edge.  The sprite's
        relevant EDGE (not center) will land at that distance from the border.
        The half-dimensions come from the previous frame's rect, which is
        accurate from frame 2 onward; frame 1 uses w2=h2=0 (same as before).
        """
        ox, oy = self._anchor_ox, self._anchor_oy
        a = self._anchor
        w2 = self.rect.width / 2
        h2 = self.rect.height / 2
        if a == "top-left":
            nx, ny = screen.left + ox + w2, screen.top - oy - h2
        elif a == "top-center":
            nx, ny = ox, screen.top - oy - h2
        elif a == "top-right":
            nx, ny = screen.right - ox - w2, screen.top - oy - h2
        elif a == "center-left":
            nx, ny = screen.left + ox + w2, oy
        elif a == "center":
            nx, ny = ox, oy
        elif a == "center-right":
            nx, ny = screen.right - ox - w2, oy
        elif a == "bottom-left":
            nx, ny = screen.left + ox + w2, screen.bottom + oy + h2
        elif a == "bottom-center":
            nx, ny = ox, screen.bottom + oy + h2
        elif a == "bottom-right":
            nx, ny = screen.right - ox - w2, screen.bottom + oy + h2
        else:
            _warnings.warn(
                f"Unknown anchor value '{a}'. "
                "Valid values: 'top-left', 'top-center', 'top-right', "
                "'center-left', 'center', 'center-right', "
                "'bottom-left', 'bottom-center', 'bottom-right'.",
                UserWarning,
                stacklevel=2,
            )
            return
        if hasattr(self, "physics") and self.physics is not None:
            self.x, self.y = nx, ny
        else:
            self._x, self._y = nx, ny
            self._should_recompute = True

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

    def update(self):
        """Orchestrate per-frame rendering: apply anchor, call _render(), clear flag."""
        if self._anchor:
            self._apply_anchor()
        if not self._should_recompute:
            return
        if self._is_hidden:
            self._image = pygame.Surface((0, 0), pygame.SRCALPHA)
        else:
            self._render()
        self._should_recompute = False

    def _render(self):
        """Override in subclasses to draw the shape-specific image onto self.image."""

    @property
    def is_clicked(self):
        """Get whether the sprite is clicked.
        :return: Whether the sprite is clicked."""
        return self.events.is_clicked

    @property
    def x(self):
        """Get the x-coordinate of the sprite.
        :return: The x-coordinate of the sprite."""
        return self._x

    @x.setter
    def x(self, _x):
        """Set the x-coordinate of the sprite.
        :param _x: The x-coordinate of the sprite."""
        # Requires self.physics to be initialized; only safe after Sprite.__init__() completes.
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
        # Requires self.physics to be initialized; only safe after Sprite.__init__() completes.
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
                UserWarning,
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
        # Requires self.physics to be initialized; only safe after Sprite.__init__() completes.
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
        # Requires self.physics to be initialized; only safe after Sprite.__init__() completes.
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
        :param x: The x-coordinate of the point, or a sprite object.
        :param y: The y-coordinate of the point (required when x is a number).
        :return: The distance to the point or sprite."""
        assert x is not None

        try:
            # x can either be a number or a sprite. If it's a sprite:
            x1 = x.x
            y1 = x.y
        except AttributeError as exc:
            if y is None:
                raise ValueError(
                    "distance_to() requires a y argument when x is a number, "
                    "or pass a sprite object as x."
                ) from exc
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
        saved = self._save_and_clear_callbacks()
        # Wall callback types don't register in _dependent_sprites, so only
        # WHEN_TOUCHING / WHEN_STOPPED_TOUCHING need cleanup here.
        for cb_type in [CallbackType.WHEN_TOUCHING, CallbackType.WHEN_STOPPED_TOUCHING]:
            for item in saved.get(cb_type, []):
                if isinstance(item, tuple) and len(item) == 2:
                    _, target = item
                    if hasattr(target, "events"):
                        target.events._dependent_sprites.discard(self)
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
        return self.events.when_clicked(callback, call_with_sprite)

    # @decorator
    def when_click_released(self, callback, call_with_sprite=False):
        """Run a function when the sprite click is released.
        :param callback: The function to run.
        :param call_with_sprite: Whether to call the function with the sprite as an argument.
        """
        return self.events.when_click_released(callback, call_with_sprite)

    def when_touching(self, *sprites):
        """Run a function when the sprite is touching another sprite.
        :param sprites: The sprites to check if they're touching.
        BEWARE: This function will yield the game loop until the given function returns.
        """
        return self.events.when_touching(*sprites)

    def when_stopped_touching(self, *sprites):
        """Run a function when the sprite is no longer touching another sprite.
        :param sprites: The sprites to check if they're touching.
        """
        return self.events.when_stopped_touching(*sprites)

    def when_touching_wall(self, callback=None, *, wall=None):
        """Run a function when the sprite is touching the edge of the screen.
        :param callback: The function to run.
        :param wall: Optional WallSide or list of WallSides to filter which walls trigger the callback.
        BEWARE: This function will yield the game loop until the given function returns.
        """
        return self.events.when_touching_wall(callback, wall=wall)

    def when_stopped_touching_wall(self, callback=None, *, wall=None):
        """Run a function when the sprite is no longer touching the edge of the screen.
        :param callback: The function to run.
        :param wall: Optional WallSide or list of WallSides to filter which walls trigger the callback.
        """
        return self.events.when_stopped_touching_wall(callback, wall=wall)

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

    def _save_and_clear_callbacks(self):
        """Save all physics-related callbacks for a sprite and clear them.

        Returns a dict mapping each CallbackType to a list of saved callbacks.
        """
        sprite_id = id(self)
        callback_types = [
            CallbackType.WHEN_TOUCHING,
            CallbackType.WHEN_TOUCHING_WALL,
            CallbackType.WHEN_STOPPED_TOUCHING,
            CallbackType.WHEN_STOPPED_TOUCHING_WALL,
        ]
        saved_callbacks = {
            callback_type: list(
                callback_manager.get_callback(callback_type, sprite_id) or []
            )
            for callback_type in callback_types
        }
        for callback_type in callback_types:
            callback_manager.remove_callbacks(callback_type, sprite_id)
        return saved_callbacks

    @staticmethod
    def _cleanup_collision_registry(collision_type):
        """Remove all collision_registry entries for a given collision type.

        Cleans up both begin/separate callback dicts and the shape_registry.
        """
        if collision_type is None:
            return
        for begin in [True, False]:
            collision_registry.callbacks[begin].pop(collision_type, None)
            for shape_ct in list(collision_registry.callbacks[begin]):
                collision_registry.callbacks[begin][shape_ct].pop(collision_type, None)
        collision_registry.shape_registry.pop(collision_type, None)

    def _reregister_own_callbacks(self, saved_callbacks):
        """Re-register this sprite's own callbacks after physics recreation."""
        for callback, sprite in saved_callbacks[CallbackType.WHEN_TOUCHING]:
            self.when_touching(sprite)(callback)
        for callback, wall_side in saved_callbacks[CallbackType.WHEN_TOUCHING_WALL]:
            self.when_touching_wall(callback, wall=wall_side)
        for callback, sprite in saved_callbacks[CallbackType.WHEN_STOPPED_TOUCHING]:
            self.when_stopped_touching(sprite)(callback)
        for callback, wall_side in saved_callbacks[
            CallbackType.WHEN_STOPPED_TOUCHING_WALL
        ]:
            self.when_stopped_touching_wall(callback, wall=wall_side)

    def _reregister_dependent_callbacks(self):
        """Re-register callbacks from other sprites that reference self.

        When self's pymunk shape changes, other sprites' collision registrations
        become stale and need to be refreshed.
        """
        sprite_callback_types = [
            CallbackType.WHEN_TOUCHING,
            CallbackType.WHEN_STOPPED_TOUCHING,
        ]
        for dependent in list(self.events._dependent_sprites):
            dep_id = id(dependent)
            dep_saved = {
                callback_type: list(
                    callback_manager.get_callback(callback_type, dep_id) or []
                )
                for callback_type in sprite_callback_types
            }
            has_refs = any(s is self for cbs in dep_saved.values() for _, s in cbs)
            if not has_refs:
                continue
            for callback_type in sprite_callback_types:
                callback_manager.remove_callbacks(callback_type, dep_id)
            self._cleanup_collision_registry(
                dependent.physics._pymunk_shape.collision_type
            )
            for cb, sprite in dep_saved[CallbackType.WHEN_TOUCHING]:
                dependent.when_touching(sprite)(cb)
            for cb, sprite in dep_saved[CallbackType.WHEN_STOPPED_TOUCHING]:
                dependent.when_stopped_touching(sprite)(cb)

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
        sensor=False,
    ):
        """Start the physics simulation for this sprite.
        :param can_move: Whether the object can move.
        :param stable: Whether the object is stable.
        :param x_speed: The x-speed of the object.
        :param y_speed: The y-speed of the object.
        :param obeys_gravity: Whether the object obeys gravity.
        :param bounciness: The bounciness of the object.
        :param mass: The mass of the object.
        :param friction: The friction of the object.
        :param sensor: Whether the object is a sensor (detects collisions without blocking).
        """
        saved_callbacks = self._save_and_clear_callbacks()

        if self.physics is not None:
            self._cleanup_collision_registry(self.physics._pymunk_shape.collision_type)
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
            sensor=sensor,
        )

        self._reregister_own_callbacks(saved_callbacks)
        self._reregister_dependent_callbacks()

    def stop_physics(self):
        """Resets the physics to the starting situation"""
        self.start_physics(stable=True, obeys_gravity=False)
