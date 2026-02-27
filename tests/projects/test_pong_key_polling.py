"""Pong with key_is_pressed() polling — realistic full-game project test.

Both paddles are controlled by polling play.key_is_pressed() inside a
repeat_forever loop, rather than using @when_key_pressed callbacks.
This is the most common way beginners write keyboard controls:

    @play.repeat_forever
    def game_loop():
        if play.key_is_pressed('w'):
            paddle.y += 5

This test verifies:
- play.key_is_pressed() returns True while a key is held
- polling-based paddle movement works alongside physics
- multiple keys can be polled independently each frame
"""

from tests.conftest import post_key_down, post_key_up
from tests.projects.conftest import (
    setup_pong,
    add_pong_scoring,
    add_safety_timeout,
    assert_pong_winner,
)

max_frames = 1500
winning_score = 1


def test_pong_key_polling():
    import pygame
    import play

    score_left = [0]
    score_right = [0]
    left_moves = [0]
    right_moves = [0]

    ball, paddle_left, paddle_right, score_text = setup_pong()

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

    # --- polling-based paddle movement -------------------------------------
    @play.repeat_forever
    def move_paddles():
        if play.key_is_pressed("w"):
            paddle_left.y += 5
            left_moves[0] += 1
        if play.key_is_pressed("s"):
            paddle_left.y -= 5
            left_moves[0] += 1
        if play.key_is_pressed("up"):
            paddle_right.y += 5
            right_moves[0] += 1
        if play.key_is_pressed("down"):
            paddle_right.y -= 5
            right_moves[0] += 1

    # --- driver: simulate key holds ----------------------------------------
    @play.when_program_starts
    async def driver():
        # Hold W and UP for a bit to move paddles up
        post_key_down(pygame.K_w)
        post_key_down(pygame.K_UP)
        for _ in range(30):
            await play.animate()
        post_key_up(pygame.K_w)
        post_key_up(pygame.K_UP)

        # Hold S and DOWN to move them back
        post_key_down(pygame.K_s)
        post_key_down(pygame.K_DOWN)
        for _ in range(30):
            await play.animate()
        post_key_up(pygame.K_s)
        post_key_up(pygame.K_DOWN)

        # Let the game play out
        for _ in range(max_frames):
            await play.animate()
        play.stop_program()

    play.start_program()

    # --- assertions --------------------------------------------------------
    assert_pong_winner(score_left, score_right, winning_score)
    assert (
        left_moves[0] > 0
    ), "key_is_pressed('w'/'s') should have moved the left paddle"
    assert (
        right_moves[0] > 0
    ), "key_is_pressed('up'/'down') should have moved the right paddle"


if __name__ == "__main__":
    test_pong_key_polling()
