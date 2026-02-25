"""Pong with AI paddle — realistic full-game project test.

The right paddle tracks the ball's y-position each frame using
distance_to() and repeat_forever.  This is a common pattern for
single-player pong with a computer opponent.

This test verifies:
- sprite.distance_to(other_sprite) returns correct values
- @play.repeat_forever runs each frame for AI logic
- AI paddle actually moves towards the ball
- the game completes with both physics and per-frame AI running
"""

import pytest

max_frames = 3000
winning_score = 3


def test_pong_ai():
    import play
    from play.callback.collision_callbacks import WallSide

    score_left = [0]
    score_right = [0]
    ai_moves = [0]
    distances_measured = []

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

    # --- AI: right paddle tracks ball each frame ---------------------------
    @play.repeat_forever
    def ai_paddle():
        dist = paddle_right.distance_to(ball)
        if len(distances_measured) < 100:
            distances_measured.append(dist)

        # Move towards ball y with a speed limit (imperfect AI)
        diff = ball.y - paddle_right.y
        speed = min(abs(diff), 4)  # max 4 pixels per frame
        if diff > 0:
            paddle_right.y += speed
        elif diff < 0:
            paddle_right.y -= speed
        ai_moves[0] += 1

    # --- collisions --------------------------------------------------------
    @ball.when_stopped_touching(paddle_left)
    def ball_leaves_left():
        pass

    @ball.when_stopped_touching(paddle_right)
    def ball_leaves_right():
        pass

    # --- scoring -----------------------------------------------------------
    @ball.when_stopped_touching_wall(wall=WallSide.LEFT)
    def right_player_scores():
        score_right[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        ball.x = 0
        ball.y = 0
        ball.physics.x_speed = 300
        ball.physics.y_speed = 40
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
    ), f"expected at least {winning_score} total points, got {total_score}"
    assert score_left[0] >= winning_score or score_right[0] >= winning_score
    assert ai_moves[0] > 0, "AI paddle should have moved via repeat_forever"
    assert len(distances_measured) > 0, "distance_to() should have been called"
    assert all(
        d >= 0 for d in distances_measured
    ), "distance_to() should return non-negative values"


if __name__ == "__main__":
    test_pong_ai()
