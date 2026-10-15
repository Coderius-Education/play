import pytest


def test_ball_movement():
    import play

    num_frames = [0]
    max_frames = 400
    x_speed = 60
    num_collisions = [0]
    expected_num_collisions = 1

    ball = play.new_circle(
        color="black",
        x=0,
        y=0,
        radius=20,
    )
    ball.start_physics(
        obeys_gravity=False, x_speed=x_speed, friction=0, mass=10, bounciness=1.0
    )

    @play.repeat_forever
    def move():
        num_frames[0] += 1

        if num_frames[0] == max_frames:
            play.stop_program()

    @ball.when_touching_wall
    def detect_collision():
        num_collisions[0] += 1

    play.start_program()

    if num_collisions[0] != expected_num_collisions:
        pytest.fail(
            f"expected exactly one collision event, but found {num_collisions[0]}"
        )


@pytest.mark.parametrize("wall_event", ["touching", "stopped touching"])
def test_wall_callbacks_survive_another_sprite_starting_physics_later(wall_event):
    import play

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

    frames = [0]

    @play.repeat_forever
    def stop_later():
        frames[0] += 1
        if frames[0] == 120:
            play.stop_program()

    play.start_program()

    assert walls


if __name__ == "__main__":
    test_ball_movement()
