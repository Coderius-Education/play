"""Pong with pause key toggle — realistic full-game project test.

The player presses "p" to pause the game and "p" again to unpause.
While paused the ball freezes (speed set to 0) and a "PAUSED" overlay
appears.  This is the most common way students implement pausing.

This test verifies:
- @when_key_pressed fires for the pause key
- toggling a game state variable pauses / unpauses correctly
- sprite.hide() / sprite.show() for the pause overlay
- the ball does not move while the game is paused
- the game resumes and completes after unpausing
"""

from tests.conftest import post_key_down, post_key_up
from tests.projects.conftest import (
    setup_pong,
    add_pong_scoring,
    assert_pong_winner,
)

max_frames = 5000
winning_score = 1


def test_pong_pause_key():
    import pygame
    import play

    score_left = [0]
    score_right = [0]
    paused = [False]
    pause_toggles = [0]
    saved_speed = [0.0, 0.0]
    position_stable_during_pause = [True]

    ball, paddle_left, paddle_right, score_text = setup_pong()

    pause_text = play.new_text(words="PAUSED", x=0, y=0, font_size=60)
    pause_text.hide()

    # --- pause toggle via "p" key ------------------------------------------
    @play.when_key_pressed("p")
    def toggle_pause(key=None):
        if paused[0]:
            paused[0] = False
            ball.physics.x_speed = saved_speed[0]
            ball.physics.y_speed = saved_speed[1]
            pause_text.hide()
        else:
            paused[0] = True
            saved_speed[0] = ball.physics.x_speed
            saved_speed[1] = ball.physics.y_speed
            ball.physics.x_speed = 0
            ball.physics.y_speed = 0
            pause_text.show()
        pause_toggles[0] += 1

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

    # --- driver: pause, verify freeze, unpause, let game finish ------------
    @play.when_program_starts
    async def driver():
        for _ in range(30):
            await play.animate()

        # press "p" to pause
        post_key_down(pygame.K_p)
        await play.animate()
        post_key_up(pygame.K_p)
        await play.animate()

        paused_x = ball.x
        paused_y = ball.y

        for _ in range(20):
            await play.animate()

        if abs(ball.x - paused_x) > 0.5 or abs(ball.y - paused_y) > 0.5:
            position_stable_during_pause[0] = False

        # press "p" again to unpause
        post_key_down(pygame.K_p)
        await play.animate()
        post_key_up(pygame.K_p)
        await play.animate()

        for _ in range(max_frames):
            await play.animate()
        play.stop_program()

    play.start_program()

    assert_pong_winner(score_left, score_right, winning_score)
    assert (
        pause_toggles[0] >= 2
    ), f"expected at least 2 pause toggles, got {pause_toggles[0]}"
    assert not paused[0], "game should not be paused at the end"
    assert pause_text.is_hidden, "pause overlay should be hidden after unpause"
    assert position_stable_during_pause[
        0
    ], "ball position should not change while the game is paused"


if __name__ == "__main__":
    test_pong_pause_key()
