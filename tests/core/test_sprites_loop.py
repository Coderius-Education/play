"""Each frame, a moving sprite takes its place, angle and speed from its physics body."""

import math

import pytest

import play
from play.core.sprites_loop import update_sprite_physics


def _box_whose_body_moved(x, y, angle, velocity=(0.0, 0.0)):
    """A physics box at (100, 100), turned 30 degrees, whose body now says otherwise."""
    box = play.new_box(x=100, y=100, angle=30)
    box.start_physics(obeys_gravity=False)
    body = box.physics._pymunk_body
    body.position = x, y
    body.angle = math.radians(angle)
    body.velocity = velocity
    return box


def test_a_sprite_takes_its_place_angle_and_speed_from_its_body():
    box = _box_whose_body_moved(10.0, 20.0, 45.0, velocity=(5.0, -3.0))

    update_sprite_physics(box)

    assert (box.x, box.y) == (10.0, 20.0)
    assert box.angle == pytest.approx(45.0)
    assert (box.physics.x_speed, box.physics.y_speed) == (5.0, -3.0)


@pytest.mark.parametrize(
    "body, expected",
    [
        ((float("nan"), 20.0, 45.0), (100, 20.0, 45.0)),
        ((10.0, float("nan"), 45.0), (10.0, 100, 45.0)),
        ((100.0, 100.0, float("nan")), (100, 100, 30)),
    ],
    ids=["x", "y", "angle"],
)
def test_a_body_value_that_is_not_a_number_is_ignored_and_the_others_still_follow(
    body, expected
):
    box = _box_whose_body_moved(*body)

    update_sprite_physics(box)

    assert (box.x, box.y, box.angle) == pytest.approx(expected)


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
