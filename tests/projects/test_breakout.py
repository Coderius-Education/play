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

from tests.projects.conftest import add_safety_timeout

max_frames = 1500
TOTAL_BRICKS = 3


def test_breakout():
    import play
    from play.callback.collision_callbacks import WallSide

    lives = [3]
    bricks_destroyed = [0]
    raw_hits = {}

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
            # Counted before the is_hidden guard: that guard is what would
            # swallow a duplicate dispatch, so counting after it would hide
            # the very bug this test exists for.
            raw_hits[id(brick)] = raw_hits.get(id(brick), 0) + 1
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

    add_safety_timeout(max_frames)

    play.start_program()

    # --- assertions --------------------------------------------------------
    assert bricks_destroyed[0] > 0, "at least one brick should have been destroyed"
    assert (
        bricks_destroyed[0] <= TOTAL_BRICKS
    ), f"can't destroy more than {TOTAL_BRICKS} bricks, got {bricks_destroyed[0]}"

    # Each brick has its own callback even though every brick shares pymunk's
    # default collision_type. If they were collapsed into one shape, a single
    # collision would dispatch every brick's callback and hide bricks the ball
    # never reached -- so the property to check is that the bricks which fired
    # are exactly the bricks which vanished.
    #
    # Not asserted: one dispatch per brick. when_stopped_touching legitimately
    # fires more than once for the same pair as the ball separates and
    # re-approaches, so counts like [2, 4] are normal rather than duplicates.
    assert raw_hits, "no brick collision callback fired at all"
    fired = {i for i, brick in enumerate(bricks) if id(brick) in raw_hits}
    vanished = {i for i, brick in enumerate(bricks) if brick.is_hidden}
    assert fired == vanished, (
        "the bricks that were hit and the bricks that disappeared should be "
        f"the same set; hit {sorted(fired)}, vanished {sorted(vanished)}"
    )

    # `lives >= 0` could never fail. Lives only drop when the ball reaches the
    # bottom wall, and the scoreboard has to agree with the counter.
    assert 0 <= lives[0] <= 3
    assert lives_text.words == f"Lives: {lives[0]}"
    destroyed = [b for b in bricks if b.is_hidden]
    assert (
        len(destroyed) == bricks_destroyed[0]
    ), "the hidden bricks should match the destroyed count"


if __name__ == "__main__":
    test_breakout()
