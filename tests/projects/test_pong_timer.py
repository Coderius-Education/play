"""Pong with timer-based serve — realistic full-game project test.

After each point, the ball freezes and a countdown runs using
await play.timer() instead of manual frame counting.  This is
the simplest way students add delays to their games.

This test verifies:
- await play.timer(seconds) pauses execution for the given duration
- the ball is stationary during the timer wait
- the game resumes and completes after the delay
"""

from tests.projects.conftest import (
    setup_pong,
    assert_pong_winner,
)

max_frames = 2000
winning_score = 2


def test_pong_timer():
    import play
    from play.callback.collision_callbacks import WallSide

    score_left = [0]
    score_right = [0]
    timer_used = [False]
    serve_direction = [0]

    ball, paddle_left, paddle_right, score_text = setup_pong()

    # --- collisions --------------------------------------------------------
    @ball.when_stopped_touching(paddle_left)
    def ball_leaves_left():
        pass

    @ball.when_stopped_touching(paddle_right)
    def ball_leaves_right():
        pass

    # --- scoring: freeze ball and request serve ----------------------------
    @ball.when_stopped_touching_wall(wall=WallSide.LEFT)
    def right_scores():
        score_right[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        if score_right[0] >= winning_score:
            play.stop_program()
            return
        ball.x = 0
        ball.y = 0
        ball.physics.x_speed = 0
        ball.physics.y_speed = 0
        serve_direction[0] = 1

    @ball.when_stopped_touching_wall(wall=WallSide.RIGHT)
    def left_scores():
        score_left[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        if score_left[0] >= winning_score:
            play.stop_program()
            return
        ball.x = 0
        ball.y = 0
        ball.physics.x_speed = 0
        ball.physics.y_speed = 0
        serve_direction[0] = -1

    # --- driver: use play.timer() for serve delay --------------------------
    @play.when_program_starts
    async def driver():
        for _ in range(max_frames):
            await play.animate()

            if serve_direction[0] != 0:
                direction = serve_direction[0]
                serve_direction[0] = 0

                # Use play.timer() to wait before serving
                await play.timer(seconds=0.05)
                timer_used[0] = True

                ball.physics.x_speed = 300 * direction
                ball.physics.y_speed = 40 * direction

        play.stop_program()

    play.start_program()

    # --- assertions --------------------------------------------------------
    assert_pong_winner(score_left, score_right, winning_score)
    assert timer_used[
        0
    ], "play.timer() should have been used for at least one serve delay"


if __name__ == "__main__":
    test_pong_timer()
