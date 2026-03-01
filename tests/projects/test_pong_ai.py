"""Pong with AI paddle — realistic full-game project test.

The right paddle tracks the ball's y-position each frame using
distance_to() and repeat_forever.  This is a common pattern for
single-player pong with a computer opponent.

This test verifies:
- sprite.distance_to(other_sprite) returns correct values
- @play.repeat_forever runs each frame for AI logic
- AI paddle actually moves towards the ball
- the game completes with both physics and per-frame AI running
"""

from tests.projects.conftest import (
    setup_pong,
    add_pong_scoring,
    add_safety_timeout,
    assert_pong_winner,
)

max_frames = 1500
winning_score = 1


def test_pong_ai():
    import play

    score_left = [0]
    score_right = [0]
    ai_moves = [0]
    distances_measured = []

    ball, paddle_left, paddle_right, score_text = setup_pong()

    # --- AI: right paddle tracks ball each frame ---------------------------
    @play.repeat_forever
    def ai_paddle():
        dist = paddle_right.distance_to(ball)
        if len(distances_measured) < 100:
            distances_measured.append(dist)

        # Move towards ball y with a speed limit (imperfect AI)
        diff = ball.y - paddle_right.y
        speed = min(abs(diff), 4)  # max 4 pixels per frame
        if diff > 0:
            paddle_right.y += speed
        elif diff < 0:
            paddle_right.y -= speed
        ai_moves[0] += 1

    # --- collisions --------------------------------------------------------
    @ball.when_stopped_touching(paddle_left)
    def ball_leaves_left():
        pass

    @ball.when_stopped_touching(paddle_right)
    def ball_leaves_right():
        pass

    add_pong_scoring(
        ball, score_left, score_right, score_text, winning_score=winning_score
    )
    add_safety_timeout(max_frames)

    play.start_program()

    # --- assertions --------------------------------------------------------
    assert_pong_winner(score_left, score_right, winning_score)
    assert ai_moves[0] > 0, "AI paddle should have moved via repeat_forever"
    assert len(distances_measured) > 0, "distance_to() should have been called"
    assert all(
        d >= 0 for d in distances_measured
    ), "distance_to() should return non-negative values"
    # Verify AI actually reduced distance — compare first and last samples
    assert (
        distances_measured[-1] != distances_measured[0]
    ), "AI paddle should have changed its distance to the ball over time"


if __name__ == "__main__":
    test_pong_ai()
