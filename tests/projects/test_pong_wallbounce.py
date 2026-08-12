"""Pong with @when_touching_wall visual effects — realistic full-game project test.

When the ball touches the top or bottom wall a counter increments.  This uses
the @when_touching_wall decorator, as opposed to when_stopped_touching_wall
used for scoring.

This test verifies:
- @sprite.when_touching_wall decorator fires while the sprite overlaps a wall
- wall= parameter filters to specific walls, with TOP and BOTTOM asserted
  separately so that one working filter cannot cover for a broken one
- the callback fires correctly alongside standard pong scoring

The serve is steep and slow on purpose.  With the usual fast, flat pong serve
the ball reaches a side wall and scores before it has climbed anywhere near
the top of the screen, so neither wall filter gets a chance to fire; a summed
`top + bottom > 0` assertion hid that.  At 80px/s across and 450px/s up the
ball crosses the full height twice before it crosses the width once.
"""

from tests.projects.conftest import (
    setup_pong,
    add_pong_scoring,
    add_safety_timeout,
    assert_pong_winner,
)

max_frames = 1500  # 25s at 60fps; pytest's timeout is 60s
winning_score = 1
BALL_X_SPEED = 80
BALL_Y_SPEED = 450


def test_pong_wallbounce():
    import play
    from play.callback.collision_callbacks import WallSide

    score_left = [0]
    score_right = [0]
    top_touches = [0]
    bottom_touches = [0]

    ball, paddle_left, paddle_right, score_text = setup_pong(
        ball_x_speed=BALL_X_SPEED,
        ball_y_speed=BALL_Y_SPEED,
    )

    # --- collisions --------------------------------------------------------
    @ball.when_stopped_touching(paddle_left)
    def ball_leaves_left():
        pass

    @ball.when_stopped_touching(paddle_right)
    def ball_leaves_right():
        pass

    scoring = add_pong_scoring(
        ball,
        score_left,
        score_right,
        score_text,
        ball_x_speed=BALL_X_SPEED,
        ball_y_speed=BALL_Y_SPEED,
        winning_score=winning_score,
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
    assert_pong_winner(score_left, score_right, winning_score, scoring)
    assert top_touches[0] > 0, "@when_touching_wall(wall=TOP) never fired"
    assert bottom_touches[0] > 0, "@when_touching_wall(wall=BOTTOM) never fired"


if __name__ == "__main__":
    test_pong_wallbounce()
