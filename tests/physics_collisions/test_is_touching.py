import pytest


def test_ball_movement():
    import play

    num_frames = [0]
    max_frames = 200
    x_speed = 60
    num_collisions_decorator = [0]
    method_check_inside_decorator = [0]

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
    batje.start_physics(
        obeys_gravity=False, can_move=False, friction=0, mass=10, bounciness=1.0
    )

    @ball.when_touching(batje)
    def detect_collision():
        num_collisions_decorator[0] += 1
        if ball.is_touching(batje):
            method_check_inside_decorator[0] += 1

    @play.repeat_forever
    def move():
        num_frames[0] += 1

        if num_frames[0] == max_frames:
            play.stop_program()

    play.start_program()

    if not (num_collisions_decorator[0] == 2 and method_check_inside_decorator[0] == 2):
        pytest.fail(
            f"expected two collisions by the method and the decorator, but found {num_collisions_decorator[0]}, {method_check_inside_decorator[0]}"
        )


if __name__ == "__main__":
    test_ball_movement()
