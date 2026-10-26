"""What each physics setting does to a sprite, set in start_physics() or later."""

import pytest

import play
from play.physics import set_gravity


def _run_frames(frames, each_frame=None):
    counted = [0]

    @play.repeat_forever
    def step():
        counted[0] += 1
        if each_frame:
            each_frame(counted[0])
        if counted[0] == frames:
            play.stop_program()

    play.start_program()


SET_LATER = pytest.mark.parametrize("set_later", [False, True], ids=["start", "setter"])


@SET_LATER
@pytest.mark.parametrize("mass, fastest, slowest", [(100, 150, 200), (1, 0, 50)])
def test_a_heavier_ball_knocks_another_ball_away_faster(
    set_later, mass, fastest, slowest
):
    hitter = play.new_circle(x=-100, radius=20)
    hitter.start_physics(
        x_speed=100, obeys_gravity=False, mass=10 if set_later else mass
    )
    if set_later:
        hitter.physics.mass = mass
    target = play.new_circle(x=0, radius=20)
    target.start_physics(obeys_gravity=False, mass=10)

    _run_frames(120)

    assert fastest < target.physics.x_speed < slowest


@SET_LATER
@pytest.mark.parametrize("friction, speed", [(0, 200), (1, 100)])
def test_friction_slows_a_box_sliding_over_a_floor(set_later, friction, speed):
    floor = play.new_box(y=-200, width=700, height=20)
    box = play.new_box(x=-300, y=-180, width=20, height=20)
    start_with = 0.5 if set_later else friction
    floor.start_physics(can_move=False, friction=start_with)
    box.start_physics(x_speed=200, bounciness=0, stable=True, friction=start_with)
    if set_later:
        floor.physics.friction = friction
        box.physics.friction = friction

    _run_frames(60)

    assert box.physics.friction == friction
    assert box.physics.x_speed == pytest.approx(speed, abs=1)


def _highest_bounce(bounciness, set_later=False):
    ball = play.new_circle(y=0, radius=10)
    floor = play.new_box(y=-200, width=400, height=20)
    ball.start_physics(bounciness=0 if set_later else bounciness)
    floor.start_physics(can_move=False, bounciness=0 if set_later else bounciness)
    if set_later:
        ball.physics.bounciness = bounciness
        floor.physics.bounciness = bounciness
    heights = []

    def after_first_bounce(_frame):
        if ball.physics.y_speed > 0 or heights:
            heights.append(ball.y)

    _run_frames(300, after_first_bounce)
    return max(heights, default=None)


def test_a_ball_without_bounciness_stays_on_the_floor():
    assert _highest_bounce(0) is None


@SET_LATER
def test_a_bouncy_ball_bounces_back_almost_as_high_as_it_fell(set_later):
    assert _highest_bounce(1, set_later) == pytest.approx(0, abs=1)


def test_a_ball_bouncier_than_1_never_bounces_higher_than_it_fell():
    assert -1 < _highest_bounce(1.5) <= 0


@SET_LATER
@pytest.mark.parametrize("stable", [False, True])
def test_only_an_unstable_box_turns_when_hit_off_centre(set_later, stable):
    set_gravity(0)
    box = play.new_box(width=20, height=100)
    box.start_physics(obeys_gravity=False, stable=stable ^ set_later)
    if set_later:
        box.physics.stable = stable
    ball = play.new_circle(x=-100, y=40, radius=10)
    ball.start_physics(x_speed=200, obeys_gravity=False)

    _run_frames(60)

    if stable:
        assert box.angle == 0
    else:
        assert abs(box.angle) > 45


def test_a_sprite_that_can_no_longer_move_stops_where_it_is():
    box = play.new_box(width=20, height=20)
    box.start_physics(x_speed=60, obeys_gravity=False)

    def freeze(frame):
        if frame == 30:
            box.physics.can_move = False

    _run_frames(60, freeze)

    assert box.x == pytest.approx(30, abs=1)
    assert box.y == 0


def test_a_sprite_that_could_not_move_falls_once_it_can():
    box = play.new_box(width=20, height=20)
    box.start_physics(can_move=False)

    def release(frame):
        if frame == 30:
            box.physics.can_move = True

    _run_frames(60, release)

    assert box.y < -10


@pytest.mark.parametrize("stable", [False, True])
def test_a_floating_sprite_falls_once_it_obeys_gravity(stable):
    platform = play.new_box(y=100)
    platform.start_physics(stable=stable, obeys_gravity=False)

    def drop(frame):
        if frame == 30:
            platform.physics.obeys_gravity = True

    _run_frames(60, drop)

    assert platform.y < 90


def test_a_falling_sprite_keeps_its_speed_once_it_no_longer_obeys_gravity():
    box = play.new_box(width=20, height=20)
    box.start_physics()
    speeds = []

    def float_on(frame):
        if frame == 30:
            box.physics.obeys_gravity = False
        if frame > 30:
            speeds.append(box.physics.y_speed)

    _run_frames(60, float_on)

    assert speeds[0] < -40
    assert speeds[-1] == pytest.approx(speeds[0])


def test_setting_mass_on_a_sprite_without_physics_keeps_python_running():
    box = play.new_box()
    box.physics.mass = 50
    assert box.physics.mass == 50

    box.start_physics(can_move=False)
    box.physics.mass = 30
    box.physics.can_move = True
    assert box.physics._pymunk_body.mass == 30


@pytest.mark.parametrize("mass", [0, -5, "heavy", float("inf"), True])
def test_a_mass_pymunk_cannot_use_gives_a_clear_error(mass):
    box = play.new_box()
    box.start_physics()
    with pytest.raises(ValueError, match="number above 0"):
        box.physics.mass = mass
    with pytest.raises(ValueError, match="number above 0"):
        box.start_physics(mass=mass)


def test_a_sprite_that_cannot_move_may_have_no_mass():
    floor = play.new_box(y=-100, width=300, height=20)
    floor.start_physics(can_move=False, mass=0)
    floor.physics.mass = 0

    with pytest.raises(ValueError, match="number above 0"):
        floor.physics.can_move = True


def test_hiding_showing_or_restarting_a_removed_sprite_is_harmless():
    from play.physics import physics_space

    coin = play.new_circle()
    coin.start_physics(can_move=False)
    coin.remove()

    coin.hide()
    coin.show()
    coin.start_physics()
    coin.stop_physics()

    assert coin.physics._pymunk_body not in physics_space.bodies
    assert coin.physics._pymunk_shape not in physics_space.shapes


def test_showing_a_sprite_that_was_hidden_and_then_removed_keeps_it_out():
    from play.physics import physics_space

    coin = play.new_circle()
    coin.hide()
    coin.remove()
    coin.show()

    assert coin.physics._pymunk_body not in physics_space.bodies
