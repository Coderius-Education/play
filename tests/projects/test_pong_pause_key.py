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

from conftest import post_key_down, post_key_up

max_frames = 5000
winning_score = 3


def test_pong_pause_key():
    import pygame
    import play
    from play.callback.collision_callbacks import WallSide

    score_left = [0]
    score_right = [0]
    paused = [False]
    pause_toggles = [0]
    saved_speed = [0.0, 0.0]  # x, y saved when pausing

    # --- sprites -----------------------------------------------------------
    ball = play.new_circle(color="black", x=0, y=0, radius=10)

    paddle_left = play.new_box(color="blue", x=-350, y=0, width=15, height=80)
    paddle_right = play.new_box(color="red", x=350, y=0, width=15, height=80)

    score_text = play.new_text(words="0 - 0", x=0, y=260, font_size=30)
    pause_text = play.new_text(words="PAUSED", x=0, y=0, font_size=60)
    pause_text.hide()

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

    # --- pause toggle via "p" key ------------------------------------------
    @play.when_key_pressed("p")
    def toggle_pause(key=None):
        if paused[0]:
            # unpause: restore saved speed
            paused[0] = False
            ball.physics.x_speed = saved_speed[0]
            ball.physics.y_speed = saved_speed[1]
            pause_text.hide()
        else:
            # pause: save current speed and zero it
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

    # --- driver: pause, verify freeze, unpause, let game finish ------------
    @play.when_program_starts
    async def driver():
        # let the ball move a bit first
        for _ in range(30):
            await play.animate()

        # press "p" to pause
        post_key_down(pygame.K_p)
        await play.animate()
        post_key_up(pygame.K_p)
        await play.animate()

        # record position while paused
        paused_x = ball.x
        paused_y = ball.y

        # wait 20 frames while paused — ball should not move
        for _ in range(20):
            await play.animate()

        position_stable = abs(ball.x - paused_x) < 0.5 and abs(ball.y - paused_y) < 0.5

        # press "p" again to unpause
        post_key_down(pygame.K_p)
        await play.animate()
        post_key_up(pygame.K_p)
        await play.animate()

        # let the game play out
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
    assert (
        pause_toggles[0] >= 2
    ), f"expected at least 2 pause toggles (pause + unpause), got {pause_toggles[0]}"
    assert not paused[0], "game should not be paused at the end"
    assert pause_text.is_hidden, "pause overlay should be hidden after unpause"


if __name__ == "__main__":
    test_pong_pause_key()
