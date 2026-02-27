"""Collision callbacks for sprites."""

from enum import Enum

from pymunk import Shape, Arbiter

from play.physics import physics_space


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
    """

    def __init__(self):
        self.callbacks = {True: {}, False: {}}
        self.shape_registry = {}

        try:
            physics_space.on_collision(
                begin=self._handle_collision, separate=self._handle_end_collision
            )
        except AttributeError:
            handler = physics_space.add_default_collision_handler()
            handler.begin = self._handle_collision
            handler.separate = self._handle_end_collision

    def _handle_collision(self, arbiter, _, __):
        shape_a, shape_b = arbiter.shapes

        if not hasattr(shape_a, "collision_id") or not hasattr(shape_b, "collision_id"):
            return True

        # check for walls
        if any(
            [
                self.shape_registry[shape_a.collision_type] is None,
                self.shape_registry[shape_b.collision_type] is None,
            ]
        ):
            return True

        # Only add callback to shape_a to avoid duplicate execution
        # (both sprites would execute the same callback otherwise)
        if (
            shape_a.collision_type in self.callbacks[True]
            and shape_b.collision_type in self.callbacks[True][shape_a.collision_type]
        ):
            callback = self.callbacks[True][shape_a.collision_type][
                shape_b.collision_type
            ]
            self.shape_registry[shape_a.collision_type].events.set_touching(
                shape_b.collision_id, callback
            )
        # If callback is only registered in the reverse direction, use that
        elif (
            shape_b.collision_type in self.callbacks[True]
            and shape_a.collision_type in self.callbacks[True][shape_b.collision_type]
        ):
            callback = self.callbacks[True][shape_b.collision_type][
                shape_a.collision_type
            ]
            self.shape_registry[shape_a.collision_type].events.set_touching(
                shape_b.collision_id, callback
            )
        return True

    def _handle_end_collision_shape(self, shape_a: Shape, shape_b: Shape):
        """Check and fire the stopped-touching callback for shape_a → shape_b.

        Returns True if the second direction should be skipped:
        - a wall is involved (wall callbacks are handled separately), or
        - a callback was found and queued for this collision pair.
        Returns False if no relevant callback was found.
        """
        if not hasattr(shape_a, "collision_id") or not hasattr(shape_b, "collision_id"):
            return False

        # check for walls — wall callbacks are handled separately; return True
        # so the caller skips the reverse direction check.
        if any(
            [
                self.shape_registry[shape_a.collision_type] is None,
                self.shape_registry[shape_b.collision_type] is None,
            ]
        ):
            return True

        if shape_a.collision_type in self.shape_registry and self.shape_registry[
            shape_a.collision_type
        ].events.get_touching(shape_b.collision_id):
            self.shape_registry[shape_a.collision_type].events.clear_touching(
                shape_b.collision_id
            )
        fired = False
        if (
            shape_a.collision_type in self.callbacks[False]
            and shape_b.collision_type in self.callbacks[False][shape_a.collision_type]
        ):
            callback = self.callbacks[False][shape_a.collision_type][
                shape_b.collision_type
            ]
            self.shape_registry[shape_a.collision_type].events.set_stopped(
                shape_b.collision_id, callback
            )
            fired = True
        return fired

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

        self.shape_registry[shape.collision_type] = sprite

        if not shape.collision_type in self.callbacks[begin]:
            self.callbacks[begin][shape.collision_type] = {}

        # pymunk always initialises collision_type=0 on every Shape, so
        # hasattr() would always return True.  Use our own sentinel flag to
        # distinguish "we assigned a unique id" from "pymunk defaulted it to 0".
        if not getattr(other_shape, "_play_collision_type_set", False):
            other_shape.collision_type = id(other_shape)
            other_shape._play_collision_type_set = True

        # Check if a callback already exists for this collision pair (sprites only)
        if (
            collision_type != CollisionType.WALL
            and other_shape.collision_type
            in self.callbacks[begin][shape.collision_type]
        ):
            event_type = "when_touching" if begin else "when_stopped_touching"
            raise ValueError(
                f"You already have a @sprite.{event_type}() for these two sprites. "
                f"You can only use one. Put all your code in a single function instead."
            )

        self.callbacks[begin][shape.collision_type][
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
        self._register_shape(
            sprite_b, shape_b, shape_a, callback, collision_type, begin
        )


collision_registry = CollisionCallbackRegistry()
