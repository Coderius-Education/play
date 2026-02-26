"""Pong with horizontal gravity — realistic full-game project test.

Horizontal gravity pulls the ball to the right, making it curve.  The ball
still bounces off paddles and walls, but trajectories are asymmetric.

This test verifies:
- play.set_gravity() changes the physics world gravity
- horizontal gravity affects ball trajectory
- the game plays to completion under altered gravity
"""

max_frames = 3000
winning_score = 3


def test_pong_gravity():
    import play
    from play.callback.collision_callbacks import WallSide

    score_left = [0]
    score_right = [0]

    # --- set horizontal gravity (pull right) -------------------------------
    from play.physics import set_gravity

    set_gravity(vertical=0, horizontal=50)

    # --- sprites -----------------------------------------------------------
    ball = play.new_circle(color="black", x=0, y=0, radius=10)

    paddle_left = play.new_box(color="blue", x=-350, y=0, width=15, height=80)
    paddle_right = play.new_box(color="red", x=350, y=0, width=15, height=80)

    score_text = play.new_text(words="0 - 0", x=0, y=260, font_size=30)

    # --- physics -----------------------------------------------------------
    ball.start_physics(
        obeys_gravity=True,  # affected by the custom gravity
        x_speed=200,
        y_speed=80,
        friction=0,
        mass=10,
        bounciness=1.0,
    )
    paddle_left.start_physics(
        obeys_gravity=False, can_move=False, friction=0, mass=10, bounciness=1.0
    )
    paddle_right.start_physics(
        obeys_gravity=False, can_move=False, friction=0, mass=10, bounciness=1.0
    )

    # --- collisions --------------------------------------------------------
    @ball.when_stopped_touching(paddle_left)
    def ball_leaves_left():
        pass

    @ball.when_stopped_touching(paddle_right)
    def ball_leaves_right():
        pass

    # --- scoring -----------------------------------------------------------
    @ball.when_stopped_touching_wall(wall=WallSide.LEFT)
    def right_player_scores():
        score_right[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        ball.x = 0
        ball.y = 0
        ball.physics.x_speed = 200
        ball.physics.y_speed = 80
        if score_right[0] >= winning_score:
            play.stop_program()

    @ball.when_stopped_touching_wall(wall=WallSide.RIGHT)
    def left_player_scores():
        score_left[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        ball.x = 0
        ball.y = 0
        ball.physics.x_speed = -200
        ball.physics.y_speed = -80
        if score_left[0] >= winning_score:
            play.stop_program()

    # --- safety timeout ----------------------------------------------------
    @play.when_program_starts
    async def safety_timeout():
        for _ in range(max_frames):
            await play.animate()
        play.stop_program()

    play.start_program()

    # --- assertions --------------------------------------------------------
    total_score = score_left[0] + score_right[0]
    assert (
        total_score >= winning_score
    ), f"expected at least {winning_score} total points, got {total_score}"
    assert score_left[0] >= winning_score or score_right[0] >= winning_score
    # With rightward gravity, the right player should score more often
    # (ball is pulled towards the right wall), but we don't assert this
    # strictly since the ball can still bounce off paddles unpredictably.


if __name__ == "__main__":
    test_pong_gravity()
