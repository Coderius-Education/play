"""Shared helpers for tests/projects/ — reduces boilerplate across pong variants."""


def setup_pong(ball_x_speed=300, ball_y_speed=40, ball_obeys_gravity=False):
    """Create the standard pong sprites and start their physics.

    Returns a namespace with: ball, paddle_left, paddle_right, score_text.
    """
    import play

    ball = play.new_circle(color="black", x=0, y=0, radius=10)
    paddle_left = play.new_box(color="blue", x=-350, y=0, width=15, height=80)
    paddle_right = play.new_box(color="red", x=350, y=0, width=15, height=80)
    score_text = play.new_text(words="0 - 0", x=0, y=260, font_size=30)

    ball.start_physics(
        obeys_gravity=ball_obeys_gravity,
        x_speed=ball_x_speed,
        y_speed=ball_y_speed,
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

    return ball, paddle_left, paddle_right, score_text


def add_pong_scoring(
    ball,
    score_left,
    score_right,
    score_text,
    ball_x_speed=300,
    ball_y_speed=40,
    winning_score=1,
    on_score=None,
):
    """Register the standard wall-scoring callbacks on the ball.

    on_score(side) is called after each score (side = "left" or "right")
    but before the win-check, for tests that need extra logic (e.g.
    highscore tracking, serve delays).
    """
    import play
    from play.callback.collision_callbacks import WallSide

    @ball.when_stopped_touching_wall(wall=WallSide.LEFT)
    def right_player_scores():
        score_right[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        if on_score:
            on_score("right")
        if score_right[0] >= winning_score:
            play.stop_program()
            return
        ball.x = 0
        ball.y = 0
        ball.physics.x_speed = ball_x_speed
        ball.physics.y_speed = ball_y_speed

    @ball.when_stopped_touching_wall(wall=WallSide.RIGHT)
    def left_player_scores():
        score_left[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        if on_score:
            on_score("left")
        if score_left[0] >= winning_score:
            play.stop_program()
            return
        ball.x = 0
        ball.y = 0
        ball.physics.x_speed = -ball_x_speed
        ball.physics.y_speed = -ball_y_speed


def add_safety_timeout(max_frames):
    """Register a when_program_starts safety timeout."""
    import play

    @play.when_program_starts
    async def safety_timeout():
        for _ in range(max_frames):
            await play.animate()
        play.stop_program()


def assert_pong_winner(score_left, score_right, winning_score):
    """Standard assertions: someone won, total score is sane."""
    total = score_left[0] + score_right[0]
    assert (
        total >= winning_score
    ), f"expected at least {winning_score} total points, got {total}"
    assert score_left[0] >= winning_score or score_right[0] >= winning_score, (
        f"expected one player to reach {winning_score}, "
        f"scores were {score_left[0]} - {score_right[0]}"
    )
