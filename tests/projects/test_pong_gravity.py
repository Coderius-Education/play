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

max_frames = 1500
winning_score = 1


def test_pong_gravity():
    from play.physics import set_gravity

    score_left = [0]
    score_right = [0]
    early_x_speed = []

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

    scoring = add_pong_scoring(
        ball,
        score_left,
        score_right,
        score_text,
        ball_x_speed=200,
        ball_y_speed=80,
        winning_score=winning_score,
    )
    import play

    @play.when_program_starts
    async def measure_the_pull():
        for _ in range(30):
            await play.animate()
        early_x_speed.append(ball.physics.x_speed)

    add_safety_timeout(max_frames)

    play.start_program()

    # --- assertions --------------------------------------------------------
    assert_pong_winner(score_left, score_right, winning_score, scoring)
    assert early_x_speed[0] > 210, (
        "rightward gravity should speed up a ball served to the right, "
        f"but after half a second its x speed was {early_x_speed[0]:.0f}"
    )
    assert (
        score_left[0] > 0
    ), "with rightward gravity, left player should have scored at least once"


if __name__ == "__main__":
    test_pong_gravity()
