"""Pong with multiple balls — realistic full-game project test.

Two paddles and two balls in play simultaneously.  Each ball has its own
when_stopped_touching callbacks for both paddles.  This stress-tests the
collision registry fix that allows multiple when_stopped_touching
registrations on the same sprite for different targets.

This test verifies:
- four when_stopped_touching registrations (2 balls x 2 paddles), with each
  ball's paddle contacts asserted separately
- two independent balls bouncing and scoring
- when_stopped_touching_wall scoring with ball identification

Both balls are served on a line that meets a paddle. The point of the test is
that four separate registrations all work, so each ball has to demonstrably
reach a paddle; a summed `ball1 + ball2 > 0` assertion passed with the second
ball completely inert, and the serves were in fact aimed past the paddles.
"""

from tests.projects.conftest import (
    add_safety_timeout,
    assert_pong_winner,
    new_scoring_state,
)

max_frames = 1500
winning_score = 2


def test_pong_multiballs():
    import play
    from play.callback.collision_callbacks import WallSide

    score_left = [0]
    score_right = [0]
    ball1_paddle_hits = [0]
    ball2_paddle_hits = [0]

    # --- sprites (custom: two balls) ---------------------------------------
    ball1 = play.new_circle(color="black", x=0, y=50, radius=10)
    ball2 = play.new_circle(color="black", x=0, y=-50, radius=10)

    paddle_left = play.new_box(color="blue", x=-350, y=0, width=15, height=80)
    paddle_right = play.new_box(color="red", x=350, y=0, width=15, height=80)

    score_text = play.new_text(words="0 - 0", x=0, y=260, font_size=30)
    scoring = new_scoring_state(score_text)

    # --- physics -----------------------------------------------------------
    # ball1 reaches x=350 after 1.17s, by which time y has fallen 50 -> 15:
    # inside paddle_right's -40..40.
    ball1.start_physics(
        obeys_gravity=False,
        x_speed=300,
        y_speed=-30,
        friction=0,
        mass=10,
        bounciness=1.0,
    )
    # ball2 reaches x=-350 after 1.4s, by which time y has risen -50 -> -8:
    # inside paddle_left's -40..40.
    ball2.start_physics(
        obeys_gravity=False,
        x_speed=-250,
        y_speed=30,
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

    # --- ball 1 paddle collisions ------------------------------------------
    @ball1.when_stopped_touching(paddle_left)
    def ball1_leaves_left():
        ball1_paddle_hits[0] += 1

    @ball1.when_stopped_touching(paddle_right)
    def ball1_leaves_right():
        ball1_paddle_hits[0] += 1

    # --- ball 2 paddle collisions ------------------------------------------
    @ball2.when_stopped_touching(paddle_left)
    def ball2_leaves_left():
        ball2_paddle_hits[0] += 1

    @ball2.when_stopped_touching(paddle_right)
    def ball2_leaves_right():
        ball2_paddle_hits[0] += 1

    # --- scoring (either ball hitting a side wall scores) ------------------
    def _reset_ball(ball, direction):
        ball.x = 0
        ball.y = 0
        ball.physics.x_speed = 300 * direction
        ball.physics.y_speed = 30 * direction

    @ball1.when_stopped_touching_wall(wall=WallSide.LEFT)
    def ball1_scores_right():
        score_right[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        _reset_ball(ball1, 1)
        if score_right[0] >= winning_score:
            scoring["won"] = True
            play.stop_program()

    @ball1.when_stopped_touching_wall(wall=WallSide.RIGHT)
    def ball1_scores_left():
        score_left[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        _reset_ball(ball1, -1)
        if score_left[0] >= winning_score:
            scoring["won"] = True
            play.stop_program()

    @ball2.when_stopped_touching_wall(wall=WallSide.LEFT)
    def ball2_scores_right():
        score_right[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        _reset_ball(ball2, 1)
        if score_right[0] >= winning_score:
            scoring["won"] = True
            play.stop_program()

    @ball2.when_stopped_touching_wall(wall=WallSide.RIGHT)
    def ball2_scores_left():
        score_left[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        _reset_ball(ball2, -1)
        if score_left[0] >= winning_score:
            scoring["won"] = True
            play.stop_program()

    add_safety_timeout(max_frames)

    play.start_program()

    assert_pong_winner(score_left, score_right, winning_score, scoring)
    # Per ball, not summed: four separate registrations are the thing under
    # test, so a ball that never reaches a paddle has to fail.
    assert ball1_paddle_hits[0] > 0, "ball1 never registered a paddle contact"
    assert ball2_paddle_hits[0] > 0, "ball2 never registered a paddle contact"


if __name__ == "__main__":
    test_pong_multiballs()
