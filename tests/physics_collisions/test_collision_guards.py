"""Tests for the guards that decide whether a collision callback exists.

Mutation testing showed the existing collision tests confirm that callbacks
*fire*, but leave the conditions deciding *whether* to fire unconstrained:
flipping the `and`/`in` guards in _handle_collision, or the value the begin
handler returns to pymunk, changed nothing that any of 1008 tests noticed.

The gap is the negative case. Every existing test registers a callback and
then triggers exactly that collision. None of them collide two things whose
pair has no callback registered, which is the only case those guards exist to
reject — and getting them wrong raises KeyError on a lookup that was never
reached before.
"""

import play
from play.callback.collision_callbacks import WallSide


def _run(max_frames=500):
    @play.when_program_starts
    async def budget():
        for _ in range(max_frames):
            await play.animate()
        play.stop_program()

    play.start_program()


def test_wall_callback_registered_for_one_wall_ignores_another():
    """A ball watching the LEFT wall must survive hitting the RIGHT one.

    The guard has to reject the pair before indexing
    callbacks[True][sprite][wall]. Loosening it to `or` makes that lookup run
    for a wall with no entry, which is a KeyError inside a pymunk callback.
    """
    fired = []

    # Started near the right wall and given a budget too short to bounce back
    # across the screen: the ball reaches the RIGHT wall and cannot reach the
    # LEFT one, so a firing here is the guard letting the wrong pair through.
    ball = play.new_circle(color="black", x=300, y=0, radius=10)
    ball.start_physics(
        obeys_gravity=False, x_speed=400, y_speed=0, friction=0, mass=10, bounciness=1.0
    )

    @ball.when_touching_wall(wall=WallSide.LEFT)
    def touched_left():
        fired.append("left")

    _run(60)

    assert ball.physics.x_speed < 0, (
        "the ball should have bounced off the right wall within the budget, "
        f"but its x_speed is {ball.physics.x_speed}"
    )
    assert not fired, "the LEFT-wall callback fired for a ball sent at the RIGHT wall"


def test_sprite_callback_registered_for_one_partner_ignores_another():
    """A ball watching block A must survive touching block B.

    Same shape of guard as the wall case, on the sprite-sprite path: the pair
    (ball, other) has no entry, and the guard is what stops the lookup.
    """
    fired = []

    ball = play.new_circle(color="black", x=-150, y=0, radius=10)
    watched = play.new_box(color="green", x=300, y=300, width=20, height=20)
    other = play.new_box(color="blue", x=0, y=0, width=40, height=400)

    ball.start_physics(
        obeys_gravity=False, x_speed=200, y_speed=0, friction=0, mass=10, bounciness=1.0
    )
    for block in (watched, other):
        block.start_physics(
            obeys_gravity=False, can_move=False, friction=0, mass=10, bounciness=1.0
        )

    @ball.when_touching(watched)
    def touched_watched():
        fired.append("watched")

    _run()

    assert not fired, "the callback for a different sprite fired on this collision"


def test_ball_bounces_off_a_wall():
    """Wall collisions must still be resolved physically.

    _handle_collision returns True to tell pymunk to process the collision.
    Returning False leaves callbacks working while the ball sails through the
    wall, so asserting on callbacks alone cannot see it.
    """
    ball = play.new_circle(color="black", x=0, y=0, radius=10)
    ball.start_physics(
        obeys_gravity=False, x_speed=400, y_speed=0, friction=0, mass=10, bounciness=1.0
    )

    @play.when_program_starts
    async def budget():
        for _ in range(400):
            await play.animate()
        play.stop_program()

    play.start_program()

    # The screen is 800 wide, so the right edge is at x=400. A ball that was
    # never stopped would be far outside it after 400 frames at 400px/s.
    assert ball.x < 400, f"the ball passed through the right wall (x={ball.x})"


def test_ball_bounces_off_a_static_sprite():
    """Same property on the sprite-sprite path."""
    ball = play.new_circle(color="black", x=-150, y=0, radius=10)
    block = play.new_box(color="blue", x=0, y=0, width=40, height=400)

    ball.start_physics(
        obeys_gravity=False, x_speed=200, y_speed=0, friction=0, mass=10, bounciness=1.0
    )
    block.start_physics(
        obeys_gravity=False, can_move=False, friction=0, mass=10, bounciness=1.0
    )

    _run(400)

    # The block spans x=-20..20; a ball that passed through would be well past it.
    assert ball.x < 20, f"the ball passed through the block (x={ball.x})"


def test_wall_callback_still_fires_for_the_wall_it_watches():
    """The negative tests above must not pass by nothing working at all."""
    fired = []

    ball = play.new_circle(color="black", x=0, y=0, radius=10)
    ball.start_physics(
        obeys_gravity=False, x_speed=400, y_speed=0, friction=0, mass=10, bounciness=1.0
    )

    @ball.when_touching_wall(wall=WallSide.RIGHT)
    def touched_right():
        fired.append("right")
        play.stop_program()

    _run()

    assert fired, "a ball sent at the RIGHT wall should trigger its RIGHT-wall callback"
