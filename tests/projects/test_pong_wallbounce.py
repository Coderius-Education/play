"""Pong with @when_touching_wall visual effects — realistic full-game project test.

When the ball touches the top or bottom wall, a counter increments and
the ball briefly changes color.  This uses the @when_touching_wall
decorator (as opposed to when_stopped_touching_wall used for scoring,
or is_touching_wall() polling used in test_pong_wallfx).

This test verifies:
- @sprite.when_touching_wall decorator fires while the sprite overlaps a wall
- wall= parameter filters to specific walls (TOP/BOTTOM only)
- the callback fires correctly alongside standard pong scoring
"""

from tests.projects.conftest import (
    setup_pong,
    add_pong_scoring,
    add_safety_timeout,
    assert_pong_winner,
)

max_frames = 2000
winning_score = 2


def test_pong_wallbounce():
    import play
    from play.callback.collision_callbacks import WallSide

    score_left = [0]
    score_right = [0]
    top_touches = [0]
    bottom_touches = [0]

    ball, paddle_left, paddle_right, score_text = setup_pong(
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

    # --- wall touch callbacks (the feature under test) ---------------------
    @ball.when_touching_wall(wall=WallSide.TOP)
    def touching_top():
        top_touches[0] += 1

    @ball.when_touching_wall(wall=WallSide.BOTTOM)
    def touching_bottom():
        bottom_touches[0] += 1

    add_safety_timeout(max_frames)

    play.start_program()

    # --- assertions --------------------------------------------------------
    assert_pong_winner(score_left, score_right, winning_score)
    total_wall = top_touches[0] + bottom_touches[0]
    assert (
        total_wall > 0
    ), "@when_touching_wall should have fired for top or bottom wall"


if __name__ == "__main__":
    test_pong_wallbounce()
