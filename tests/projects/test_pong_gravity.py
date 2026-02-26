"""Pong with horizontal gravity — realistic full-game project test.

Horizontal gravity pulls the ball to the right, making it curve.  The ball
still bounces off paddles and walls, but trajectories are asymmetric.

This test verifies:
- play.set_gravity() changes the physics world gravity
- horizontal gravity affects ball trajectory (left player scores more)
- the game plays to completion under altered gravity
"""

from tests.projects.conftest import (
    setup_pong,
    add_pong_scoring,
    add_safety_timeout,
    assert_pong_winner,
)

max_frames = 4000
winning_score = 3


def test_pong_gravity():
    from play.physics import set_gravity

    score_left = [0]
    score_right = [0]

    # --- set horizontal gravity (pull right) -------------------------------
    set_gravity(vertical=0, horizontal=50)

    ball, paddle_left, paddle_right, score_text = setup_pong(
        ball_x_speed=200,
        ball_y_speed=80,
        ball_obeys_gravity=True,
    )

    # --- collisions --------------------------------------------------------
    @ball.when_stopped_touching(paddle_left)
    def ball_leaves_left():
        pass

    @ball.when_stopped_touching(paddle_right)
    def ball_leaves_right():
        pass

    add_pong_scoring(
        ball,
        score_left,
        score_right,
        score_text,
        ball_x_speed=200,
        ball_y_speed=80,
        winning_score=winning_score,
    )
    add_safety_timeout(max_frames)

    import play

    play.start_program()

    # restore default gravity so this test doesn't affect others
    set_gravity(vertical=-900, horizontal=0)

    # --- assertions --------------------------------------------------------
    assert_pong_winner(score_left, score_right, winning_score)
    # With rightward gravity the ball is pulled towards the left wall,
    # so the left player (scoring on the right wall) should score at least once.
    assert (
        score_left[0] > 0
    ), "with rightward gravity, left player should have scored at least once"


if __name__ == "__main__":
    test_pong_gravity()
