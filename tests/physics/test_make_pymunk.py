"""How start_physics() settings decide whether a sprite falls, gets pushed or turns."""

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


def _ball_hitting(x, y):
    ball = play.new_circle(x=x - 100, y=y + 30, radius=10)
    ball.start_physics(x_speed=300, obeys_gravity=False, mass=50)
    return ball


@pytest.mark.parametrize("stable", [False, True])
@pytest.mark.parametrize("obeys_gravity", [False, True])
def test_a_sprite_that_cannot_move_is_neither_pulled_down_nor_pushed(
    stable, obeys_gravity
):
    box = play.new_box(width=20, height=100)
    box.start_physics(can_move=False, stable=stable, obeys_gravity=obeys_gravity)
    ball = _ball_hitting(0, 0)

    _run_frames(60)

    assert (box.x, box.y, box.angle) == (0, 0, 0)
    assert ball.physics.x_speed < 0


def test_a_stable_sprite_that_obeys_gravity_still_falls():
    box = play.new_box(width=20, height=20)
    box.start_physics(stable=True, obeys_gravity=True)

    _run_frames(60)

    assert box.y == pytest.approx(-50, abs=1)


def test_a_moving_platform_carries_a_box_without_sagging_or_slowing():
    platform = play.new_box(y=-100, width=200, height=20)
    platform.start_physics(stable=True, obeys_gravity=False, x_speed=30)
    box = play.new_box(y=0, width=20, height=20)
    box.start_physics(bounciness=0)

    _run_frames(120)

    assert (platform.x, platform.y) == (pytest.approx(60), -100)
    assert platform.physics.x_speed == 30
    assert box.y == pytest.approx(-80, abs=0.5)


def test_without_gravity_a_stable_sprite_is_pushed_but_does_not_turn():
    set_gravity(0)
    box = play.new_box(width=20, height=100)
    box.start_physics(stable=True, obeys_gravity=False)
    _ball_hitting(0, 0)

    _run_frames(60)

    assert box.x > 20
    assert box.angle == 0


def test_a_sprite_starts_physics_where_it_is_turned_the_way_it_was():
    box = play.new_box(x=150, y=-75, width=20, height=20, angle=30)
    box.start_physics(x_speed=60, obeys_gravity=False)

    _run_frames(60)

    assert (box.x, box.y, box.angle) == (pytest.approx(210), -75, pytest.approx(30))


def test_a_circle_is_hit_on_its_round_edge_and_a_box_in_its_corners():
    circle = play.new_circle(radius=25)
    circle.start_physics()
    box = play.new_box(x=200, width=50, height=30)
    box.start_physics()

    assert circle.is_touching((24, 0))
    assert not circle.is_touching((20, 20))
    assert box.is_touching((224, 14))
    assert not box.is_touching((224, 16))
