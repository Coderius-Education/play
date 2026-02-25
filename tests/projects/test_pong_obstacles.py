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

import pytest

max_frames = 3000
winning_score = 3


def test_pong_obstacles():
    import play
    from play.callback.collision_callbacks import WallSide

    score_left = [0]
    score_right = [0]
    paddle_hits = [0]
    obstacle_hits = [0]

    # --- sprites -----------------------------------------------------------
    ball = play.new_circle(color="black", x=0, y=0, radius=10)

    paddle_left = play.new_box(color="blue", x=-350, y=0, width=15, height=80)
    paddle_right = play.new_box(color="red", x=350, y=0, width=15, height=80)

    obstacle = play.new_box(color="gray", x=0, y=0, width=30, height=120)

    score_text = play.new_text(words="0 - 0", x=0, y=260, font_size=30)

    # --- physics -----------------------------------------------------------
    ball.start_physics(
        obeys_gravity=False,
        x_speed=300,
        y_speed=60,
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
    obstacle.start_physics(
        obeys_gravity=False, can_move=False, friction=0, mass=10, bounciness=1.0
    )

    # --- collisions --------------------------------------------------------
    @ball.when_stopped_touching(paddle_left)
    def ball_leaves_left_paddle():
        paddle_hits[0] += 1

    @ball.when_stopped_touching(paddle_right)
    def ball_leaves_right_paddle():
        paddle_hits[0] += 1

    @ball.when_stopped_touching(obstacle)
    def ball_leaves_obstacle():
        obstacle_hits[0] += 1

    # --- scoring -----------------------------------------------------------
    @ball.when_stopped_touching_wall(wall=WallSide.LEFT)
    def right_player_scores():
        score_right[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        ball.x = 0
        ball.y = 0
        ball.physics.x_speed = 300
        ball.physics.y_speed = 60
        if score_right[0] >= winning_score:
            play.stop_program()

    @ball.when_stopped_touching_wall(wall=WallSide.RIGHT)
    def left_player_scores():
        score_left[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        ball.x = 0
        ball.y = 0
        ball.physics.x_speed = -300
        ball.physics.y_speed = -60
        if score_left[0] >= winning_score:
            play.stop_program()

    # --- safety timeout ----------------------------------------------------
    @play.when_program_starts
    async def safety_timeout():
        for _ in range(max_frames):
            await play.animate()
        play.stop_program()

    play.start_program()

    # --- assertions --------------------------------------------------------
    total_score = score_left[0] + score_right[0]
    assert (
        total_score >= winning_score
    ), f"expected at least {winning_score} total points scored, got {total_score}"
    assert score_left[0] >= winning_score or score_right[0] >= winning_score, (
        f"expected one player to reach {winning_score}, "
        f"scores were {score_left[0]} - {score_right[0]}"
    )
    assert obstacle_hits[0] > 0, "ball should have hit the obstacle at least once"


if __name__ == "__main__":
    test_pong_obstacles()
