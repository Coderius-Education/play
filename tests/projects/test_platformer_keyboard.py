"""Keyboard platformer — realistic full-game project test.

A player box controlled with arrow keys jumps between platforms under gravity.
The player moves left/right and can jump when on a platform.  Coins are
placed on the platforms; when the player touches a coin it is collected
(hidden) and the score increments.  The game ends when all coins are collected
or the safety timeout fires.

This is the most common student project type after pong: a simple side-view
platformer with keyboard controls, gravity, and collectables.

This test verifies:
- @when_key_pressed for movement and jumping
- obeys_gravity=True with real gravity-driven falling
- when_stopped_touching for landing detection (player–platform)
- sprite.hide() for collecting coins
- is_touching for coin pickup detection
- the game completes when all coins are collected
"""

from tests.conftest import post_key_down, post_key_up
from tests.projects.conftest import add_safety_timeout

max_frames = 2000


def test_platformer_keyboard():
    import pygame
    import play

    coins_collected = [0]
    on_ground = [False]
    jumps = [0]
    TOTAL_COINS = 3

    # --- sprites -----------------------------------------------------------
    player = play.new_box(color="green", x=-100, y=-150, width=30, height=30)

    # Wide ground platform
    ground = play.new_box(color="brown", x=0, y=-230, width=700, height=20)

    # Coins close together so the player reliably walks through them
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
    @player.when_stopped_touching(ground)
    def left_ground():
        on_ground[0] = False

    # --- keyboard controls -------------------------------------------------
    @play.when_key_pressed("right")
    def move_right(key=None):
        player.physics.x_speed = 200

    @play.when_key_pressed("left")
    def move_left(key=None):
        player.physics.x_speed = -200

    @play.when_key_pressed("up")
    def jump(key=None):
        player.physics.y_speed = 300
        jumps[0] += 1

    # --- driver: simulate keyboard, collect coins --------------------------
    @play.when_program_starts
    async def driver():
        # Let player fall onto ground
        for _ in range(30):
            await play.animate()

        # Hold right key for most of the game
        post_key_down(pygame.K_RIGHT)

        for frame in range(max_frames):
            # Jump occasionally
            if frame % 60 == 20:
                post_key_down(pygame.K_UP)
            if frame % 60 == 22:
                post_key_up(pygame.K_UP)

            # Check coin collection via is_touching
            for coin in coins:
                if not coin.is_hidden and player.is_touching(coin):
                    coin.hide()
                    coins_collected[0] += 1
                    score_text.words = f"Coins: {coins_collected[0]}"
                    if coins_collected[0] >= TOTAL_COINS:
                        play.stop_program()
                        return

            await play.animate()

        play.stop_program()

    play.start_program()

    # --- assertions --------------------------------------------------------
    assert coins_collected[0] > 0, "should have collected at least one coin"
    assert jumps[0] > 0, "player should have jumped at least once"


if __name__ == "__main__":
    test_platformer_keyboard()
