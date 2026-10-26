import pytest

import play
from play.callback.collision_callbacks import WallSide


def _run_frames(frames):
    """Run the game loop for *frames* frames, then stop it."""
    counted = [0]

    @play.repeat_forever
    def stop_later():
        counted[0] += 1
        if counted[0] == frames:
            play.stop_program()

    play.start_program()


@pytest.mark.parametrize("event", ["when_touching_wall", "when_stopped_touching_wall"])
def test_a_ball_bouncing_off_a_wall_runs_the_wall_callback_once(event):
    ball = play.new_circle(color="black", x=300, radius=20)
    ball.start_physics(obeys_gravity=False, x_speed=60, friction=0, bounciness=1.0)
    walls = []
    getattr(ball, event)(lambda wall: walls.append(wall))

    _run_frames(150)

    assert walls == [WallSide.RIGHT]
    assert ball.physics.x_speed < 0


@pytest.mark.parametrize("wall_event", ["touching", "stopped touching"])
def test_wall_callbacks_survive_another_sprite_starting_physics_later(wall_event):
    ball = play.new_circle(radius=10)
    paddle = play.new_box(x=-300, width=20, height=100)
    ball.start_physics(x_speed=300, obeys_gravity=False)
    walls = []

    if wall_event == "touching":
        ball.when_touching_wall(lambda: walls.append("wall"))
    else:
        ball.when_stopped_touching_wall(lambda: walls.append("wall"))

    @ball.when_touching(paddle)
    def hit():
        pass

    paddle.start_physics(can_move=False)

    _run_frames(120)

    assert walls == ["wall"]
