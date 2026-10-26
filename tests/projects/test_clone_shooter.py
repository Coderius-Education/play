"""Clone-based shooter — realistic full-game project test.

A player at the left side of the screen shoots bullets to the right by
cloning a prototype bullet. Bullets that reach the right edge are removed.
An enemy on the right side can be hit; it then dodges upwards, so the shots
already in flight miss and leave at the edge. Two hits win the game.

This test verifies:
- sprite.clone() for creating bullets
- sprite.remove() for cleanup
- sprite.right / sprite.left edge properties for boundary detection
- managing a list of cloned sprites
"""

MAX_FRAMES = 300
BULLET_SPEED = 600
WINNING_HITS = 2


def test_clone_shooter():
    import play
    from play.io.screen import screen

    score = [0]
    frames_run = [0]
    bullets_created = [0]
    edge_removals = [0]
    removed = []

    # --- sprites ---
    player = play.new_box(color="blue", x=screen.left + 40, y=0, width=20, height=30)
    player.start_physics(obeys_gravity=False, can_move=False)

    # Prototype bullet (hidden, used only for cloning)
    bullet_proto = play.new_circle(color="yellow", x=-999, y=-999, radius=5)
    bullet_proto.start_physics(obeys_gravity=False, can_move=False)
    bullet_proto.hide()

    # Off the bullets' 10px grid: see the is_touching xfail in test_edge_cases.
    enemy = play.new_box(color="red", x=screen.right - 57, y=0, width=20, height=40)
    enemy.start_physics(obeys_gravity=False, can_move=False)

    score_text = play.new_text(words="Hits: 0", x=0, y=screen.top - 30, font_size=25)

    bullets = []

    def fire_bullet():
        """Clone the prototype and launch it to the right, at the enemy's height."""
        b = bullet_proto.clone()
        b.x = player.x + 20
        b.y = enemy.y
        b.show()
        b.start_physics(
            obeys_gravity=False, x_speed=BULLET_SPEED, y_speed=0, bounciness=0
        )
        bullets.append(b)
        bullets_created[0] += 1

    def remove_bullet(b):
        b.remove()
        bullets.remove(b)
        removed.append(b)

    # --- game loop ---
    @play.when_program_starts
    async def game_loop():
        for frame in range(MAX_FRAMES):
            await play.animate()
            frames_run[0] += 1

            if frame % 20 == 0:
                fire_bullet()
            for b in list(bullets):
                if b.right > screen.right - 5:
                    remove_bullet(b)
                    edge_removals[0] += 1
                elif b.is_touching(enemy):
                    score[0] += 1
                    score_text.words = f"Hits: {score[0]}"
                    remove_bullet(b)
                    enemy.y = 50

            if score[0] >= WINNING_HITS:
                play.stop_program()
                return

        play.stop_program()

    play.start_program()

    # --- assertions ---
    assert score[0] == WINNING_HITS, f"expected {WINNING_HITS} hits, got {score[0]}"
    assert frames_run[0] < MAX_FRAMES, "the game should end on its last hit"
    assert score_text.words == f"Hits: {WINNING_HITS}"
    assert edge_removals[0] >= 1, "the shots that missed should leave at the edge"
    assert bullets_created[0] == len(removed) + len(bullets)
    assert not any(b.alive() for b in removed), "removed bullets should be gone"
    assert all(b.alive() and b.is_shown for b in bullets)
    assert bullet_proto.is_hidden and (bullet_proto.x, bullet_proto.y) == (-999, -999)


if __name__ == "__main__":
    test_clone_shooter()
