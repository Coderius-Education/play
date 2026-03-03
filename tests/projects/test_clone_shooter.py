"""Clone-based shooter — realistic full-game project test.

A player at the left side of the screen shoots bullets to the right by
cloning a prototype bullet. Bullets that reach the right edge are removed.
An enemy on the right side can be hit.

This test verifies:
- sprite.clone() for creating bullets
- sprite.remove() for cleanup
- sprite.right / sprite.left edge properties for boundary detection
- managing a list of cloned sprites
"""

MAX_FRAMES = 150


def test_clone_shooter():
    import play
    from play.io.screen import screen

    score = [0]
    frames_run = [0]
    bullets_created = [0]
    bullets_removed = [0]

    # --- sprites ---
    player = play.new_box(color="blue", x=screen.left + 40, y=0, width=20, height=30)
    player.start_physics(obeys_gravity=False, can_move=False)

    # Prototype bullet (hidden, used only for cloning)
    bullet_proto = play.new_circle(color="yellow", x=-999, y=-999, radius=5)
    bullet_proto.start_physics(obeys_gravity=False, can_move=False)
    bullet_proto.hide()

    enemy = play.new_box(color="red", x=screen.right - 60, y=0, width=20, height=40)
    enemy.start_physics(obeys_gravity=False, can_move=False)

    score_text = play.new_text(words="Hits: 0", x=0, y=screen.top - 30, font_size=25)

    bullets = []

    def fire_bullet():
        """Clone the prototype and launch it to the right."""
        b = bullet_proto.clone()
        b.x = player.x + 20
        b.y = player.y
        b.show()
        b.start_physics(obeys_gravity=False, x_speed=300, y_speed=0, bounciness=0)
        bullets.append(b)
        bullets_created[0] += 1

    # --- game loop ---
    @play.when_program_starts
    async def game_loop():
        for frame in range(MAX_FRAMES):
            await play.animate()
            frames_run[0] += 1

            if score[0] >= 2:
                play.stop_program()
                return

            # Fire a bullet every 20 frames
            if frame % 20 == 0:
                fire_bullet()

            # Check bullets for off-screen or hit
            for b in list(bullets):
                # Use edge property to check boundary
                if b.right > screen.right - 5:
                    b.remove()
                    bullets.remove(b)
                    bullets_removed[0] += 1
                elif b.is_touching(enemy):
                    score[0] += 1
                    score_text.words = f"Hits: {score[0]}"
                    b.remove()
                    bullets.remove(b)
                    bullets_removed[0] += 1
                    # Respawn enemy at a different y
                    enemy.y = -enemy.y if enemy.y >= 0 else 50

        play.stop_program()

    play.start_program()

    # --- assertions ---
    assert frames_run[0] >= 1, "Game loop never ran"
    assert (
        bullets_created[0] >= 2
    ), f"Expected >=2 bullets created, got {bullets_created[0]}"
    assert (
        bullets_removed[0] >= 1
    ), f"Expected >=1 bullet removed, got {bullets_removed[0]}"
    assert score[0] >= 1, f"Expected at least 1 hit, got {score[0]}"


if __name__ == "__main__":
    test_clone_shooter()
