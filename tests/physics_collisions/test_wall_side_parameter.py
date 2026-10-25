"""The wall parameter of when_touching_wall and when_stopped_touching_wall."""

import pytest

import play
from play.callback.collision_callbacks import WallSide

ALL_WALLS = [WallSide.RIGHT, WallSide.TOP, WallSide.LEFT, WallSide.BOTTOM]


def _ball_round_the_screen():
    """A ball that touches the right, top, left and bottom wall, in that order."""
    ball = play.new_circle(x=300, y=200, radius=10)
    ball.start_physics(x_speed=600, y_speed=300, obeys_gravity=False)
    return ball


def _run_frames(frames=150):
    counted = [0]

    @play.repeat_forever
    def step():
        counted[0] += 1
        if counted[0] == frames:
            play.stop_program()

    play.start_program()


def test_wall_sides_are_play_wall_side_with_readable_values():
    assert play.WallSide is WallSide
    assert {side.name: side.value for side in play.WallSide} == {
        "TOP": "top",
        "BOTTOM": "bottom",
        "LEFT": "left",
        "RIGHT": "right",
    }


@pytest.mark.parametrize(
    "wall, expected",
    [
        (None, ALL_WALLS),
        (WallSide.LEFT, [WallSide.LEFT]),
        ([WallSide.LEFT, WallSide.RIGHT], [WallSide.RIGHT, WallSide.LEFT]),
        ([WallSide.BOTTOM, WallSide.TOP], [WallSide.TOP, WallSide.BOTTOM]),
    ],
    ids=["every wall", "one wall", "two walls", "top and bottom"],
)
@pytest.mark.parametrize("event", ["when_touching_wall", "when_stopped_touching_wall"])
def test_a_wall_callback_runs_only_for_the_walls_it_names(event, wall, expected):
    ball = _ball_round_the_screen()
    touched = []

    def on_wall(wall):
        touched.append(wall)

    getattr(ball, event)(on_wall, wall=wall)

    _run_frames()

    assert touched == expected


def test_a_wall_callback_may_leave_out_the_wall_parameter():
    ball = _ball_round_the_screen()
    touched = []

    @ball.when_touching_wall
    def on_wall():
        touched.append("touched")

    _run_frames()

    assert touched == ["touched"] * 4


@pytest.mark.xfail(
    strict=True,
    reason="a second when_touching_wall on a sprite silently replaces the first",
)
@pytest.mark.parametrize("event", ["when_touching_wall", "when_stopped_touching_wall"])
def test_a_second_wall_callback_does_not_silently_replace_the_first(event):
    ball = _ball_round_the_screen()
    left, every = [], []
    getattr(ball, event)(lambda: left.append("left"), wall=WallSide.LEFT)
    try:
        getattr(ball, event)(lambda: every.append("any"))
    except ValueError:
        return

    _run_frames()

    assert (left, every) == (["left"], ["any"] * 4)
