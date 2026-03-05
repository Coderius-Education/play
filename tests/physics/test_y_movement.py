import pytest


def test_ball_movement():
    import play

    max_frames = 100
    y_speed = 60
    y_data = []
    num_frames = [0]

    ball = play.new_circle(color="gray", radius=10)
    ball.start_physics(
        obeys_gravity=False, bounciness=0, stable=False, friction=1, y_speed=y_speed
    )

    y_data.append(ball.y)

    @play.repeat_forever
    def move():
        num_frames[0] += 1

        y_data.append(ball.y)

        if num_frames[0] == max_frames:
            play.stop_program()

    play.start_program()

    for index, y_position in enumerate(y_data):
        actual_value = round(y_position)
        expected_value = index
        print(actual_value, expected_value)
        if actual_value != expected_value:
            pytest.fail(
                f"expected ball.y to be {expected_value} but the y value is {actual_value}"
            )


if __name__ == "__main__":
    test_ball_movement()
