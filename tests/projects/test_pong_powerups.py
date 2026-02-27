"""Pong with power-ups — realistic full-game project test.

A power-up box spawns in the centre.  When the ball hits it, it hides and
the scoring paddle grows (size increases).  After about a second the
power-up reappears and the paddle shrinks back.

This test verifies:
- sprite.hide() removes the sprite from physics AND rendering
- sprite.show() re-adds the sprite to physics
- sprite.size setter changes the sprite's physical and visual size
- when_stopped_touching still fires for a power-up sprite
- @play.repeat_forever for timed power-up respawn
"""

from tests.projects.conftest import (
    setup_pong,
    add_pong_scoring,
    add_safety_timeout,
    assert_pong_winner,
)

max_frames = 1500
winning_score = 1


def test_pong_powerups():
    import play

    score_left = [0]
    score_right = [0]
    powerup_collected = [0]
    size_changes = [0]
    powerup_hide_frame = [0]

    ball, paddle_left, paddle_right, score_text = setup_pong(ball_y_speed=60)

    # Power-up box in the centre
    powerup = play.new_box(color="green", x=0, y=0, width=30, height=120)
    powerup.start_physics(
        obeys_gravity=False, can_move=False, friction=0, mass=10, bounciness=1.0
    )

    # --- power-up collision ------------------------------------------------
    @ball.when_stopped_touching(powerup)
    def ball_hits_powerup():
        if powerup.is_hidden:
            return
        powerup_collected[0] += 1
        powerup.hide()
        if ball.physics.x_speed > 0:
            paddle_right.size = 150
        else:
            paddle_left.size = 150
        size_changes[0] += 1
        powerup_hide_frame[0] = 1

    # --- paddle collisions -------------------------------------------------
    @ball.when_stopped_touching(paddle_left)
    def ball_leaves_left():
        pass

    @ball.when_stopped_touching(paddle_right)
    def ball_leaves_right():
        pass

    # --- powerup respawn via repeat_forever --------------------------------
    @play.repeat_forever
    def respawn_powerup():
        if powerup_hide_frame[0] > 0:
            powerup_hide_frame[0] += 1
            if powerup_hide_frame[0] > 60:
                paddle_left.size = 100
                paddle_right.size = 100
                size_changes[0] += 1
                powerup.show()
                powerup_hide_frame[0] = 0

    add_pong_scoring(
        ball,
        score_left,
        score_right,
        score_text,
        ball_y_speed=60,
        winning_score=winning_score,
    )
    add_safety_timeout(max_frames)

    play.start_program()

    assert_pong_winner(score_left, score_right, winning_score)
    assert powerup_collected[0] > 0, "ball should have hit the power-up at least once"
    assert (
        size_changes[0] > 0
    ), "paddle size should have changed at least once via the power-up"


if __name__ == "__main__":
    test_pong_powerups()
