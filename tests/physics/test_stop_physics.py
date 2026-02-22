import pytest

num_frames = 0
max_frames = 75

data = []
# Ball moves up for 25 frames (y increases by 1 per frame at y_speed=60)
# Then stop_physics is called - ball should stop moving
# Expected: 0, 1, 2, ..., 24, 25, 25, 25, ... (stays at 25 for remaining frames)
expected = list(range(0, 26)) + [25 for _ in range(50)]


def test_stop_physics():

    import play

    ball = play.new_circle(
        color="gray",
        x=0,
        y=0,
        radius=50,
    )
    ball.start_physics(y_speed=60, obeys_gravity=False)

    data.append(ball.y)

    @play.repeat_forever
    def move():
        global num_frames
        global data

        num_frames += 1
        data.append(round(ball.y))

        if num_frames == 25:
            ball.stop_physics()

        if num_frames == max_frames:
            play.stop_program()

    play.start_program()

    for i, (expected_value, actual_value) in enumerate(zip(expected, data)):
        if expected_value != actual_value:
            pytest.fail(
                f"Frame {i}: expected ball.y to be {expected_value} but got {actual_value}"
            )


def test_stop_physics_removes_gravity():
    """Test that stop_physics disables gravity."""
    global frames

    import play

    ball = play.new_circle(x=0, y=100, radius=50)
    ball.start_physics(obeys_gravity=True)

    initial_y = ball.y
    frames = 0
    max_test_frames = 10
    y_values = [initial_y]

    @play.repeat_forever
    def check():
        global frames
        frames += 1
        y_values.append(round(ball.y))

        if frames == 5:
            ball.stop_physics()

        if frames == max_test_frames:
            play.stop_program()

    play.start_program()

    # After stop_physics, y should remain constant
    y_after_stop = y_values[6]
    for i in range(7, len(y_values)):
        if y_values[i] != y_after_stop:
            pytest.fail(
                f"Frame {i}: ball should stay at y={y_after_stop} after stop_physics, but got {y_values[i]}"
            )


if __name__ == "__main__":
    test_stop_physics()
