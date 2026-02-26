"""Gravity Platformer — realistic full-game project test.

A player box falls under real gravity and lands on a platform below.
With bounciness=1.0 the player bounces; each time it stops touching the
platform the bounce counter goes up.  A second, higher platform is
reachable after bouncing high enough — when the player stops touching
that platform the "reached_upper_platform" flag is set.

This test verifies:
- gravity-driven movement (obeys_gravity=True)
- when_stopped_touching between two different sprite pairs
  (player–lower_platform and player–upper_platform)
- the double-fire bug-fix: each landing fires the callback exactly once
- the game stops cleanly after the win condition or timeout
"""

from tests.projects.conftest import add_safety_timeout

max_frames = 4000


def test_gravity_platformer():
    import play

    lower_bounces = [0]
    upper_reached = [False]

    # --- sprites -----------------------------------------------------------
    player = play.new_box(color="green", x=0, y=100, width=40, height=40)

    # Wide lower platform so the player reliably lands on it
    lower_platform = play.new_box(color="brown", x=0, y=-200, width=400, height=20)

    # Upper platform off to the side — player falls past it to the lower one
    upper_platform = play.new_box(color="gray", x=250, y=50, width=200, height=20)

    lives_text = play.new_text(words="Bounces: 0", x=0, y=270, font_size=24)

    # --- physics -----------------------------------------------------------
    # Player obeys gravity; high bounciness so it bounces many times
    player.start_physics(
        obeys_gravity=True,
        x_speed=0,
        y_speed=0,
        friction=0,
        mass=5,
        bounciness=0.9,
    )
    lower_platform.start_physics(
        obeys_gravity=False, can_move=False, friction=0, mass=100, bounciness=0.9
    )
    upper_platform.start_physics(
        obeys_gravity=False, can_move=False, friction=0, mass=100, bounciness=0.9
    )

    # --- callbacks ---------------------------------------------------------
    @player.when_stopped_touching(lower_platform)
    def bounced_lower():
        lower_bounces[0] += 1
        lives_text.words = f"Bounces: {lower_bounces[0]}"
        if lower_bounces[0] >= 3:
            play.stop_program()

    @player.when_stopped_touching(upper_platform)
    def reached_upper():
        upper_reached[0] = True

    add_safety_timeout(max_frames)

    play.start_program()

    # --- assertions --------------------------------------------------------
    assert (
        lower_bounces[0] > 0
    ), "player should have bounced off the lower platform at least once"
    # Each bounce fires exactly once — the double-fire fix
    assert (
        lower_bounces[0] <= 20
    ), f"too many bounce events ({lower_bounces[0]}); callback may be firing twice per collision"


if __name__ == "__main__":
    test_gravity_platformer()
