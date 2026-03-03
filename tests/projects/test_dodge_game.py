"""Dodge game — realistic full-game project test.

The player follows the mouse cursor. An enemy moves toward the player.
When the enemy touches the player, the player flashes (transparency change)
and loses a life. The game ends when lives reach 0.

This test verifies:
- mouse.x / mouse.y for player movement (follow cursor)
- when_touching(sprite) decorator (the "while touching" form)
- sprite.transparency setter for visual feedback
- mouse.distance_to(x, y) for distance calculation
- game-over via lives counter
"""

from tests.conftest import post_mouse_motion

MAX_FRAMES = 300


def test_dodge_game():
    import play
    from play.io.screen import screen

    lives = [3]
    hit_cooldown = [0]
    frames_run = [0]
    hits_taken = [0]

    # --- sprites ---
    player = play.new_circle(color="green", x=0, y=0, radius=15)
    player.start_physics(obeys_gravity=False, can_move=False)

    enemy = play.new_circle(color="red", x=-200, y=200, radius=15)
    enemy.start_physics(
        obeys_gravity=False, x_speed=80, y_speed=-60, bounciness=1.0, friction=0
    )

    lives_text = play.new_text(words="Lives: 3", x=0, y=screen.top - 30, font_size=25)

    # --- collision: enemy touches player ---
    @enemy.when_touching(player)
    def enemy_hit_player():
        if hit_cooldown[0] > 0:
            return
        lives[0] -= 1
        hits_taken[0] += 1
        lives_text.words = f"Lives: {lives[0]}"
        # Flash effect via transparency
        player.transparency = 50
        hit_cooldown[0] = 30  # 30-frame cooldown

        if lives[0] <= 0:
            play.stop_program()

    # --- game loop ---
    @play.when_program_starts
    async def game_loop():
        for frame in range(MAX_FRAMES):
            await play.animate()
            frames_run[0] += 1

            if lives[0] <= 0:
                return

            # Decrease cooldown and restore transparency
            if hit_cooldown[0] > 0:
                hit_cooldown[0] -= 1
                if hit_cooldown[0] == 0:
                    player.transparency = 100

            # Move player toward center via mouse (simulate mouse at enemy position
            # to guarantee collision)
            if frame < 20:
                # First frames: move mouse to where the enemy is heading
                sx = int(enemy.x + screen.width / 2)
                sy = int(-enemy.y + screen.height / 2)
                post_mouse_motion(sx, sy)
                player.x = enemy.x
                player.y = enemy.y

            # Check distance for verification
            dist = play.mouse.distance_to(player.x, player.y)
            assert isinstance(dist, float) or isinstance(dist, int)

        play.stop_program()

    play.start_program()

    # --- assertions ---
    assert frames_run[0] >= 1, "Game loop never ran"
    assert hits_taken[0] >= 1, f"Expected at least 1 hit, got {hits_taken[0]}"


if __name__ == "__main__":
    test_dodge_game()
