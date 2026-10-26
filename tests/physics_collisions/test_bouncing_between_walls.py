from itertools import groupby

import play


def test_a_ball_bounces_off_the_right_then_the_left_wall_staying_level_at_full_speed():
    num_frames = [0]
    speeds = []
    heights = []

    ball = play.new_circle(color="gray", radius=10)
    ball.start_physics(x_speed=300, obeys_gravity=False, bounciness=1, friction=0)

    @play.repeat_forever
    def move():
        num_frames[0] += 1
        speeds.append(ball.physics.x_speed)
        heights.append(ball.y)
        if num_frames[0] == 300:
            play.stop_program()

    play.start_program()

    assert set(heights) == {0}
    going_right = [right for right, _ in groupby(speed > 0 for speed in speeds)]
    assert going_right == [True, False, True]
    assert {round(abs(speed)) for speed in speeds} == {300}
