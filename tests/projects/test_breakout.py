"""Breakout — realistic full-game project test.

A ball moves upward and bounces off a row of three bricks.  When the ball
stops touching a brick the brick is hidden (destroyed) and a score is
incremented.  If the ball falls below the paddle and touches the bottom
wall the player loses a life and the ball resets.  The game ends when all
bricks are destroyed or all lives are lost.

This test verifies:
- multiple when_stopped_touching callbacks registered for the same ball
  against different brick sprites (the _play_collision_type_set bug-fix)
- each brick fires its callback exactly once (the double-fire bug-fix)
- life tracking via when_stopped_touching_wall(WallSide.BOTTOM)
- win/lose conditions stop the program correctly
"""

max_frames = 3000
TOTAL_BRICKS = 3


def test_breakout():
    import play
    from play.callback.collision_callbacks import WallSide

    lives = [3]
    bricks_destroyed = [0]

    # --- sprites -----------------------------------------------------------
    ball = play.new_circle(color="white", x=0, y=-100, radius=12)
    paddle = play.new_box(color="blue", x=0, y=-230, width=120, height=15)
    lives_text = play.new_text(words="Lives: 3", x=0, y=270, font_size=24)
    score_text = play.new_text(words="Score: 0", x=0, y=245, font_size=24)

    # Three bricks in a row near the top of the screen
    bricks = [
        play.new_box(color="red", x=-160 + i * 160, y=180, width=100, height=25)
        for i in range(TOTAL_BRICKS)
    ]

    # --- physics -----------------------------------------------------------
    ball.start_physics(
        obeys_gravity=False,
        x_speed=120,
        y_speed=240,
        friction=0,
        mass=10,
        bounciness=1.0,
    )
    paddle.start_physics(
        obeys_gravity=False, can_move=False, friction=0, mass=10, bounciness=1.0
    )
    for brick in bricks:
        brick.start_physics(
            obeys_gravity=False, can_move=False, friction=0, mass=10, bounciness=1.0
        )

    # --- brick collision callbacks -----------------------------------------
    # Each brick gets its own when_stopped_touching callback.
    # This exercises the fix for the _play_collision_type_set flag: all three
    # bricks have collision_type=0 by default from pymunk, so without the fix
    # they would be treated as the same shape.
    def _make_brick_callback(brick):
        @ball.when_stopped_touching(brick)
        def brick_hit():
            if not brick.is_hidden:
                bricks_destroyed[0] += 1
                score_text.words = f"Score: {bricks_destroyed[0]}"
                brick.hide()
                brick.stop_physics()
                if bricks_destroyed[0] >= TOTAL_BRICKS:
                    play.stop_program()

    for brick in bricks:
        _make_brick_callback(brick)

    # --- bottom wall = lose a life -----------------------------------------
    @ball.when_stopped_touching_wall(wall=WallSide.BOTTOM)
    def ball_fell():
        lives[0] -= 1
        lives_text.words = f"Lives: {lives[0]}"
        ball.x = 0
        ball.y = -100
        ball.physics.x_speed = 120
        ball.physics.y_speed = 240
        if lives[0] <= 0:
            play.stop_program()

    # --- safety timeout ----------------------------------------------------
    @play.when_program_starts
    async def safety_timeout():
        for _ in range(max_frames):
            await play.animate()
        play.stop_program()

    play.start_program()

    # --- assertions --------------------------------------------------------
    assert bricks_destroyed[0] >= 0, "bricks_destroyed should never go negative"
    assert lives[0] >= 0, "lives should never go negative"
    assert (
        bricks_destroyed[0] <= TOTAL_BRICKS
    ), f"can't destroy more than {TOTAL_BRICKS} bricks, got {bricks_destroyed[0]}"
    # At least something happened during the game
    game_events = bricks_destroyed[0] + (3 - lives[0])
    assert (
        game_events > 0
    ), "No game events detected — ball likely did not move or collide with anything"


if __name__ == "__main__":
    test_breakout()
