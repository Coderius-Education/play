"""Pong with wall-bounce effects — realistic full-game project test.

When the ball touches a wall it changes color briefly.  The test uses
is_touching_wall() and get_touching_walls() each frame to detect wall
contact — the most common polling-style approach students use instead of
(or in addition to) callback-based wall events.

This test verifies:
- sprite.is_touching_wall() returns True when touching a wall
- sprite.get_touching_walls() returns the correct WallSide values
- polling-based wall detection works alongside callback-based scoring
- the game completes normally with per-frame wall checks
"""

from tests.projects.conftest import (
    setup_pong,
    add_pong_scoring,
    add_safety_timeout,
    assert_pong_winner,
)

max_frames = 2000
winning_score = 2


def test_pong_wallfx():
    import play

    score_left = [0]
    score_right = [0]
    wall_touches_detected = [0]
    walls_seen = set()

    ball, paddle_left, paddle_right, score_text = setup_pong(
        ball_x_speed=200,
        ball_y_speed=200,
    )

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

    # --- per-frame wall detection (polling style) --------------------------
    @play.repeat_forever
    def check_walls():
        if ball.is_touching_wall():
            wall_touches_detected[0] += 1
            touching = ball.get_touching_walls()
            for w in touching:
                walls_seen.add(w)
            # Visual effect: change ball color on wall contact
            ball.color = "red"
        else:
            ball.color = "black"

    add_safety_timeout(max_frames)

    play.start_program()

    # --- assertions --------------------------------------------------------
    assert_pong_winner(score_left, score_right, winning_score)
    assert (
        wall_touches_detected[0] > 0
    ), "is_touching_wall() should have detected at least one wall contact"
    assert (
        len(walls_seen) > 0
    ), "get_touching_walls() should have returned at least one WallSide"


if __name__ == "__main__":
    test_pong_wallfx()
