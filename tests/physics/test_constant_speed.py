import pytest

import play


def _positions_per_frame(sprite, axis, frames, each_frame=None):
    positions = [getattr(sprite, axis)]
    counted = [0]

    @play.repeat_forever
    def record():
        counted[0] += 1
        positions.append(round(getattr(sprite, axis), 6))
        if each_frame:
            each_frame(counted[0])
        if counted[0] == frames:
            play.stop_program()

    play.start_program()
    return positions


@pytest.mark.parametrize("axis", ["x", "y"])
def test_a_sprite_moves_its_speed_in_pixels_every_second(axis):
    ball = play.new_circle(color="gray", radius=10)
    ball.start_physics(
        obeys_gravity=False,
        bounciness=0,
        stable=False,
        friction=1,
        **{f"{axis}_speed": 60},
    )

    positions = _positions_per_frame(ball, axis, 100)

    assert [round(position) for position in positions] == list(range(101))


@pytest.mark.parametrize("axis, other", [("x", "y"), ("y", "x")])
def test_setting_one_speed_mid_game_keeps_the_other(axis, other):
    ball = play.new_circle(radius=10)
    ball.start_physics(obeys_gravity=False, **{f"{other}_speed": 60})

    def speed_up(frame):
        if frame == 10:
            setattr(ball.physics, f"{axis}_speed", 120)

    other_positions = _positions_per_frame(ball, other, 30, speed_up)

    assert getattr(ball.physics, f"{axis}_speed") == pytest.approx(120)
    assert getattr(ball.physics, f"{other}_speed") == pytest.approx(60)
    assert [round(position) for position in other_positions] == list(range(31))
    assert getattr(ball, axis) == pytest.approx(20 * 2, abs=0.01)
