import pytest

import play
from play.physics import set_gravity


def _run_frames(frames):
    counted = [0]

    @play.repeat_forever
    def step():
        counted[0] += 1
        if counted[0] == frames:
            play.stop_program()

    play.start_program()


def test_a_sprite_without_physics_stays_put_and_stops_a_physics_ball():
    wall = play.new_box(width=20, height=100)
    ball = play.new_circle(x=-100, radius=10)
    ball.start_physics(x_speed=200, obeys_gravity=False)

    _run_frames(60)

    assert (wall.x, wall.y, wall.angle) == (0, 0, 0)
    assert ball.physics.x_speed == pytest.approx(-200, abs=1)
    assert ball.x < -20


def test_a_cloned_physics_has_every_setting_of_the_original():
    box = play.new_box()
    box.start_physics(
        can_move=True,
        stable=True,
        x_speed=100,
        y_speed=-20,
        obeys_gravity=False,
        bounciness=0.8,
        mass=5,
        friction=0.3,
        sensor=True,
    )

    cloned = box.physics.clone(play.new_box(x=50))

    assert (
        cloned.can_move,
        cloned.stable,
        cloned.x_speed,
        cloned.y_speed,
        cloned.obeys_gravity,
        cloned.bounciness,
        cloned.mass,
        cloned.friction,
        cloned.sensor,
    ) == (True, True, 100, -20, False, 0.8, 5, 0.3, True)


@pytest.mark.parametrize(
    "gravity, x_speed, y_speed",
    [
        ({"vertical": 0, "horizontal": 60}, 60, 0),
        ({"vertical": -60, "horizontal": 60}, 60, -60),
        ({"vertical": -60}, 0, -60),
    ],
    ids=["sideways", "both", "vertical only"],
)
def test_gravity_pulls_a_sprite_the_way_it_is_set(gravity, x_speed, y_speed):
    set_gravity(**gravity)
    ball = play.new_circle(radius=10)
    ball.start_physics()

    _run_frames(60)

    assert ball.physics.x_speed == pytest.approx(x_speed, abs=0.5)
    assert ball.physics.y_speed == pytest.approx(y_speed, abs=0.5)


def test_setting_only_vertical_gravity_keeps_the_sideways_pull():
    set_gravity(vertical=0, horizontal=60)
    set_gravity(vertical=-60)
    ball = play.new_circle(radius=10)
    ball.start_physics()

    _run_frames(60)

    assert ball.physics.x_speed == pytest.approx(60, abs=0.5)
    assert ball.physics.y_speed == pytest.approx(-60, abs=0.5)


def test_sideways_gravity_can_be_switched_off_again():
    set_gravity(vertical=0, horizontal=60)
    set_gravity(vertical=0, horizontal=0)
    ball = play.new_circle(radius=10)
    ball.start_physics()

    _run_frames(60)

    assert (ball.x, ball.y) == (0, 0)
