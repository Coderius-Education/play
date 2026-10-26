import pytest

import play


def _ball_after_a_second(sim_steps):
    """A ball moving 60 px/s after 60 frames at *sim_steps* simulation steps."""
    play.set_physics_simulation_steps(sim_steps)
    ball = play.new_circle(radius=10)
    ball.start_physics(x_speed=60, obeys_gravity=False)
    frames = [0]

    @play.repeat_forever
    def stop_later():
        frames[0] += 1
        if frames[0] == 60:
            play.stop_program()

    play.start_program()
    return ball


@pytest.mark.parametrize("sim_steps", [1, 3, 10, 20])
def test_more_simulation_steps_do_not_make_sprites_faster(sim_steps):
    ball = _ball_after_a_second(sim_steps)
    assert ball.x == pytest.approx(60)


@pytest.mark.parametrize("sim_steps", [0, -1])
def test_no_simulation_steps_freezes_physics(sim_steps):
    ball = _ball_after_a_second(sim_steps)
    assert ball.x == 0
