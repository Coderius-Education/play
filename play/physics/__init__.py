"""This handles the physics of the game."""

import math as _math
from dataclasses import dataclass

import pygame
import pymunk as _pymunk

from ..globals import globals_list


class Physics:
    def __init__(
        self,
        sprite,
        can_move,
        stable,
        x_speed,
        y_speed,
        obeys_gravity,
        bounciness,
        mass,
        friction,
        sensor=False,
    ):
        """
        Examples of objects with different parameters:

            Blocks that can be knocked over (the default):
                can_move = True
                stable = False
                obeys_gravity = True
            Jumping platformer character:
                can_move = True
                stable = True (doesn't fall over)
                obeys_gravity = True
            Moving platform:
                can_move = True
                stable = True
                obeys_gravity = False
            Stationary platform:
                can_move = False
                (others don't matter)
            Sensor (detects collisions without blocking):
                sensor = True
        """
        self.sprite = sprite
        self._can_move = can_move
        self._stable = stable
        self._x_speed = x_speed
        self._y_speed = y_speed
        self._obeys_gravity = obeys_gravity
        self._bounciness = bounciness
        self._mass = mass
        self._friction = friction
        self._sensor = sensor
        self._is_paused = False

        self._make_pymunk()

    def _compute_body_type(self):
        """Determine the pymunk body type based on movement and stability properties."""
        if not self.can_move:
            return _pymunk.Body.STATIC
        # Special case: moving platforms that don't obey gravity in a gravity world
        if self.stable and not self.obeys_gravity and physics_space.gravity != (0, 0):
            return _pymunk.Body.KINEMATIC
        return _pymunk.Body.DYNAMIC

    def _hit_dims(self):
        """Ask the sprite for its hit-shape as ``(radius, width, height)``.

        Box, Circle and Video scale their logical size by ``size``; other
        sprites fall back to the current rect. A positive radius means a
        circular shape.
        """
        return self.sprite._hit_dims((self.sprite._size or 100) / 100)

    def _moment(self, is_circle, radius, width, height):
        mass = self.mass if self.can_move else 0
        if self.stable:
            return float("inf")
        if is_circle:
            return _pymunk.moment_for_circle(mass, 0, radius, (0, 0))
        return _pymunk.moment_for_box(mass, (width, height))

    def _make_pymunk(self):
        """Build the body and shape once, at construction. Later changes to the
        sprite's size or physics settings are applied in place by
        :meth:`_resize_shape` and :meth:`_retype_body`."""
        radius, width, height = self._hit_dims()
        is_circle = radius > 0
        mass = self.mass if self.can_move else 0

        self._pymunk_body = _pymunk.Body(
            mass,
            self._moment(is_circle, radius, width, height),
            body_type=self._compute_body_type(),
        )
        self._pymunk_body.position = self.sprite.x, self.sprite.y
        self._pymunk_body.angle = _math.radians(self.sprite.angle)

        if self.can_move:
            self._pymunk_body.velocity = (self._x_speed, self._y_speed)

        if not self.obeys_gravity:
            self._pymunk_body.velocity_func = lambda body, gravity, damping, dt: None

        if is_circle:
            self._pymunk_shape = _pymunk.Circle(self._pymunk_body, radius, (0, 0))
        else:
            self._pymunk_shape = _pymunk.Poly.create_box(
                self._pymunk_body, (width, height)
            )

        self._pymunk_shape.elasticity = pygame.math.clamp(self.bounciness, 0, 0.9999)
        self._pymunk_shape.friction = self._friction
        self._pymunk_shape.sensor = self._sensor

        if not self._is_paused:
            physics_space.add(self._pymunk_body, self._pymunk_shape)

    def _resize_shape(self):
        """Fit the shape to the sprite's current hit dimensions, in place.

        The body and shape objects survive, so their collision_type, sensor
        flag and place in the collision registry need no bookkeeping. pymunk
        calls these setters unsafe because a shape that grows into another
        does not push it away as a moving one would; that is exactly what a
        rebuilt shape did too.
        """
        radius, width, height = self._hit_dims()
        shape = self._pymunk_shape
        is_circle = isinstance(shape, _pymunk.Circle)
        if is_circle:
            radius = max(radius, 0)  # a negative size means "nothing", not a hole
            shape.unsafe_set_radius(radius)
        else:
            shape.unsafe_set_vertices(_box_vertices(width, height))
        shape.cache_bb()
        if not self._is_paused:
            physics_space.reindex_shape(shape)
        moment = self._moment(is_circle, radius, width, height)
        # pymunk refuses a zero moment on a dynamic body in a space, so a
        # sprite shrunk to nothing keeps the moment it had.
        if self._pymunk_body.body_type == _pymunk.Body.DYNAMIC and moment > 0:
            self._pymunk_body.moment = moment

    def _retype_body(self):
        """Give the body the type its settings call for, in place.

        pymunk zeroes the mass and moment of a body that becomes dynamic, so
        both are set again afterwards; static and kinematic bodies take
        neither (Chipmunk aborts the process rather than raise on it).
        """
        body = self._pymunk_body
        body.body_type = self._compute_body_type()
        if body.body_type == _pymunk.Body.DYNAMIC and self._mass > 0:
            body.mass = self._mass
        self._resize_shape()
        if self.can_move:
            body.velocity = (self._x_speed, self._y_speed)

    def clone(self, sprite):
        """
        Clone the physics object.
        :param sprite: The sprite to clone.
        """
        return self.__class__(
            sprite=sprite,
            can_move=self.can_move,
            x_speed=self.x_speed,
            y_speed=self.y_speed,
            obeys_gravity=self.obeys_gravity,
            bounciness=self.bounciness,
            mass=self.mass,
            friction=self._friction,
            stable=self.stable,
            sensor=self.sensor,
        )

    def pause(self):
        """Pause the object."""
        if self._is_paused:
            return
        self._remove()  # Remove first, before setting flag
        self._is_paused = True

    def unpause(self):
        """Unpause the object."""
        if not self._is_paused:
            return
        self._is_paused = False
        physics_space.add(self._pymunk_body, self._pymunk_shape)

    def _remove(self):
        if self._is_paused:
            return  # Already removed from space
        physics_space.remove(self._pymunk_body)
        physics_space.remove(self._pymunk_shape)

    @property
    def can_move(self):
        """Check if the object can move.
        :return: True if the object can move, False otherwise."""
        return self._can_move

    @can_move.setter
    def can_move(self, _can_move):
        prev_can_move = self._can_move
        self._can_move = _can_move
        if prev_can_move != _can_move:
            self._retype_body()

    @property
    def x_speed(self):
        """Get the x-speed of the object.
        :return: The x-speed of the object."""
        return self._x_speed

    @x_speed.setter
    def x_speed(self, _x_speed):
        self._x_speed = _x_speed
        self._pymunk_body.velocity = self._x_speed, self._pymunk_body.velocity[1]

    @property
    def y_speed(self):
        """Get the y-speed of the object.
        :return: The y-speed of the object."""
        return self._y_speed

    @y_speed.setter
    def y_speed(self, _y_speed):
        self._y_speed = _y_speed
        self._pymunk_body.velocity = self._pymunk_body.velocity[0], self._y_speed

    @property
    def bounciness(self):
        """Get the bounciness of the object.
        :return: The bounciness of the object."""
        return self._bounciness

    @bounciness.setter
    def bounciness(self, _bounciness):
        self._bounciness = _bounciness
        self._pymunk_shape.elasticity = pygame.math.clamp(self._bounciness, 0, 0.9999)

    @property
    def stable(self):
        """Check if the object is stable.
        :return: True if the object is stable, False otherwise."""
        return self._stable

    @stable.setter
    def stable(self, _stable):
        prev_stable = self._stable
        self._stable = _stable
        if self._stable != prev_stable:
            self._retype_body()

    @property
    def mass(self):
        """Get the mass of the object.
        :return: The mass of the object."""
        return self._mass

    @mass.setter
    def mass(self, _mass):
        """Set the mass of the object.
        :param _mass: The mass of the object."""
        self._mass = _mass
        self._pymunk_body.mass = _mass

    @property
    def sensor(self):
        """Check if the object is a sensor.
        :return: True if the object is a sensor, False otherwise."""
        return self._pymunk_shape.sensor

    @sensor.setter
    def sensor(self, value):
        self._sensor = value
        self._pymunk_shape.sensor = value

    @property
    def obeys_gravity(self):
        """Check if the object obeys gravity.
        :return: True if the object obeys gravity, False otherwise."""
        return self._obeys_gravity

    @obeys_gravity.setter
    def obeys_gravity(self, _obeys_gravity):
        self._obeys_gravity = _obeys_gravity
        if _obeys_gravity:
            self._pymunk_body.velocity_func = _pymunk.Body.update_velocity
        else:
            self._pymunk_body.velocity_func = lambda body, gravity, damping, dt: None


def _box_vertices(width, height):
    """The corners of a centred box, in the order Poly.create_box uses."""
    half_w, half_h = width / 2, height / 2
    return [(half_w, -half_h), (half_w, half_h), (-half_w, half_h), (-half_w, -half_h)]


@dataclass
class _Gravity:
    """The gravity of the game."""

    vertical: int = -100
    horizontal: int = 0


globals_list.gravity = _Gravity()
physics_space = _pymunk.Space()
physics_space.sleep_time_threshold = float("inf")
physics_space.idle_speed_threshold = 0
physics_space.gravity = globals_list.gravity.horizontal, globals_list.gravity.vertical


def set_gravity(vertical=-100, horizontal=None):
    """
    Set the gravity of the game.
    :param vertical: The vertical gravity of the game.
    :param horizontal: The horizontal gravity of the game.
    """
    globals_list.gravity.vertical = vertical
    if horizontal is not None:
        globals_list.gravity.horizontal = horizontal

    physics_space.gravity = (
        globals_list.gravity.horizontal,
        globals_list.gravity.vertical,
    )


def set_physics_simulation_steps(num_steps: int) -> None:
    """
    Set the number of simulation steps for the physics engine.
    :param num_steps: The number of simulation steps.
    """
    globals_list.num_sim_steps = num_steps
