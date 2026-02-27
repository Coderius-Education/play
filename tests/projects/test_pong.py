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

from tests.projects.conftest import (
    setup_pong,
    add_pong_scoring,
    add_safety_timeout,
    assert_pong_winner,
)

max_frames = 1500
winning_score = 1


def test_pong():
    score_left = [0]
    score_right = [0]
    ball_paddle_hits = [0]

    ball, paddle_left, paddle_right, score_text = setup_pong()

    # --- paddle–ball collisions --------------------------------------------
    @ball.when_stopped_touching(paddle_left)
    def ball_leaves_left_paddle():
        ball_paddle_hits[0] += 1

    @ball.when_stopped_touching(paddle_right)
    def ball_leaves_right_paddle():
        ball_paddle_hits[0] += 1

    add_pong_scoring(
        ball, score_left, score_right, score_text, winning_score=winning_score
    )
    add_safety_timeout(max_frames)

    import play

    play.start_program()

    assert_pong_winner(score_left, score_right, winning_score)
    assert ball_paddle_hits[0] > 0, "ball should have hit at least one paddle"


if __name__ == "__main__":
    test_pong()
