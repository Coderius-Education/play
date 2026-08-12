"""Breakout — realistic full-game project test.

A ball is served up at a row of three bricks.  Destroying a brick hides it and
scores a point, and the ball is re-served at whichever brick is still standing.
If the ball ever gets past the paddle and reaches the bottom wall a life is
lost.  The game ends when all three bricks are destroyed.

This test verifies:
- multiple when_stopped_touching callbacks registered for the same ball
  against different brick sprites (the _play_collision_type_set bug-fix)
- the bricks that fired a callback are exactly the bricks that vanished
- life tracking via when_stopped_touching_wall(WallSide.BOTTOM)
- the game stops on its win condition rather than on the safety timeout

Each serve is aimed at a specific brick rather than fired at a fixed angle and
left to carom around.  The old version launched the ball on one fixed
trajectory that only ever intersected the right-hand brick, so it could not
clear the row however long it ran: it spent 1500 frames -- 24 seconds, the
slowest test in the suite -- to establish that at least one brick out of three
had been hit, and the win condition in the docstring was never reached or
asserted.
"""

from tests.projects.conftest import add_safety_timeout

max_frames = 600
TOTAL_BRICKS = 3

BRICK_Y = 180
BRICK_HEIGHT = 25
BALL_START_Y = -100
BALL_RADIUS = 12
SERVE_Y_SPEED = 240

# How long a serve takes to climb from the serve point to the underside of the
# brick row. The horizontal speed that puts the ball under a given brick is
# then just that brick's x divided by this.
FLIGHT_TIME = (BRICK_Y - BRICK_HEIGHT / 2 - BALL_RADIUS - BALL_START_Y) / SERVE_Y_SPEED


def test_breakout():
    import play
    from play.callback.collision_callbacks import WallSide

    lives = [3]
    bricks_destroyed = [0]
    won = [False]
    raw_hits = {}

    # --- sprites -----------------------------------------------------------
    ball = play.new_circle(color="white", x=0, y=BALL_START_Y, radius=BALL_RADIUS)
    paddle = play.new_box(color="blue", x=0, y=-230, width=120, height=15)
    lives_text = play.new_text(words="Lives: 3", x=0, y=270, font_size=24)
    score_text = play.new_text(words="Score: 0", x=0, y=245, font_size=24)

    # Three bricks in a row near the top of the screen
    bricks = [
        play.new_box(color="red", x=-160 + i * 160, y=BRICK_Y, width=100, height=25)
        for i in range(TOTAL_BRICKS)
    ]

    # --- physics -----------------------------------------------------------
    ball.start_physics(
        obeys_gravity=False,
        x_speed=bricks[0].x / FLIGHT_TIME,
        y_speed=SERVE_Y_SPEED,
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

    def _serve_at_next_brick():
        """Put the ball back on the launcher, aimed at a brick still standing."""
        remaining = [b for b in bricks if not b.is_hidden]
        if not remaining:
            return
        ball.x = 0
        ball.y = BALL_START_Y
        ball.physics.x_speed = remaining[0].x / FLIGHT_TIME
        ball.physics.y_speed = SERVE_Y_SPEED

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
                    won[0] = True
                    play.stop_program()
                    return
                _serve_at_next_brick()

    for brick in bricks:
        _make_brick_callback(brick)

    # --- bottom wall = lose a life -----------------------------------------
    @ball.when_stopped_touching_wall(wall=WallSide.BOTTOM)
    def ball_fell():
        lives[0] -= 1
        lives_text.words = f"Lives: {lives[0]}"
        _serve_at_next_brick()
        if lives[0] <= 0:
            play.stop_program()

    add_safety_timeout(max_frames)

    play.start_program()

    # --- assertions --------------------------------------------------------
    assert bricks_destroyed[0] == TOTAL_BRICKS, (
        f"the ball should clear all {TOTAL_BRICKS} bricks, got "
        f"{bricks_destroyed[0]}"
    )
    assert won[0], "the game should end on the last brick, not on the safety timeout"
    assert score_text.words == f"Score: {TOTAL_BRICKS}"
    assert all(b.is_hidden for b in bricks), "every brick should be gone"

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

    # Every serve is aimed straight at a standing brick, so the ball should
    # never get behind the paddle at all.
    assert lives[0] == 3, f"no life should have been lost, but lives is {lives[0]}"
    assert lives_text.words == "Lives: 3"


if __name__ == "__main__":
    test_breakout()
