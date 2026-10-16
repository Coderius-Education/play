"""An async def contact callback runs as a task of its own, so its awaits do not hold up the game."""

import sys

import pygame
import pytest

import play
from tests.conftest import post_key_down

FRAMES = 60


def _ball_at(y):
    ball = play.new_circle(y=y, radius=10)
    ball.start_physics(bounciness=0)
    return ball


def _run_frames(frame):
    @play.repeat_forever
    def count():
        frame[0] += 1
        if frame[0] == FRAMES:
            play.stop_program()

    play.start_program()


def _record_runs(frame, runs, running):
    async def landed():
        running.append(1)
        start = frame[0]
        for _ in range(3):
            await play.animate()
        runs.append((start, frame[0], len(running)))
        running.pop()

    return landed


def test_frames_keep_running_while_an_async_when_touching_awaits():
    floor = play.new_box(y=-200, width=400, height=20)
    floor.start_physics(can_move=False)
    ball = _ball_at(-179)
    frame, runs, running = [0], [], []
    ball.when_touching(floor)(_record_runs(frame, runs, running))

    _run_frames(frame)

    assert len(runs) > 1
    assert all(end > start for start, end, _ in runs)
    assert all(overlapping == 1 for _, _, overlapping in runs)


def test_frames_keep_running_while_an_async_when_touching_wall_awaits():
    ball = _ball_at(play.screen.bottom + 11)
    frame, runs, running = [0], [], []
    ball.when_touching_wall(_record_runs(frame, runs, running))

    _run_frames(frame)

    assert len(runs) > 1
    assert all(end > start for start, end, _ in runs)
    assert all(overlapping == 1 for _, _, overlapping in runs)


def test_a_bound_method_can_be_a_contact_callback():
    ball = play.new_circle(x=-100, radius=10)
    ball.start_physics(x_speed=300, obeys_gravity=False)
    coin = play.new_circle(radius=10)
    coin.start_physics(can_move=False)
    ball.when_touching(coin)(coin.hide)

    _run_frames([0])

    assert coin.is_hidden


def test_a_bound_method_can_be_a_key_callback():
    box = play.new_box()
    play.when_key_pressed("space")(box.hide)

    @play.when_program_starts
    async def press():
        await play.animate()
        post_key_down(pygame.K_SPACE)

    _run_frames([0])

    assert box.is_hidden


@pytest.mark.skipif(sys.version_info < (3, 12), reason="eager tasks need 3.12")
def test_an_async_when_touching_starts_in_the_frame_its_contact_begins():
    frame, first_touch = [0], {}
    for kind, x in (("plain", -100), ("async", 100)):
        floor = play.new_box(x=x, y=-200, width=100, height=20)
        floor.start_physics(can_move=False)
        ball = _ball_at(-165)
        ball.x = x
        if kind == "plain":
            ball.when_touching(floor)(lambda: first_touch.setdefault("plain", frame[0]))
        else:

            @ball.when_touching(floor)
            async def landed():
                first_touch.setdefault("async", frame[0])

    _run_frames(frame)

    assert first_touch["async"] == first_touch["plain"]


def test_restarting_physics_does_not_run_an_async_contact_callback_twice_at_once():
    floor = play.new_box(y=-200, width=400, height=20)
    floor.start_physics(can_move=False)
    ball = _ball_at(-179)
    frame, runs, running = [0], [], []
    ball.when_touching(floor)(_record_runs(frame, runs, running))

    @play.repeat_forever
    def restart():
        if frame[0] in (10, 20):
            ball.start_physics(bounciness=0)

    _run_frames(frame)

    assert len(runs) > 1
    assert all(overlapping == 1 for _, _, overlapping in runs)
