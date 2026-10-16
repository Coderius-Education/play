"""An async def contact callback runs as a task of its own, so its awaits do not hold up the game."""

from typing import NamedTuple

import pytest

import play

FRAMES = 60


class Run(NamedTuple):
    start: int
    end: int
    at_once: int


class _Runs:
    """The frame count, and every finished run of a contact callback."""

    def __init__(self):
        self.frame = 0
        self.running = 0
        self.seen = []

    async def landed(self):
        self.running += 1
        start = self.frame
        for _ in range(3):
            await play.animate()
        self.seen.append(Run(start, self.frame, self.running))
        self.running -= 1


def _ball_at(y):
    ball = play.new_circle(y=y, radius=10)
    ball.start_physics(bounciness=0)
    return ball


def _run_frames(runs):
    @play.repeat_forever
    def count():
        runs.frame += 1
        if runs.frame == FRAMES:
            play.stop_program()

    play.start_program()


def _touching_a_floor():
    floor = play.new_box(y=-200, width=400, height=20)
    floor.start_physics(can_move=False)
    return _ball_at(-179).when_touching(floor)


def _touching_the_bottom_wall():
    return _ball_at(play.screen.bottom + 11).when_touching_wall


@pytest.mark.parametrize(
    "when_touching",
    [_touching_a_floor, _touching_the_bottom_wall],
    ids=["sprite", "wall"],
)
def test_frames_keep_running_while_an_async_contact_callback_awaits(when_touching):
    runs = _Runs()
    when_touching()(runs.landed)

    _run_frames(runs)

    assert len(runs.seen) > 1
    assert all(run.end > run.start for run in runs.seen)
    assert all(run.at_once == 1 for run in runs.seen)


def test_restarting_physics_does_not_run_an_async_contact_callback_twice_at_once():
    floor = play.new_box(y=-200, width=400, height=20)
    floor.start_physics(can_move=False)
    ball = _ball_at(-179)
    runs = _Runs()
    ball.when_touching(floor)(runs.landed)

    @play.repeat_forever
    def restart():
        if runs.frame in (10, 20):
            ball.start_physics(bounciness=0)

    _run_frames(runs)

    assert len(runs.seen) > 1
    assert all(run.at_once == 1 for run in runs.seen)


def _bouncing_ball_over_a_floor(x):
    floor = play.new_box(x=x, y=-200, width=100, height=20)
    floor.start_physics(can_move=False)
    ball = play.new_circle(x=x, y=-165, radius=10)
    ball.start_physics(bounciness=1)
    return ball, floor


def test_an_async_when_touching_starts_in_the_sub_step_its_contact_begins():
    runs, first_touch = _Runs(), {}
    plain_ball, plain_floor = _bouncing_ball_over_a_floor(-100)
    async_ball, async_floor = _bouncing_ball_over_a_floor(100)

    @plain_ball.when_touching(plain_floor)
    def plain():
        first_touch.setdefault("plain", (runs.frame, plain_ball.y))

    @async_ball.when_touching(async_floor)
    async def landed():
        first_touch.setdefault("async", (runs.frame, async_ball.y))

    _run_frames(runs)

    assert first_touch["async"] == first_touch["plain"]
