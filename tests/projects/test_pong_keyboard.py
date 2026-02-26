"""Pong with keyboard-controlled paddles — realistic full-game project test.

Two paddles controlled via simulated key presses (w/s for left, up/down for
right).  An async loop posts KEYDOWN / KEYUP events so the paddles actually
move.  The ball bounces between them with physics.

This test verifies:
- @when_key_pressed callback fires for specific keys
- keyboard-driven paddle movement works alongside physics
- scoring and game-end still function with active key input
"""

from tests.conftest import post_key_down, post_key_up
from tests.projects.conftest import (
    setup_pong,
    add_pong_scoring,
    assert_pong_winner,
)

max_frames = 5000
winning_score = 3


def test_pong_keyboard():
    import pygame
    import play

    score_left = [0]
    score_right = [0]
    paddle_moves = [0]

    ball, paddle_left, paddle_right, score_text = setup_pong()

    # --- keyboard-controlled paddle movement -------------------------------
    @play.when_key_pressed("w")
    def left_paddle_up(key=None):
        paddle_left.y += 5
        paddle_moves[0] += 1

    @play.when_key_pressed("s")
    def left_paddle_down(key=None):
        paddle_left.y -= 5
        paddle_moves[0] += 1

    @play.when_key_pressed("up")
    def right_paddle_up(key=None):
        paddle_right.y += 5
        paddle_moves[0] += 1

    @play.when_key_pressed("down")
    def right_paddle_down(key=None):
        paddle_right.y -= 5
        paddle_moves[0] += 1

    # --- scoring -----------------------------------------------------------
    @ball.when_stopped_touching(paddle_left)
    def ball_leaves_left():
        pass

    @ball.when_stopped_touching(paddle_right)
    def ball_leaves_right():
        pass

    add_pong_scoring(
        ball, score_left, score_right, score_text, winning_score=winning_score
    )

    # --- simulate keyboard input + safety timeout --------------------------
    @play.when_program_starts
    async def driver():
        directions = [pygame.K_w, pygame.K_s, pygame.K_UP, pygame.K_DOWN]
        for i in range(max_frames):
            if i % 10 == 0:
                key = directions[i // 10 % len(directions)]
                post_key_down(key)
            if i % 10 == 5:
                key = directions[i // 10 % len(directions)]
                post_key_up(key)
            await play.animate()
        play.stop_program()

    play.start_program()

    assert_pong_winner(score_left, score_right, winning_score)
    assert paddle_moves[0] > 0, "keyboard-driven paddle movement should have occurred"


if __name__ == "__main__":
    test_pong_keyboard()
