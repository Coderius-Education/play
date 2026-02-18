"""This handles the physics of the game."""

import math as _math
from dataclasses import dataclass

import pymunk as _pymunk

from ..globals import globals_list
from ..io.logging import play_logger
from ..utils import clamp as _clamp


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
        self._is_paused = False

        self._make_pymunk()

    def _compute_effective_dims(self, is_circle, size_factor):
        """Return (effective_radius, effective_w, effective_h) for the sprite."""
        if is_circle:
            return self.sprite._radius * size_factor, 0.0, 0.0
        if self.sprite.__class__.__name__ == "Box":
            return (
                0.0,
                self.sprite._width * size_factor,
                self.sprite._height * size_factor,
            )
        return 0.0, self.sprite.width, self.sprite.height

    def _compute_body_type(self):
        """Determine the pymunk body type based on movement and stability properties."""
        if not self.can_move:
            return _pymunk.Body.STATIC
        # Special case: moving platforms that don't obey gravity in a gravity world
        if self.stable and not self.obeys_gravity and physics_space.gravity != (0, 0):
            return _pymunk.Body.KINEMATIC
        return _pymunk.Body.DYNAMIC

    def _make_pymunk(self):
        # Save collision attributes so the collision registry stays valid
        prev_shape = getattr(self, "_pymunk_shape", None)
        collision_type = (
            getattr(prev_shape, "collision_type", None) if prev_shape else None
        )
        collision_id = getattr(prev_shape, "collision_id", None) if prev_shape else None

        mass = self.mass if self.can_move else 0
        size_factor = (self.sprite._size or 100) / 100
        is_circle = self.sprite.__class__.__name__ == "Circle"

        # Compute effective dimensions with size scaling for Box and Circle
        effective_radius, effective_w, effective_h = self._compute_effective_dims(
            is_circle, size_factor
        )

        if self.stable:
            moment = float("inf")
        elif is_circle:
            moment = _pymunk.moment_for_circle(mass, 0, effective_radius, (0, 0))
        else:
            moment = _pymunk.moment_for_box(mass, (effective_w, effective_h))

        body_type = self._compute_body_type()

        self._pymunk_body = _pymunk.Body(mass, moment, body_type=body_type)
        self._pymunk_body.position = self.sprite.x, self.sprite.y
        self._pymunk_body.angle = _math.radians(self.sprite.angle)

        if self.can_move:
            self._pymunk_body.velocity = (self._x_speed, self._y_speed)

        if not self.obeys_gravity:
            self._pymunk_body.velocity_func = lambda body, gravity, damping, dt: None

        if is_circle:
            self._pymunk_shape = _pymunk.Circle(
                self._pymunk_body, effective_radius, (0, 0)
            )
        else:
            self._pymunk_shape = _pymunk.Poly.create_box(
                self._pymunk_body, (effective_w, effective_h)
            )

        self._pymunk_shape.elasticity = _clamp(self.bounciness, 0, 0.9999)
        self._pymunk_shape.friction = self._friction

        # Restore collision attributes so collision callbacks keep working
        if collision_type is not None:
            self._pymunk_shape.collision_type = collision_type
            self._pymunk_shape.collision_id = collision_id

        if not self._is_paused:
            physics_space.add(self._pymunk_body, self._pymunk_shape)

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
        if self._pymunk_body and self._pymunk_shape:
            physics_space.add(self._pymunk_body, self._pymunk_shape)
        else:
            play_logger.error("Cannot unpause object, it has not been created yet.")

    def _remove(self):
        if self._is_paused:
            return  # Already removed from space
        if self._pymunk_body:
            physics_space.remove(self._pymunk_body)
        if self._pymunk_shape:
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
            self._remove()
            self._make_pymunk()

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
        self._pymunk_shape.elasticity = _clamp(self._bounciness, 0, 0.9999)

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
            self._remove()
            self._make_pymunk()

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


@dataclass
class _Gravity:
    """The gravity of the game."""

    vertical: int = -100
    horizontal: int = 0


globals_list.gravity = _Gravity()
physics_space = _pymunk.Space()
physics_space.sleep_time_threshold = 0.5
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
