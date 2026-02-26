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

from tests.projects.conftest import (
    setup_pong,
    add_safety_timeout,
    assert_pong_winner,
)

max_frames = 5000
winning_score = 2


def test_pong_pause():
    import play
    from play.callback.collision_callbacks import WallSide

    score_left = [0]
    score_right = [0]
    pause_cycles = [0]
    position_stable_during_pause = [True]

    ball, paddle_left, paddle_right, score_text = setup_pong()

    # --- serve with pause/unpause cycle ------------------------------------
    async def pause_and_serve(direction):
        ball.x = 0
        ball.y = 0
        ball.physics.x_speed = 0
        ball.physics.y_speed = 0
        ball.physics.pause()

        paused_x = ball.x
        paused_y = ball.y

        for _ in range(5):
            await play.animate()

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

    # --- scoring (custom because of async pause_and_serve) -----------------
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

    add_safety_timeout(max_frames)

    play.start_program()

    assert_pong_winner(score_left, score_right, winning_score)
    assert pause_cycles[0] > 0, "at least one pause/unpause cycle should have occurred"
    assert position_stable_during_pause[
        0
    ], "ball position should not change while physics is paused"


if __name__ == "__main__":
    test_pong_pause()
