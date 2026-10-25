"""Each frame, a moving sprite takes its place, angle and speed from its physics body."""

import math
from unittest.mock import MagicMock

import pytest

import play
from play.core.sprites_loop import update_sprite_physics


def _sprite_with_body(x=0.0, y=0.0, angle=0.0, velocity=(0.0, 0.0)):
    """A stand-in sprite whose physics body is at (x, y), turned *angle* degrees."""
    sprite = MagicMock()
    body = sprite.physics._pymunk_body
    body.position.x = x
    body.position.y = y
    body.angle = math.radians(angle)
    body.velocity = velocity
    sprite._x, sprite._y, sprite.angle = 99.0, 99.0, 99.0
    return sprite


def test_a_sprite_takes_its_place_angle_and_speed_from_its_body():
    sprite = _sprite_with_body(x=10.0, y=20.0, angle=45.0, velocity=(5.0, -3.0))

    update_sprite_physics(sprite)

    assert (sprite._x, sprite._y) == (10.0, 20.0)
    assert sprite.angle == pytest.approx(45.0)
    assert (sprite.physics._x_speed, sprite.physics._y_speed) == (5.0, -3.0)


@pytest.mark.parametrize(
    "body, kept",
    [
        ({"x": float("nan"), "y": 20.0}, ("_x",)),
        ({"x": 10.0, "y": float("nan")}, ("_y",)),
        ({"angle": float("nan")}, ("angle",)),
    ],
    ids=["x", "y", "angle"],
)
def test_a_body_value_that_is_not_a_number_leaves_the_sprite_where_it_was(body, kept):
    sprite = _sprite_with_body(**body)

    update_sprite_physics(sprite)

    assert all(getattr(sprite, name) == 99.0 for name in kept)


def test_the_speed_a_student_reads_turns_round_after_a_bounce():
    ball = play.new_circle(x=360, radius=20)
    ball.start_physics(x_speed=300, obeys_gravity=False, bounciness=1.0)
    speeds = []

    @play.repeat_forever
    def watch():
        speeds.append(ball.physics.x_speed)
        if len(speeds) == 30:
            play.stop_program()

    play.start_program()

    assert speeds[0] == pytest.approx(300)
    assert speeds[-1] < 0
