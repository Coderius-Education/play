"""Pong with pause/unpause — realistic full-game project test.

The ball freezes (physics.pause) after each point and resumes
(physics.unpause) after a short wait.  This simulates a common game
pattern where the action pauses briefly between rallies.

This test verifies:
- physics.pause() stops the ball from moving
- physics.unpause() resumes movement
- the ball's position does not change while paused
- the game completes normally after multiple pause/unpause cycles
"""

import pytest

max_frames = 5000
winning_score = 3


def test_pong_pause():
    import play
    from play.callback.collision_callbacks import WallSide

    score_left = [0]
    score_right = [0]
    pause_cycles = [0]
    position_stable_during_pause = [True]

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

    # --- serve with pause/unpause cycle ------------------------------------
    async def pause_and_serve(direction):
        ball.x = 0
        ball.y = 0
        ball.physics.x_speed = 0
        ball.physics.y_speed = 0
        ball.physics.pause()

        # Record position while paused
        paused_x = ball.x
        paused_y = ball.y

        # Wait a few frames while paused
        for _ in range(5):
            await play.animate()

        # Verify position didn't change while paused
        if abs(ball.x - paused_x) > 0.01 or abs(ball.y - paused_y) > 0.01:
            position_stable_during_pause[0] = False

        ball.physics.unpause()
        ball.physics.x_speed = 300 * direction
        ball.physics.y_speed = 40 * direction
        pause_cycles[0] += 1

    # --- collisions --------------------------------------------------------
    @ball.when_stopped_touching(paddle_left)
    def ball_leaves_left():
        pass

    @ball.when_stopped_touching(paddle_right)
    def ball_leaves_right():
        pass

    # --- scoring -----------------------------------------------------------
    @ball.when_stopped_touching_wall(wall=WallSide.LEFT)
    async def right_player_scores():
        score_right[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        if score_right[0] >= winning_score:
            play.stop_program()
            return
        await pause_and_serve(1)

    @ball.when_stopped_touching_wall(wall=WallSide.RIGHT)
    async def left_player_scores():
        score_left[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        if score_left[0] >= winning_score:
            play.stop_program()
            return
        await pause_and_serve(-1)

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
    assert pause_cycles[0] > 0, "at least one pause/unpause cycle should have occurred"
    assert position_stable_during_pause[
        0
    ], "ball position should not change while physics is paused"


if __name__ == "__main__":
    test_pong_pause()
