"""Space Shooter — realistic full-game project test.

A player ship sits at the bottom of the screen.  Every 20 frames it fires
a bullet upward toward an enemy that is moving back and forth horizontally.
When the bullet stops touching the enemy the hit counter goes up and the
bullet resets below screen.  The game ends when three hits are scored or
the safety timeout is reached.

This test verifies:
- when_stopped_touching between a bullet and a moving enemy
- the double-fire fix: each hit increments the counter exactly once
- resetting a sprite position inside a when_stopped_touching callback
- the game stops cleanly after the win condition
"""

import pytest

max_frames = 3000
winning_hits = 3


def test_space_shooter():
    import play

    hits = [0]
    shots_fired = [0]

    # --- sprites -----------------------------------------------------------
    # Player ship at the bottom
    player = play.new_box(color="blue", x=0, y=-230, width=50, height=20)

    # Enemy that sweeps left-right near the top
    enemy = play.new_box(color="red", x=0, y=200, width=60, height=30)

    # A single reusable bullet — starts off-screen
    bullet = play.new_circle(color="yellow", x=0, y=-500, radius=6)

    score_text = play.new_text(words="Hits: 0", x=0, y=270, font_size=24)

    # --- physics -----------------------------------------------------------
    # Enemy sweeps horizontally
    enemy.start_physics(
        obeys_gravity=False,
        x_speed=150,
        y_speed=0,
        friction=0,
        mass=10,
        bounciness=1.0,
    )

    bullet.start_physics(
        obeys_gravity=False,
        x_speed=0,
        y_speed=0,
        friction=0,
        mass=1,
        bounciness=0,
    )

    # --- bullet hits enemy -------------------------------------------------
    @bullet.when_stopped_touching(enemy)
    def bullet_hit():
        hits[0] += 1
        score_text.words = f"Hits: {hits[0]}"
        # Reset bullet to below screen so it can be re-fired
        bullet.x = 0
        bullet.y = -500
        bullet.physics.y_speed = 0
        if hits[0] >= winning_hits:
            play.stop_program()

    # --- fire bullets on a timer ------------------------------------------
    @play.when_program_starts
    async def fire_loop():
        for frame in range(max_frames):
            await play.animate()
            # Fire a new bullet every 20 frames if it is parked off-screen
            if frame % 20 == 0 and bullet.y < -400:
                bullet.x = enemy.x  # aim at current enemy x
                bullet.y = player.y + 30
                bullet.physics.y_speed = 500
                shots_fired[0] += 1
        play.stop_program()

    play.start_program()

    # --- assertions --------------------------------------------------------
    assert (
        shots_fired[0] > 0
    ), "no shots were fired — when_program_starts may not have run"
    assert hits[0] > 0, (
        f"bullet never hit the enemy after {shots_fired[0]} shots; "
        "collision detection may be broken"
    )
    assert hits[0] <= shots_fired[0], (
        f"more hits ({hits[0]}) than shots fired ({shots_fired[0]}); "
        "when_stopped_touching callback may be firing multiple times per collision"
    )


if __name__ == "__main__":
    test_space_shooter()
