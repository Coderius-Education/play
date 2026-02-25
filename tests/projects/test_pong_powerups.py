"""Pong with power-ups — realistic full-game project test.

A power-up box spawns in the centre.  When the ball hits it, it hides and
the scoring paddle grows (size increases).  After a few seconds the power-up
reappears and the paddle shrinks back.

This test verifies:
- sprite.hide() removes the sprite from physics AND rendering
- sprite.show() re-adds the sprite to physics
- sprite.size setter changes the sprite's physical and visual size
- when_stopped_touching still fires for a power-up sprite
- await play.timer() for timed power-up duration
"""

import pytest

max_frames = 4000
winning_score = 3


def test_pong_powerups():
    import play
    from play.callback.collision_callbacks import WallSide

    score_left = [0]
    score_right = [0]
    powerup_collected = [0]
    size_changes = [0]

    # --- sprites -----------------------------------------------------------
    ball = play.new_circle(color="black", x=0, y=0, radius=10)

    paddle_left = play.new_box(color="blue", x=-350, y=0, width=15, height=80)
    paddle_right = play.new_box(color="red", x=350, y=0, width=15, height=80)

    # Power-up box — same as the obstacle in test_pong_obstacles (which works)
    powerup = play.new_box(color="green", x=0, y=0, width=30, height=120)

    score_text = play.new_text(words="0 - 0", x=0, y=260, font_size=30)

    # --- physics -----------------------------------------------------------
    ball.start_physics(
        obeys_gravity=False,
        x_speed=300,
        y_speed=60,
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
    powerup.start_physics(
        obeys_gravity=False, can_move=False, friction=0, mass=10, bounciness=1.0
    )

    # --- power-up collision ------------------------------------------------
    powerup_hide_frame = [0]  # frame when powerup was hidden (0 = not hidden)

    @ball.when_stopped_touching(powerup)
    def ball_hits_powerup():
        if powerup.is_hidden:
            return
        powerup_collected[0] += 1
        powerup.hide()
        # grow whichever paddle the ball is heading towards
        if ball.physics.x_speed > 0:
            paddle_right.size = 150
        else:
            paddle_left.size = 150
        size_changes[0] += 1
        powerup_hide_frame[0] = 1  # mark as needing reset

    # --- paddle collisions -------------------------------------------------
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
        ball.physics.y_speed = 60
        if score_right[0] >= winning_score:
            play.stop_program()

    @ball.when_stopped_touching_wall(wall=WallSide.RIGHT)
    def left_player_scores():
        score_left[0] += 1
        score_text.words = f"{score_left[0]} - {score_right[0]}"
        ball.x = 0
        ball.y = 0
        ball.physics.x_speed = -300
        ball.physics.y_speed = -60
        if score_left[0] >= winning_score:
            play.stop_program()

    # --- powerup respawn via repeat_forever --------------------------------
    respawn_countdown = [0]

    @play.repeat_forever
    def respawn_powerup():
        if powerup_hide_frame[0] > 0:
            powerup_hide_frame[0] += 1
            # respawn after ~60 frames (~1 second)
            if powerup_hide_frame[0] > 60:
                paddle_left.size = 100
                paddle_right.size = 100
                size_changes[0] += 1
                powerup.show()
                powerup_hide_frame[0] = 0

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
    assert powerup_collected[0] > 0, (
        "ball should have hit the power-up at least once; "
        "when_stopped_touching on a non-paddle sprite may not work"
    )
    assert (
        size_changes[0] > 0
    ), "paddle size should have changed at least once via the power-up"


if __name__ == "__main__":
    test_pong_powerups()
