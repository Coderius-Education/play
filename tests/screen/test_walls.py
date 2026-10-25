"""The four walls around the screen, as a ball in a game meets them."""

import pytest

import play
from play.callback.collision_callbacks import WallSide
from play.globals import globals_list
from play.io.screen import remove_wall, screen


def _launch(x_speed, y_speed):
    ball = play.new_circle(x=0, y=0, radius=10)
    ball.start_physics(
        obeys_gravity=False, x_speed=x_speed, y_speed=y_speed, friction=1, mass=10
    )
    return ball


def _run_frames(count, each_frame=None):
    frames = [0]

    @play.repeat_forever
    def tick():
        if each_frame is not None:
            each_frame()
        frames[0] += 1
        if frames[0] == count:
            play.stop_program()

    play.start_program()


def test_remove_wall_takes_the_side_its_index_names():
    remove_wall(0)
    remove_wall(1)

    sides = {wall.wall_side for wall in globals_list.walls}
    assert sides == {WallSide.LEFT, WallSide.RIGHT}


@pytest.mark.parametrize(
    "index, x_speed, y_speed, escapes",
    [
        (0, 0, 400, lambda ball: ball.y > screen.top),
        (1, 0, -400, lambda ball: ball.y < screen.bottom),
        (2, -500, 0, lambda ball: ball.x < screen.left),
        (3, 500, 0, lambda ball: ball.x > screen.right),
    ],
    ids=["top", "bottom", "left", "right"],
)
def test_a_ball_flies_out_through_a_removed_wall(index, x_speed, y_speed, escapes):
    ball = _launch(x_speed, y_speed)
    remove_wall(index)

    _run_frames(90)

    assert escapes(ball), f"the ball stayed on screen at ({ball.x:.0f}, {ball.y:.0f})"


def test_the_other_walls_still_hold_after_one_is_removed():
    ball = _launch(-500, 0)
    remove_wall(3)

    _run_frames(90)

    assert screen.left < ball.x < screen.right


def test_a_wall_bounce_keeps_the_ball_speed_and_its_sideways_motion():
    ball = _launch(300, 120)
    after_bounce = []

    def watch():
        if ball.physics.x_speed < 0 and not after_bounce:
            after_bounce.append((ball.physics.x_speed, ball.physics.y_speed))

    _run_frames(100, watch)

    assert after_bounce, "the ball never bounced off the right wall"
    x_speed, y_speed = after_bounce[0]
    assert x_speed == pytest.approx(-300, rel=0.05)
    assert y_speed == pytest.approx(120, rel=0.05)


def test_a_ball_rolling_along_a_wall_is_not_slowed_by_it():
    ball = play.new_circle(x=-300, y=screen.bottom + 10, radius=10)
    ball.start_physics(x_speed=200, y_speed=0, friction=1, mass=10, bounciness=0)

    _run_frames(60)

    assert ball.physics.x_speed == pytest.approx(200, rel=0.05)


def test_resizing_twice_leaves_one_wall_per_side_at_the_latest_edges():
    screen.resize(400, 300)
    screen.resize(1000, 700)
    ball = _launch(600, 0)
    furthest = [0]

    def watch():
        furthest[0] = max(furthest[0], ball.x)

    _run_frames(120, watch)

    assert sorted(wall.wall_side.name for wall in globals_list.walls) == sorted(
        side.name for side in WallSide
    )
    assert 200 < furthest[0] <= screen.right
