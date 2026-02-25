"""Pong with mouse-controlled paddle — realistic full-game project test.

The left paddle follows the mouse y-position each frame (via repeat_forever).
Simulated MOUSEMOTION events move the mouse up and down.  The right paddle
is static.

This test verifies:
- mouse.y tracking from MOUSEMOTION events
- @play.repeat_forever callback runs each frame
- paddle positioning from mouse input alongside physics collisions
"""

import pytest

max_frames = 3000
winning_score = 3


def test_pong_mouse():
    import pygame
    import play
    from play.callback.collision_callbacks import WallSide

    score_left = [0]
    score_right = [0]
    mouse_updates = [0]

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

    # --- simulate mouse movement + safety timeout --------------------------
    @play.when_program_starts
    async def driver():
        from play.io.screen import screen

        for i in range(max_frames):
            # Move mouse up and down in a sine-wave pattern
            # Convert play y-coord to pygame screen coord
            play_y = 100 * (1 if (i // 60) % 2 == 0 else -1)
            screen_x = int(screen.width / 2 + (-350))  # left paddle x
            screen_y = int(screen.height / 2 - play_y)
            pygame.event.post(
                pygame.event.Event(
                    pygame.MOUSEMOTION,
                    {"pos": (screen_x, screen_y), "rel": (0, 0), "buttons": (0, 0, 0)},
                )
            )
            await play.animate()
        play.stop_program()

    play.start_program()

    # --- assertions --------------------------------------------------------
    total_score = score_left[0] + score_right[0]
    assert (
        total_score >= winning_score
    ), f"expected at least {winning_score} total points, got {total_score}"
    assert score_left[0] >= winning_score or score_right[0] >= winning_score
    assert mouse_updates[0] > 0, "repeat_forever should have run (mouse tracking)"


if __name__ == "__main__":
    test_pong_mouse()
