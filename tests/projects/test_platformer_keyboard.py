"""Keyboard platformer — realistic full-game project test.

A player box controlled with arrow keys falls onto a platform under gravity,
jumps, lands again, then walks right collecting coins.  The game ends when all
coins are collected or the safety timeout fires.

This is the most common student project type after pong: a simple side-view
platformer with keyboard controls, gravity, and collectables.

This test verifies:
- @when_key_pressed for movement and jumping
- obeys_gravity=True with real gravity-driven falling
- when_touching / when_stopped_touching for landing detection (player–platform)
- sprite.hide() for collecting coins
- is_touching for coin pickup detection
- the game completes when all coins are collected

The jump has to be tuned against gravity or none of that is actually
exercised.  An earlier version of this test jumped on a fixed 60-frame cadence
with y_speed=300 against gravity of -100 -- a six-second round trip
re-launched every second -- so the player was thrown up the screen before it
ever reached the platform and never touched it once.  Every collision callback
here was dead, and `player.y > ground.y` passed because the player was
airborne rather than because the platform held it up.  Hence: jump only when
standing on something, and only as high as gravity brings you back from.
"""

from tests.conftest import post_key_down, post_key_up

max_frames = 600
TOTAL_COINS = 3
JUMP_SPEED = 100  # rises 50px against gravity of -100: a 2-second round trip
WALK_SPEED = 200


def test_platformer_keyboard():
    import pygame
    import play

    coins_collected = [0]
    on_ground = [False]
    ground_contacts = [0]
    jumps = [0]
    seen = {}

    # --- sprites -----------------------------------------------------------
    player = play.new_box(color="green", x=-100, y=-150, width=30, height=30)

    # Wide ground platform
    ground = play.new_box(color="brown", x=0, y=-230, width=700, height=20)

    # Coins sit at the height of a player standing on the platform, so walking
    # right runs through all three of them.
    coins = [
        play.new_circle(color="yellow", x=-50 + i * 60, y=-200, radius=12)
        for i in range(TOTAL_COINS)
    ]

    score_text = play.new_text(words="Coins: 0", x=0, y=260, font_size=24)

    # --- physics -----------------------------------------------------------
    player.start_physics(
        obeys_gravity=True,
        x_speed=0,
        y_speed=0,
        friction=0,
        mass=5,
        bounciness=0.0,
    )
    ground.start_physics(obeys_gravity=False, can_move=False, bounciness=0.0)
    for coin in coins:
        coin.start_physics(obeys_gravity=False, can_move=False, bounciness=0.0)

    # --- landing detection -------------------------------------------------
    @player.when_touching(ground)
    def standing_on_ground():
        on_ground[0] = True
        ground_contacts[0] += 1

    @player.when_stopped_touching(ground)
    def left_ground():
        on_ground[0] = False

    # --- keyboard controls -------------------------------------------------
    @play.when_key_pressed("right")
    def move_right(key=None):
        player.physics.x_speed = WALK_SPEED

    @play.when_key_pressed("left")
    def move_left(key=None):
        player.physics.x_speed = -WALK_SPEED

    @play.when_key_pressed("up")
    def jump(key=None):
        # The way a student writes it: you can only jump off solid ground.
        if not on_ground[0]:
            return
        player.physics.y_speed = JUMP_SPEED
        jumps[0] += 1

    # --- driver: simulate keyboard, collect coins --------------------------
    @play.when_program_starts
    async def driver():
        async def wait_until(condition, limit=300):
            """Run frames until condition() holds. False if it never does."""
            for _ in range(limit):
                if condition():
                    return True
                await play.animate()
            return False

        # Fall onto the platform.
        seen["landed"] = await wait_until(lambda: on_ground[0])

        # One jump, and back down onto the platform.
        post_key_down(pygame.K_UP)
        await play.animate()
        post_key_up(pygame.K_UP)
        seen["left_ground"] = await wait_until(lambda: not on_ground[0])
        seen["landed_again"] = await wait_until(lambda: on_ground[0])

        # Walk right along the platform, through the coins.
        post_key_down(pygame.K_RIGHT)
        for _ in range(max_frames):
            for coin in coins:
                if not coin.is_hidden and player.is_touching(coin):
                    coin.hide()
                    coins_collected[0] += 1
                    score_text.words = f"Coins: {coins_collected[0]}"
            if coins_collected[0] >= TOTAL_COINS:
                break
            await play.animate()

        play.stop_program()

    play.start_program()

    # --- landing detection actually happened -------------------------------
    assert seen["landed"], "the player should fall onto the platform"
    assert seen["left_ground"], "the jump should lift the player off the platform"
    assert seen["landed_again"], "the player should come back down onto the platform"
    assert jumps[0] > 0, "player should have jumped at least once"
    assert (
        ground_contacts[0] > 0
    ), "when_touching(ground) should fire while the player stands on the platform"

    # --- coins -------------------------------------------------------------
    assert coins_collected[0] > 0, "should have collected at least one coin"

    # A counter that disagrees with the world is the bug worth catching: every
    # coin counted must actually be gone, and the scoreboard must say so.
    hidden_coins = [c for c in coins if c.is_hidden]
    assert (
        len(hidden_coins) == coins_collected[0]
    ), f"{coins_collected[0]} coins counted but {len(hidden_coins)} are hidden"
    assert score_text.words == f"Coins: {coins_collected[0]}"

    # Gravity plus a solid platform: the player ends up resting on top of it,
    # never through it. Measured against the platform's surface rather than its
    # centre, so sinking halfway into it is a failure too.
    platform_top = ground.y + ground.height / 2
    assert player.y > platform_top, (
        f"the player should rest on the platform (surface at {platform_top}), "
        f"but ended at y={player.y}"
    )


if __name__ == "__main__":
    test_platformer_keyboard()
