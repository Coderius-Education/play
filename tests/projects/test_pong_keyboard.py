"""Pong with keyboard-controlled paddles — realistic full-game project test.

Two paddles controlled via simulated key presses (w/s for left, up/down for
right).  An async loop posts KEYDOWN / KEYUP events so the paddles actually
move.  The ball bounces between them with physics.

This test verifies:
- @when_key_pressed callback fires for specific keys
- keyboard-driven paddle movement works alongside physics
- scoring and game-end still function with active key input
"""

from conftest import post_key_down, post_key_up

max_frames = 5000
winning_score = 3


def test_pong_keyboard():
    import pygame
    import play
    from play.callback.collision_callbacks import WallSide

    score_left = [0]
    score_right = [0]
    paddle_moves = [0]

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

    # --- simulate keyboard input + safety timeout --------------------------
    @play.when_program_starts
    async def driver():
        directions = [pygame.K_w, pygame.K_s, pygame.K_UP, pygame.K_DOWN]
        for i in range(max_frames):
            # press a key every 10 frames, release it 5 frames later
            if i % 10 == 0:
                key = directions[i // 10 % len(directions)]
                post_key_down(key)
            if i % 10 == 5:
                key = directions[i // 10 % len(directions)]
                post_key_up(key)
            await play.animate()
        play.stop_program()

    play.start_program()

    # --- assertions --------------------------------------------------------
    total_score = score_left[0] + score_right[0]
    assert (
        total_score >= winning_score
    ), f"expected at least {winning_score} total points, got {total_score}"
    assert score_left[0] >= winning_score or score_right[0] >= winning_score
    assert paddle_moves[0] > 0, "keyboard-driven paddle movement should have occurred"


if __name__ == "__main__":
    test_pong_keyboard()
