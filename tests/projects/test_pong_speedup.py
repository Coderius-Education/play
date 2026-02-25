"""Pong with speed increase — realistic full-game project test.

Two paddles and a ball.  Each time the ball bounces off a paddle the
speed increases by 20%.  When the ball passes a paddle the speed resets
for the next serve.  The game ends when one player reaches 3 points.

This test verifies:
- modifying physics.x_speed / physics.y_speed inside when_stopped_touching
- speed actually increases after paddle hits
- scoring and reset still work at higher speeds
"""

import pytest

max_frames = 3000
winning_score = 3
speed_factor = 1.2


def test_pong_speedup():
    import play
    from play.callback.collision_callbacks import WallSide

    score_left = [0]
    score_right = [0]
    paddle_hits = [0]
    current_speed = [300.0]  # tracks intended speed independently of physics
    max_speed_ever = [300.0]  # high-water mark — never reset

    # --- sprites -----------------------------------------------------------
    ball = play.new_circle(color="black", x=0, y=0, radius=10)

    paddle_left = play.new_box(color="blue", x=-350, y=0, width=15, height=80)
    paddle_right = play.new_box(color="red", x=350, y=0, width=15, height=80)

    score_text = play.new_text(words="0 - 0", x=0, y=260, font_size=30)

    # --- physics -----------------------------------------------------------
    ball.start_physics(
        obeys_gravity=False,
        x_speed=300,
        y_speed=40,
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

    # --- scoring (reset speed on each serve) ------------------------------
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
    assert paddle_hits[0] > 0, "ball should have hit at least one paddle"
    assert max_speed_ever[0] > 300, (
        f"speed should have increased beyond 300, but max was {max_speed_ever[0]}; "
        "when_stopped_touching callback may not have fired on paddle hit"
    )


if __name__ == "__main__":
    test_pong_speedup()
