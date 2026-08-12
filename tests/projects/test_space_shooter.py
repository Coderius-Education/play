"""Space Shooter — realistic full-game project test.

A player ship sits at the bottom of the screen and fires bullets upward at an
enemy sweeping back and forth near the top.  When a bullet stops touching the
enemy the hit counter goes up and the bullet resets below the screen.  The
game ends when three hits are scored.

This test verifies:
- when_stopped_touching between a bullet and a moving enemy
- resetting a sprite position inside a when_stopped_touching callback
- the game stops on its win condition rather than on the safety timeout

Shots have to actually connect for any of that to be exercised.  An earlier
version aimed each bullet at the enemy's x *at the moment of firing* while the
enemy moved on at 150px/s, so nearly every one of ~45 shots missed and the
test spent 15 seconds to prove a single hit.  The bullet now carries the
enemy's horizontal velocity, so it tracks the enemy over its flight the way a
led shot does, and the run needs three hits instead of one.
"""

max_frames = 1500
WINNING_HITS = 3
BULLET_SPEED = 500


def test_space_shooter():
    import play

    hits = [0]
    shots_fired = [0]
    won = [False]

    # --- sprites -----------------------------------------------------------
    # Player ship at the bottom
    player = play.new_box(color="blue", x=0, y=-230, width=50, height=20)

    # Enemy that sweeps left-right near the top
    enemy = play.new_box(color="red", x=0, y=200, width=60, height=30)

    # A single reusable bullet — starts hidden at the bottom of the screen
    bullet = play.new_circle(color="yellow", x=0, y=-290, radius=6)

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

    # A sensor: it registers the hit without knocking the enemy off its lane,
    # so the second and third shots face the same geometry as the first.
    bullet.start_physics(
        obeys_gravity=False,
        x_speed=0,
        y_speed=0,
        friction=0,
        mass=1,
        bounciness=1.0,
        sensor=True,
    )

    # --- bullet hits enemy -------------------------------------------------
    @bullet.when_stopped_touching(enemy)
    def bullet_hit():
        hits[0] += 1
        score_text.words = f"Hits: {hits[0]}"
        # Reset bullet to below screen so it can be re-fired
        bullet.x = 0
        bullet.y = -290
        bullet.physics.x_speed = 0
        bullet.physics.y_speed = 0
        if hits[0] >= WINNING_HITS:
            won[0] = True
            play.stop_program()

    # --- fire bullets on a timer ------------------------------------------
    @play.when_program_starts
    async def fire_loop():
        for frame in range(max_frames):
            await play.animate()
            # Fire a new bullet every 20 frames if it is parked at the bottom
            if frame % 20 == 0 and bullet.y < -250:
                bullet.x = enemy.x
                bullet.y = player.y + 30
                # Match the enemy's horizontal velocity so the bullet stays
                # under it for the whole flight instead of aiming where it was.
                bullet.physics.x_speed = enemy.physics.x_speed
                bullet.physics.y_speed = BULLET_SPEED
                shots_fired[0] += 1
        play.stop_program()

    play.start_program()

    # --- assertions --------------------------------------------------------
    assert (
        shots_fired[0] > 0
    ), "no shots were fired — when_program_starts may not have run"
    assert hits[0] == WINNING_HITS, (
        f"expected {WINNING_HITS} hits from {shots_fired[0]} shots, got "
        f"{hits[0]}; collision detection or the bullet's aim may be broken"
    )
    assert won[0], "the game should end on its third hit, not on the safety timeout"
    assert score_text.words == f"Hits: {hits[0]}"
    assert bullet.y < -250, "the bullet should be parked below the screen after a hit"


if __name__ == "__main__":
    test_space_shooter()
