import pytest

num_frames = 0
max_frames = 200
x_speed = 300

num_collisions_decorator = 0


def test_ball_movement():
    import sys

    sys.path.insert(0, ".")
    import play

    ball = play.new_circle(
        color="black",
        x=0,
        y=0,
        radius=20,
    )

    ball.start_physics(
        obeys_gravity=False, x_speed=x_speed, friction=0, mass=10, bounciness=1.0
    )

    @ball.when_stopped_touching_wall
    def detect_collision():
        global num_collisions_decorator
        num_collisions_decorator += 1

    @play.repeat_forever
    def move():
        global num_frames
        num_frames += 1

        if num_frames == max_frames:
            play.stop_program()

    play.start_program()

    if not (num_collisions_decorator == 1):
        pytest.fail(
            f"expected one collision by the decorator, but found, {num_collisions_decorator}"
        )


if __name__ == "__main__":
    test_ball_movement()
