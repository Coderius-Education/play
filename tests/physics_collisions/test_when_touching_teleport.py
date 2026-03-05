import pytest


def test_ball_movement():
    import play

    num_frames = [0]
    max_frames = 200
    x_speed = 60
    num_collisions = [0]
    expected_num_collisions = 1

    ball = play.new_circle(
        color="black",
        x=0,
        y=0,
        radius=20,
    )
    batje = play.new_box(color="black", x=200)

    ball.start_physics(
        obeys_gravity=False, x_speed=x_speed, friction=0, mass=10, bounciness=1.0
    )
    batje.start_physics(obeys_gravity=False, can_move=False, friction=0, mass=10)

    @play.repeat_forever
    def move():
        num_frames[0] += 1

        if num_frames[0] == max_frames:
            play.stop_program()

    @ball.when_touching(batje)
    def detect_collision():
        num_collisions[0] += 1
        ball.x = 0

    play.start_program()

    if num_collisions[0] != expected_num_collisions:
        pytest.fail(
            f"expected exactly one collision event, but found {num_collisions[0]}"
        )


if __name__ == "__main__":
    test_ball_movement()
