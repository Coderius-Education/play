"""Calling start_physics() again keeps every contact callback running exactly as before."""

import pytest


@pytest.mark.parametrize("event", ["touching", "stopped touching"])
def test_a_third_sprites_callback_survives_another_sprite_starting_physics(event):
    import play

    ball = play.new_circle(radius=10)
    target = play.new_box(x=200, width=20, height=20)
    goal = play.new_box(x=-200, width=20, height=20)
    ball.start_physics(x_speed=-300, obeys_gravity=False)
    goal.start_physics(can_move=False)
    hits = []

    ball.when_touching(target)(lambda: hits.append("ball on target"))
    if event == "touching":
        goal.when_touching(ball)(lambda: hits.append("goal"))
    else:
        goal.when_stopped_touching(ball)(lambda: hits.append("goal"))

    target.start_physics(can_move=False)
    frames = [0]

    @play.repeat_forever
    def stop_later():
        frames[0] += 1
        if frames[0] == 90:
            play.stop_program()

    play.start_program()

    assert hits == ["goal"]


_REGISTER = {
    "when_touching": lambda ball, paddle, hit: ball.when_touching(paddle)(hit),
    "when_stopped_touching": lambda ball, paddle, hit: ball.when_stopped_touching(
        paddle
    )(hit),
    "when_touching_wall": lambda ball, paddle, hit: ball.when_touching_wall(hit),
    "when_stopped_touching_wall": lambda ball, paddle, hit: (
        ball.when_stopped_touching_wall(hit)
    ),
}


@pytest.mark.parametrize(
    "restarted, event",
    [
        ("ball", "when_touching"),
        ("ball", "when_stopped_touching"),
        ("ball", "when_touching_wall"),
        ("ball", "when_stopped_touching_wall"),
        ("paddle", "when_touching"),
        ("paddle", "when_stopped_touching"),
    ],
)
def test_callbacks_run_once_per_contact_after_many_restarts_of_physics(
    restarted, event
):
    import play

    if "wall" in event:
        ball = play.new_circle(x=-350, y=200, radius=10)
    else:
        ball = play.new_circle(x=0, radius=10)
    paddle = play.new_box(x=-300, width=20, height=200)
    ball.start_physics(x_speed=-600, obeys_gravity=False)
    hits = []
    _REGISTER[event](ball, paddle, lambda: hits.append("hit"))

    for _ in range(1500):
        if restarted == "paddle":
            paddle.start_physics(can_move=False)
        else:
            ball.start_physics(x_speed=-600, obeys_gravity=False)
    frames = [0]

    @play.repeat_forever
    def stop_later():
        frames[0] += 1
        if frames[0] == 60:
            play.stop_program()

    play.start_program()

    assert hits == ["hit"]


def test_when_stopped_touching_on_a_sprite_survives_it_starting_physics_again():
    import play

    ball = play.new_circle(radius=10)
    ball.start_physics(x_speed=-300, obeys_gravity=False)
    target = play.new_box(x=-100, width=20, height=200)
    target.start_physics(can_move=False)
    hits = []
    ball.when_stopped_touching(target)(lambda: hits.append("stopped"))
    target.start_physics(can_move=False)
    frames = [0]

    @play.repeat_forever
    def stop_later():
        frames[0] += 1
        if frames[0] == 120:
            play.stop_program()

    play.start_program()

    assert hits == ["stopped"]


def test_when_touching_stops_once_the_floor_is_moved_away_and_restarted():
    import play

    floor = play.new_box(y=-200, width=400, height=20)
    floor.start_physics(can_move=False)
    box = play.new_box(y=-180, width=20, height=20)
    box.start_physics(bounciness=0)
    frames = [0]
    calls = []
    box.when_touching(floor)(lambda: calls.append(frames[0]))

    @play.repeat_forever
    def move_the_floor():
        frames[0] += 1
        if frames[0] == 30:
            floor.y = -400
            floor.start_physics(can_move=False)
        if frames[0] == 60:
            play.stop_program()

    play.start_program()

    assert calls == list(range(30))
    assert box.y < -190
