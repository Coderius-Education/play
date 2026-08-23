"""Gravity Platformer — realistic full-game project test.

A player box falls under real gravity onto a platform, bounces, and drifts
sideways onto a second platform further along.  Each time it stops touching a
platform that platform's bounce counter goes up.  The game ends once the
player has bounced on both platforms.

This test verifies:
- gravity-driven movement (obeys_gravity=True)
- when_stopped_touching against two different sprite pairs, with each pair
  asserted separately so a dead second registration cannot hide behind the
  first one firing
- the game stops on its win condition rather than on the safety timeout

The geometry is the point here.  An earlier version put the second platform at
x=250 while the player fell straight down from x=0 with no horizontal speed
and nothing to impart any: that platform could never be touched, its callback
could never run, and the flag it set was never asserted.  The player now
carries a horizontal speed, and the platforms are laid end to end along its
path, so both landings are ordinary consequences of the trajectory.
"""

from tests.projects.conftest import add_safety_timeout

max_frames = 1500

# Two platforms end to end with a gap far too narrow for a 40px player to fall
# through, so the second landing is a consequence of drifting right, not luck.
PLATFORM_Y = -200
PLATFORM_WIDTH = 390
PLATFORM_OFFSET = 205


def test_gravity_platformer():
    import play

    bounces_a = [0]
    bounces_b = [0]
    won = [False]

    # --- sprites -----------------------------------------------------------
    player = play.new_box(color="green", x=-300, y=100, width=40, height=40)

    platform_a = play.new_box(
        color="brown",
        x=-PLATFORM_OFFSET,
        y=PLATFORM_Y,
        width=PLATFORM_WIDTH,
        height=20,
    )
    platform_b = play.new_box(
        color="gray",
        x=PLATFORM_OFFSET,
        y=PLATFORM_Y,
        width=PLATFORM_WIDTH,
        height=20,
    )

    bounce_text = play.new_text(words="Bounces: 0", x=0, y=270, font_size=24)

    # --- physics -----------------------------------------------------------
    # Bouncy, and drifting right at a steady 60px/s: the first arc lands well
    # inside platform_a, the second well inside platform_b.
    player.start_physics(
        obeys_gravity=True,
        x_speed=60,
        y_speed=0,
        friction=0,
        mass=5,
        bounciness=0.9,
    )
    platform_a.start_physics(
        obeys_gravity=False, can_move=False, friction=0, mass=100, bounciness=0.9
    )
    platform_b.start_physics(
        obeys_gravity=False, can_move=False, friction=0, mass=100, bounciness=0.9
    )

    # --- callbacks ---------------------------------------------------------
    def _check_win():
        bounce_text.words = f"Bounces: {bounces_a[0] + bounces_b[0]}"
        if bounces_a[0] > 0 and bounces_b[0] > 0:
            won[0] = True
            play.stop_program()

    @player.when_stopped_touching(platform_a)
    def bounced_a():
        bounces_a[0] += 1
        _check_win()

    @player.when_stopped_touching(platform_b)
    def bounced_b():
        bounces_b[0] += 1
        _check_win()

    add_safety_timeout(max_frames)

    play.start_program()

    # --- assertions --------------------------------------------------------
    # Asserted per platform. Summing them would let a second registration that
    # never fires pass on the strength of the first one.
    assert bounces_a[0] > 0, "the player should have bounced off the first platform"
    assert bounces_b[0] > 0, (
        "the player should have drifted onto the second platform and bounced "
        f"there too; it ended at x={player.x}"
    )
    assert won[0], (
        "the game should have ended on its win condition rather than the "
        f"safety timeout (bounces: {bounces_a[0]} and {bounces_b[0]})"
    )
    assert bounce_text.words == f"Bounces: {bounces_a[0] + bounces_b[0]}"

    # Gravity plus solid platforms: the player is on top of them, not through.
    assert player.y > PLATFORM_Y, f"the player fell through the platforms to {player.y}"


if __name__ == "__main__":
    test_gravity_platformer()
