"""Pong — realistic full-game project test.

Two paddles (left/right), a ball that bounces between them at high speed.
The ball starts in the centre and moves diagonally.  When it hits a paddle
it bounces back.  When it passes a paddle and hits the left or right wall
the other player scores a point.  The game ends when one player reaches 3
points.

This test verifies:
- high x_speed / y_speed ball movement with wall bouncing
- paddle–ball collisions via when_stopped_touching callbacks
- score tracking via when_stopped_touching_wall callbacks
- the game stops after the win condition is met
"""

max_frames = 3000
winning_score = 3


def test_pong():
    import play
    from play.callback.collision_callbacks import WallSide

    score_left = [0]
    score_right = [0]
    ball_paddle_hits = [0]

    # --- sprites -----------------------------------------------------------
    ball = play.new_circle(color="black", x=0, y=0, radius=10)

    paddle_left = play.new_box(color="blue", x=-350, y=0, width=15, height=80)
    paddle_right = play.new_box(color="red", x=350, y=0, width=15, height=80)

    score_text = play.new_text(words="0 - 0", x=0, y=260, font_size=30)

    # --- physics -----------------------------------------------------------
    ball.start_physics(
        obeys_gravity=False,
        x_speed=300,
        y_speed=40,
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

    # --- paddle–ball collisions --------------------------------------------
    @ball.when_stopped_touching(paddle_left)
    def ball_leaves_left_paddle():
        ball_paddle_hits[0] += 1

    @ball.when_stopped_touching(paddle_right)
    def ball_leaves_right_paddle():
        ball_paddle_hits[0] += 1

    # --- scoring via wall callbacks ----------------------------------------
    @ball.when_stopped_touching_wall(wall=WallSide.LEFT)
    def right_player_scores():
        score_right[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        ball.x = 0
        ball.y = 0
        ball.physics.x_speed = 300
        ball.physics.y_speed = 40
        if score_right[0] >= winning_score:
            play.stop_program()

    @ball.when_stopped_touching_wall(wall=WallSide.RIGHT)
    def left_player_scores():
        score_left[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        ball.x = 0
        ball.y = 0
        ball.physics.x_speed = -300
        ball.physics.y_speed = -40
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
    ), f"expected at least {winning_score} total points scored, got {total_score}"
    assert score_left[0] >= winning_score or score_right[0] >= winning_score, (
        f"expected one player to reach {winning_score}, "
        f"scores were {score_left[0]} - {score_right[0]}"
    )
    assert ball_paddle_hits[0] > 0, "ball should have hit at least one paddle"


if __name__ == "__main__":
    test_pong()
