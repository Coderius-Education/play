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
    # distance_to() is dominated by the fixed x-gap between paddle and ball,
    # so it cannot show whether the AI tracks. Sample the vertical error too.
    y_errors = []

    ball, paddle_left, paddle_right, score_text = setup_pong()

    # --- AI: right paddle tracks ball each frame ---------------------------
    @play.repeat_forever
    def ai_paddle():
        dist = paddle_right.distance_to(ball)
        if len(distances_measured) < 100:
            distances_measured.append(dist)
        y_errors.append(abs(ball.y - paddle_right.y))

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

    scoring = add_pong_scoring(
        ball, score_left, score_right, score_text, winning_score=winning_score
    )
    add_safety_timeout(max_frames)

    play.start_program()

    # --- assertions --------------------------------------------------------
    assert_pong_winner(score_left, score_right, winning_score, scoring)
    assert ai_moves[0] > 0, "AI paddle should have moved via repeat_forever"
    assert len(distances_measured) > 0, "distance_to() should have been called"
    assert all(
        d >= 0 for d in distances_measured
    ), "distance_to() should return non-negative values"
    # The old check here was `distances_measured[-1] != distances_measured[0]`,
    # which is true for any moving ball even if the AI paddle never moved.
    # Assert the tracking itself: the paddle stays level with the ball for most
    # frames. Allow the tail of frames after a score, where the ball teleports
    # back to the centre and the paddle has to catch up.
    close_frames = sum(1 for e in y_errors if e < 30)
    assert close_frames > len(y_errors) * 0.5, (
        "the AI paddle should stay within 30px of the ball for most frames; "
        f"it managed {close_frames} of {len(y_errors)}"
    )


if __name__ == "__main__":
    test_pong_ai()
