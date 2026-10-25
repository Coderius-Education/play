import play


def test_a_ball_bouncing_between_the_side_walls_stays_level_and_keeps_its_speed():
    num_frames = [0]
    speeds = []
    heights = []

    ball = play.new_circle(color="gray", radius=10)
    ball.start_physics(x_speed=60, obeys_gravity=False, bounciness=1, friction=0)

    @play.repeat_forever
    def move():
        num_frames[0] += 1
        speeds.append(ball.physics.x_speed)
        heights.append(ball.y)
        if num_frames[0] == 1000:
            play.stop_program()

    play.start_program()

    assert set(heights) == {0}
    assert speeds[0] == 60
    assert min(speeds) < 0
    assert {abs(round(speed, 1)) for speed in speeds} == {60}
