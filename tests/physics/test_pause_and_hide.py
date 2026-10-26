import pytest

import play

STOP_AND_GO = {
    "hide and show": (lambda ball: ball.hide(), lambda ball: ball.show()),
    "pause and unpause": (
        lambda ball: ball.physics.pause(),
        lambda ball: ball.physics.unpause(),
    ),
}


@pytest.mark.parametrize("stop_and_go", STOP_AND_GO)
def test_a_sprite_stands_still_while_stopped_and_moves_on_from_there(stop_and_go):
    stop, go = STOP_AND_GO[stop_and_go]
    num_frames = [0]
    data = []
    expected = (
        [0]
        + list(range(1, 25))
        + [25 for _ in range(25)]
        + list(range(25, 50))
        + [50 for _ in range(26)]
    )

    ball = play.new_circle(color="gray", radius=100)
    ball.start_physics(y_speed=60, obeys_gravity=False)
    data.append(ball.y)

    @play.repeat_forever
    def move():
        num_frames[0] += 1
        data.append(round(ball.y))
        if num_frames[0] in (25, 75):
            stop(ball)
        elif num_frames[0] == 50:
            go(ball)
        elif num_frames[0] == 100:
            play.stop_program()

    play.start_program()

    assert data == expected


@pytest.mark.parametrize("stop_and_go", STOP_AND_GO)
def test_stopping_or_starting_a_sprite_twice_is_the_same_as_once(stop_and_go):
    stop, go = STOP_AND_GO[stop_and_go]
    ball = play.new_circle(radius=10)
    ball.start_physics(y_speed=60, obeys_gravity=False)

    frames = [0]
    stop(ball)
    stop(ball)

    @play.repeat_forever
    def start_later():
        frames[0] += 1
        if frames[0] == 30:
            go(ball)
            go(ball)
        if frames[0] == 60:
            play.stop_program()

    play.start_program()

    assert ball.y == pytest.approx(30, abs=1)
