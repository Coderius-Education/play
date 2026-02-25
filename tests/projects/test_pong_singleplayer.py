"""Single-player Pong — realistic full-game project test.

A ball bounces around the screen at high speed.  A paddle sits at the
bottom.  The ball bounces off the top, left, and right walls and the
paddle.  If it hits the bottom wall the player loses a life.  The game
tracks lives and paddle hits.

This test verifies:
- high x_speed / y_speed with diagonal bouncing
- paddle collision detection via when_stopped_touching callback
- bottom-wall "miss" detection via when_stopped_touching_wall callback
- life tracking and game-over
"""

import pytest

max_frames = 2000
lives = 3
paddle_hits = 0
bottom_hits = 0


def test_pong_singleplayer():
    import play
    from play.callback.collision_callbacks import WallSide

    global lives, paddle_hits, bottom_hits

    # --- sprites -----------------------------------------------------------
    ball = play.new_circle(color="black", x=0, y=100, radius=10)
    # Wide, thick paddle so the ball reliably hits it at high speed
    paddle = play.new_box(color="green", x=0, y=-250, width=300, height=60)
    lives_text = play.new_text(words="Lives: 3", x=0, y=270, font_size=30)

    # --- physics -----------------------------------------------------------
    ball.start_physics(
        obeys_gravity=False,
        x_speed=60,
        y_speed=-260,
        friction=0,
        mass=10,
        bounciness=1.0,
    )
    paddle.start_physics(
        obeys_gravity=False, can_move=False, friction=0, mass=10, bounciness=1.0
    )

    # --- paddle collision --------------------------------------------------
    @ball.when_stopped_touching(paddle)
    def ball_hits_paddle():
        global paddle_hits
        paddle_hits += 1

    # --- ball hits bottom wall = lose a life -------------------------------
    @ball.when_stopped_touching_wall(wall=WallSide.BOTTOM)
    def ball_hits_bottom():
        global lives, bottom_hits
        bottom_hits += 1
        lives -= 1
        lives_text.words = f"Lives: {lives}"
        ball.x = 0
        ball.y = 100
        ball.physics.x_speed = 60
        ball.physics.y_speed = -260
        if lives <= 0:
            play.stop_program()

    # --- safety timeout ----------------------------------------------------
    @play.when_program_starts
    async def safety_timeout():
        for _ in range(max_frames):
            await play.animate()
        play.stop_program()

    play.start_program()

    # --- assertions --------------------------------------------------------
    assert paddle_hits > 0, "ball should have hit the paddle at least once"
    assert bottom_hits > 0, "ball should have hit the bottom wall at least once"
    assert lives < 3, "player should have lost at least one life"


if __name__ == "__main__":
    test_pong_singleplayer()
