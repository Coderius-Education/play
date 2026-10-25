import pymunk
import pytest

import play
from play.physics import on_every_collision, physics_space


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_static_body_does_not_sleep():
    """Bodies should never sleep — sleeping disables collision detection."""
    ramp = play.new_box(y=-100, width=500, height=20, angle=15)

    # Step the simulation long enough that sleep would have kicked in
    # with the old sleep_time_threshold=0.5
    for _ in range(100):
        physics_space.step(1 / 60)

    assert not ramp.physics._pymunk_body.is_sleeping


def test_angled_platform_collision():
    """A falling box must collide with an angled platform, not pass through."""
    ramp = play.new_box(y=-100, width=500, height=20, angle=15)
    ramp.start_physics(can_move=False)

    block = play.new_box(x=0, y=100, width=40, height=40, color="red")
    block.start_physics(obeys_gravity=True)

    # Run enough physics steps for the block to fall onto the ramp
    for _ in range(300):
        physics_space.step(1 / 60)

    # The block should have landed on the ramp, not fallen through
    assert block.physics._pymunk_body.position.y > ramp.physics._pymunk_body.position.y


def _make_sensor_at_start(platform):
    platform.start_physics(can_move=False, sensor=True)


def _make_sensor_later(platform):
    platform.start_physics(can_move=False)
    platform.physics.sensor = True


def _make_sensor_then_retype(platform):
    _make_sensor_later(platform)
    platform.physics.can_move = True
    platform.physics.can_move = False


@pytest.mark.parametrize(
    "make_platform, passes_through",
    [
        (lambda platform: platform.start_physics(can_move=False), False),
        (_make_sensor_at_start, True),
        (_make_sensor_later, True),
        (_make_sensor_then_retype, True),
    ],
    ids=["solid", "sensor", "sensor set later", "sensor set before can_move changes"],
)
def test_only_a_sensor_platform_lets_a_falling_block_through(
    make_platform, passes_through
):
    platform = play.new_box(y=-50, width=200, height=20)
    make_platform(platform)
    block = play.new_box(y=0, width=20, height=20)
    block.start_physics(obeys_gravity=True, bounciness=0)

    frames = [0]

    @play.repeat_forever
    def stop_later():
        frames[0] += 1
        if frames[0] == 120:
            play.stop_program()

    play.start_program()

    assert (block.y < -50) is passes_through


def test_sleep_disabled_on_space():
    """The physics space should not have body sleeping enabled."""
    assert physics_space.sleep_time_threshold == float("inf")


@pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
def test_a_ball_still_lands_on_a_floor_when_the_begin_handler_raises():
    space = pymunk.Space()
    space.gravity = (0, -900)
    floor = pymunk.Segment(space.static_body, (-100, 0), (100, 0), 1)
    ball = pymunk.Body(1, 100)
    ball.position = (0, 20)
    space.add(floor, ball, pymunk.Circle(ball, 10))

    def begin(*_):
        raise RuntimeError("bug in a begin handler")

    on_every_collision(begin, lambda *_: None, space=space)
    for _ in range(120):
        space.step(1 / 60)

    assert ball.position.y > 0
