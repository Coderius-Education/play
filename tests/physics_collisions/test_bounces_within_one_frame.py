"""A ball that bounces several times within one frame gets a callback for each bounce."""

import collections

import play

FRAMES = 120


def test_every_bounce_within_a_frame_runs_when_touching_and_when_stopped_touching():
    wall = play.new_box(x=-380, width=20, height=600)
    paddle = play.new_box(x=-330, width=20, height=100)
    ball = play.new_circle(x=-355, radius=10)
    wall.start_physics(can_move=False)
    paddle.start_physics(can_move=False)
    ball.start_physics(x_speed=-6000, obeys_gravity=False)
    frames = [0]
    touching = collections.Counter()
    stopped = collections.Counter()

    @ball.when_touching(paddle)
    def hit():
        touching[frames[0]] += 1

    @ball.when_stopped_touching(paddle)
    def left():
        stopped[frames[0]] += 1

    @play.repeat_forever
    def count():
        frames[0] += 1
        if frames[0] == FRAMES:
            play.stop_program()

    play.start_program()

    assert max(touching.values()) > 1
    assert abs(sum(touching.values()) - sum(stopped.values())) <= 1
