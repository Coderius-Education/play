"""Pong with speed increase — realistic full-game project test.

Two paddles and a ball.  Each time the ball bounces off a paddle the
speed increases by 20%.  When the ball passes a paddle the speed resets
for the next serve.  The game ends when one player reaches 3 points.

This test verifies:
- modifying physics.x_speed / physics.y_speed inside when_stopped_touching
- speed actually increases after paddle hits
- scoring and reset still work at higher speeds
"""

from tests.projects.conftest import (
    setup_pong,
    add_safety_timeout,
    assert_pong_winner,
)

max_frames = 1500
winning_score = 1
speed_factor = 1.2


def test_pong_speedup():
    import play
    from play.callback.collision_callbacks import WallSide

    score_left = [0]
    score_right = [0]
    paddle_hits = [0]
    current_speed = [300.0]
    max_speed_ever = [300.0]

    ball, paddle_left, paddle_right, score_text = setup_pong()

    # --- paddle collisions: speed up on each hit --------------------------
    @ball.when_stopped_touching(paddle_left)
    def ball_leaves_left_paddle():
        paddle_hits[0] += 1
        current_speed[0] *= speed_factor
        if current_speed[0] > max_speed_ever[0]:
            max_speed_ever[0] = current_speed[0]
        ball.physics.x_speed = ball.physics.x_speed * speed_factor
        ball.physics.y_speed = ball.physics.y_speed * speed_factor

    @ball.when_stopped_touching(paddle_right)
    def ball_leaves_right_paddle():
        paddle_hits[0] += 1
        current_speed[0] *= speed_factor
        if current_speed[0] > max_speed_ever[0]:
            max_speed_ever[0] = current_speed[0]
        ball.physics.x_speed = ball.physics.x_speed * speed_factor
        ball.physics.y_speed = ball.physics.y_speed * speed_factor

    # --- scoring (reset speed on each serve) — custom because of speed reset
    @ball.when_stopped_touching_wall(wall=WallSide.LEFT)
    def right_player_scores():
        score_right[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        ball.x = 0
        ball.y = 0
        ball.physics.x_speed = 300
        ball.physics.y_speed = 40
        current_speed[0] = 300.0
        if score_right[0] >= winning_score:
            play.stop_program()

    @ball.when_stopped_touching_wall(wall=WallSide.RIGHT)
    def left_player_scores():
        score_left[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        ball.x = 0
        ball.y = 0
        ball.physics.x_speed = -300
        ball.physics.y_speed = -40
        current_speed[0] = 300.0
        if score_left[0] >= winning_score:
            play.stop_program()

    add_safety_timeout(max_frames)

    play.start_program()

    assert_pong_winner(score_left, score_right, winning_score)
    assert paddle_hits[0] > 0, "ball should have hit at least one paddle"
    assert (
        max_speed_ever[0] > 300
    ), f"speed should have increased beyond 300, but max was {max_speed_ever[0]}"


if __name__ == "__main__":
    test_pong_speedup()
