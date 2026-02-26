"""Pong with mouse-controlled paddle — realistic full-game project test.

The left paddle follows the mouse y-position each frame (via repeat_forever).
Simulated MOUSEMOTION events move the mouse up and down.  The right paddle
is static.

This test verifies:
- mouse.y tracking from MOUSEMOTION events
- @play.repeat_forever callback runs each frame
- paddle positioning from mouse input alongside physics collisions
"""

from tests.conftest import post_mouse_motion
from tests.projects.conftest import (
    setup_pong,
    add_pong_scoring,
    assert_pong_winner,
)

max_frames = 4000
winning_score = 3


def test_pong_mouse():
    import play
    from play.io.screen import screen

    score_left = [0]
    score_right = [0]
    mouse_updates = [0]

    ball, paddle_left, paddle_right, score_text = setup_pong()

    # --- mouse-controlled left paddle (every frame) ------------------------
    @play.repeat_forever
    def track_mouse():
        paddle_left.y = play.mouse.y
        mouse_updates[0] += 1

    # --- collisions --------------------------------------------------------
    @ball.when_stopped_touching(paddle_left)
    def ball_leaves_left():
        pass

    @ball.when_stopped_touching(paddle_right)
    def ball_leaves_right():
        pass

    add_pong_scoring(
        ball, score_left, score_right, score_text, winning_score=winning_score
    )

    # --- simulate mouse movement + safety timeout --------------------------
    @play.when_program_starts
    async def driver():
        for i in range(max_frames):
            play_y = 100 * (1 if (i // 60) % 2 == 0 else -1)
            screen_x = int(screen.width / 2 + (-350))
            screen_y = int(screen.height / 2 - play_y)
            post_mouse_motion(screen_x, screen_y)
            await play.animate()
        play.stop_program()

    play.start_program()

    assert_pong_winner(score_left, score_right, winning_score)
    assert mouse_updates[0] > 0, "repeat_forever should have run (mouse tracking)"


if __name__ == "__main__":
    test_pong_mouse()
