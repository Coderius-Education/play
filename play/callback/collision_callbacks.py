"""Collision callbacks for sprites."""

from enum import Enum

from pymunk import Shape, Arbiter

from ..physics import physics_space


class WallSide(Enum):
    """Enum representing the sides of the screen walls."""

    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


class CollisionType(Enum):
    SPRITE = 0
    WALL = 1


class CollisionCallbackRegistry:  # pylint: disable=too-few-public-methods
    """
    A registry for collision callbacks.

    pymunk calls the two handlers below for every collision in the space.
    Each registered shape carries its sprite as ``_play_sprite``, and
    ``callbacks[begin][type][other_type]`` holds the callback for a pair,
    keyed on the shapes' ``collision_type``.
    """

    def __init__(self):
        self.callbacks = {}
        self.reset()
        physics_space.on_collision(
            begin=self._handle_collision, separate=self._handle_end_collision
        )

    def reset(self):
        """Clear every registered callback.

        Shared with the constructor so tests reset through the same code
        instead of reassigning ``callbacks`` from outside.
        """
        self.callbacks = {True: {}, False: {}}

    def _callback(self, begin, shape, other_shape):
        """The callback registered for *shape* against *other_shape*, or None."""
        return (
            self.callbacks[begin]
            .get(shape.collision_type, {})
            .get(other_shape.collision_type)
        )

    def forget(self, shape):
        """Drop every callback registered for or against *shape*.

        Used when a sprite's collision registrations are about to be redone,
        so none of the old ones can fire.
        """
        collision_type = shape.collision_type
        for begin in (True, False):
            self.callbacks[begin].pop(collision_type, None)
            for others in self.callbacks[begin].values():
                others.pop(collision_type, None)
        if hasattr(shape, "_play_sprite"):
            del shape._play_sprite

    def _handle_collision(self, arbiter, _, __):
        shape_a, shape_b = arbiter.shapes

        # Wall collision: one shape has wall_side set by create_wall
        if hasattr(shape_a, "wall_side") or hasattr(shape_b, "wall_side"):
            if hasattr(shape_a, "wall_side"):
                wall_shape, sprite_shape = shape_a, shape_b
            else:
                wall_shape, sprite_shape = shape_b, shape_a
            sprite = getattr(sprite_shape, "_play_sprite", None)
            callback = self._callback(True, sprite_shape, wall_shape)
            if sprite is not None and callback is not None:
                sprite.events.set_touching(wall_shape.collision_type, callback)
            return True

        # Sprite-sprite collision
        if not hasattr(shape_a, "collision_id") or not hasattr(shape_b, "collision_id"):
            return True

        sprite_a = getattr(shape_a, "_play_sprite", None)
        if sprite_a is None:
            return True

        # Only queue on shape_a's sprite, so the callback runs once. Keyed on
        # the other shape's collision_type: collision_id is always
        # CollisionType.SPRITE, so every pair would share one slot.
        callback = self._callback(True, shape_a, shape_b)
        if callback is None:
            callback = self._callback(True, shape_b, shape_a)
        if callback is not None:
            sprite_a.events.set_touching(shape_b.collision_type, callback)
        return True

    def _handle_end_collision_shape(self, shape_a: Shape, shape_b: Shape):
        """Check and fire the stopped-touching callback for shape_a → shape_b.

        Returns True if the second direction should be skipped:
        - a wall separation was handled here, or
        - a sprite-sprite callback was found and queued.
        Returns False if no relevant callback was found.
        """
        # Wall separation needs only shape_a to be registered; sprite-sprite
        # separation needs both to have been.
        is_wall = hasattr(shape_b, "wall_side")
        if not is_wall and (
            not hasattr(shape_a, "collision_id") or not hasattr(shape_b, "collision_id")
        ):
            return False

        sprite_a = getattr(shape_a, "_play_sprite", None)
        if sprite_a is None:
            return False  # let caller try the reverse direction

        if sprite_a.events.get_touching(shape_b.collision_type):
            sprite_a.events.clear_touching(shape_b.collision_type)
        callback = self._callback(False, shape_a, shape_b)
        if callback is None:
            return False
        sprite_a.events.set_stopped(shape_b.collision_type, callback)
        return True

    def _handle_end_collision(self, arbiter: Arbiter, _, __):
        shape_a, shape_b = arbiter.shapes

        fired_a = self._handle_end_collision_shape(shape_a, shape_b)
        if not fired_a:
            self._handle_end_collision_shape(  # pylint: disable=arguments-out-of-order
                shape_b, shape_a
            )

        return True

    def _register_shape(
        self,
        sprite,
        shape: Shape,
        other_shape: Shape,
        callback,
        collision_type: CollisionType,
        begin: bool = True,
    ):
        shape.collision_id = collision_type
        shape.collision_type = id(shape)
        shape._play_sprite = sprite

        # pymunk always initialises collision_type=0 on every Shape, so
        # hasattr() would always return True.  Use our own sentinel flag to
        # distinguish "we assigned a unique id" from "pymunk defaulted it to 0".
        if not getattr(other_shape, "_play_collision_type_set", False):
            other_shape.collision_type = id(other_shape)
            other_shape._play_collision_type_set = True

        # Check if a callback already exists for this collision pair (sprites only)
        if (
            collision_type != CollisionType.WALL
            and self._callback(begin, shape, other_shape) is not None
        ):
            event_type = "when_touching" if begin else "when_stopped_touching"
            raise ValueError(
                f"You already have a @sprite.{event_type}() for these two sprites. "
                f"You can only use one. Put all your code in a single function instead."
            )

        self.callbacks[begin].setdefault(shape.collision_type, {})[
            other_shape.collision_type
        ] = callback

    def register(
        self,
        sprite_a,
        sprite_b,
        shape_a: Shape,
        shape_b: Shape,
        callback,
        collision_type: CollisionType,
        begin: bool = True,
    ):
        """
        Register a callback with a name.
        """
        self._register_shape(
            sprite_a, shape_a, shape_b, callback, collision_type, begin
        )
        if sprite_b is not None:
            self._register_shape(
                sprite_b, shape_b, shape_a, callback, collision_type, begin
            )


collision_registry = CollisionCallbackRegistry()
