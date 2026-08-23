"""Dodge game — realistic full-game project test.

The player follows the mouse cursor. An enemy moves toward the player.
When the enemy touches the player, the player flashes (transparency change)
and loses a life. The game ends when lives reach 0.

This test verifies:
- mouse.x / mouse.y for player movement (follow cursor)
- when_touching(sprite) decorator (the "while touching" form)
- sprite.transparency setter for visual feedback, both applied and restored
- mouse.distance_to(x, y) for distance calculation
- game-over via the lives counter, reached rather than assumed

The player is steered onto the enemy for the whole run.  It used to be steered
there only for the first 20 frames, which was enough for a single hit out of
the three needed, so the game-over branch this test describes never ran and
`lives` was never asserted -- the run just played out its 300 frames.
"""

from tests.conftest import post_mouse_motion

MAX_FRAMES = 300
STARTING_LIVES = 3
HIT_COOLDOWN_FRAMES = 30


def test_dodge_game():
    import play
    from play.io.screen import screen

    lives = [STARTING_LIVES]
    hit_cooldown = [0]
    frames_run = [0]
    hits_taken = [0]
    flashes_restored = [0]
    closest_mouse_distance = [float("inf")]

    # --- sprites ---
    player = play.new_circle(color="green", x=0, y=0, radius=15)
    player.start_physics(obeys_gravity=False, can_move=False)

    enemy = play.new_circle(color="red", x=-200, y=200, radius=15)
    enemy.start_physics(
        obeys_gravity=False, x_speed=80, y_speed=-60, bounciness=1.0, friction=0
    )

    lives_text = play.new_text(
        words=f"Lives: {STARTING_LIVES}", x=0, y=screen.top - 30, font_size=25
    )

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
        hit_cooldown[0] = HIT_COOLDOWN_FRAMES

        if lives[0] <= 0:
            play.stop_program()

    # --- game loop ---
    @play.when_program_starts
    async def game_loop():
        for _ in range(MAX_FRAMES):
            await play.animate()
            frames_run[0] += 1

            if lives[0] <= 0:
                return

            # Decrease cooldown and restore transparency
            if hit_cooldown[0] > 0:
                hit_cooldown[0] -= 1
                if hit_cooldown[0] == 0:
                    player.transparency = 100
                    flashes_restored[0] += 1

            # Steer the player onto the enemy so the collision keeps happening
            # and the lives counter actually runs down.
            sx = int(enemy.x + screen.width / 2)
            sy = int(-enemy.y + screen.height / 2)
            post_mouse_motion(sx, sy)
            player.x = enemy.x
            player.y = enemy.y

            closest_mouse_distance[0] = min(
                closest_mouse_distance[0],
                play.mouse.distance_to(player.x, player.y),
            )

        play.stop_program()

    play.start_program()

    # --- assertions ---
    assert frames_run[0] >= 1, "Game loop never ran"
    assert (
        hits_taken[0] == STARTING_LIVES
    ), f"expected {STARTING_LIVES} hits to run the lives down, got {hits_taken[0]}"
    assert lives[0] == 0, f"lives should reach 0 for game over, got {lives[0]}"
    assert lives_text.words == "Lives: 0", "the lives display should show the game over"
    assert (
        frames_run[0] < MAX_FRAMES
    ), "the game should end on the lives counter, not by running out of frames"

    # The flash is applied on the last hit and never restored, because the game
    # ends there; earlier hits must have been restored.
    assert player.transparency == 50, "the player should be mid-flash at game over"
    assert flashes_restored[0] > 0, "the flash should be restored after the cooldown"

    # The cursor is put exactly where the player is, so distance_to should
    # report roughly zero rather than any old number.
    assert closest_mouse_distance[0] < 10, (
        "mouse.distance_to should report the cursor on top of the player, got "
        f"{closest_mouse_distance[0]}"
    )


if __name__ == "__main__":
    test_dodge_game()
