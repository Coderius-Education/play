"""Pong with obstacles — realistic full-game project test.

Two paddles (left/right) and a ball, but with a static obstacle in the
centre of the field.  The ball bounces off the obstacle, the paddles,
and the walls.  This exercises three when_stopped_touching callbacks on
the same ball (left paddle, right paddle, obstacle).

This test verifies:
- three when_stopped_touching registrations on one sprite
- obstacle deflections change the ball's path
- scoring still works via when_stopped_touching_wall
"""

from tests.projects.conftest import (
    setup_pong,
    add_pong_scoring,
    add_safety_timeout,
    assert_pong_winner,
)

max_frames = 4000
winning_score = 3


def test_pong_obstacles():
    import play

    score_left = [0]
    score_right = [0]
    obstacle_hits = [0]

    ball, paddle_left, paddle_right, score_text = setup_pong(ball_y_speed=60)

    # extra obstacle sprite
    obstacle = play.new_box(color="gray", x=0, y=0, width=30, height=120)
    obstacle.start_physics(
        obeys_gravity=False, can_move=False, friction=0, mass=10, bounciness=1.0
    )

    # --- collisions --------------------------------------------------------
    @ball.when_stopped_touching(paddle_left)
    def ball_leaves_left_paddle():
        pass

    @ball.when_stopped_touching(paddle_right)
    def ball_leaves_right_paddle():
        pass

    @ball.when_stopped_touching(obstacle)
    def ball_leaves_obstacle():
        obstacle_hits[0] += 1

    add_pong_scoring(
        ball,
        score_left,
        score_right,
        score_text,
        ball_y_speed=60,
        winning_score=winning_score,
    )
    add_safety_timeout(max_frames)

    play.start_program()

    assert_pong_winner(score_left, score_right, winning_score)
    assert obstacle_hits[0] > 0, "ball should have hit the obstacle at least once"


if __name__ == "__main__":
    test_pong_obstacles()
