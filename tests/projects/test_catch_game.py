"""Catch game — realistic full-game project test.

Fruits fall from the top of the screen. A basket catches them by being
positioned directly beneath. Each catch scores a point. Missed fruits
respawn at the top at a random x position.

This test verifies:
- sprite.bottom edge property for off-screen detection
- random_position() for spawn location
- is_touching() polling for collision (beginner pattern)
- score tracking via text.words
- respawning sprites to screen.top
"""

MAX_FRAMES = 200


def test_catch_game():
    import play
    from play.io.screen import screen

    score = [0]
    frames_run = [0]

    # --- sprites ---
    basket = play.new_box(color="brown", x=0, y=screen.bottom + 40, width=120, height=20)
    basket.start_physics(obeys_gravity=False, can_move=False)

    fruit = play.new_circle(color="red", x=0, y=100, radius=15)
    fruit.start_physics(obeys_gravity=True, x_speed=0, y_speed=0, bounciness=0)

    score_text = play.new_text(words="Score: 0", x=0, y=screen.top - 30, font_size=25)

    # --- fruit respawn helper ---
    def respawn_fruit():
        pos = play.random_position()
        fruit.x = pos.x
        fruit.y = 100
        fruit.physics.y_speed = 0
        fruit.physics.x_speed = 0

    # --- game loop: poll is_touching each frame (common beginner approach) ---
    @play.when_program_starts
    async def game_loop():
        for frame in range(MAX_FRAMES):
            await play.animate()
            frames_run[0] += 1

            if score[0] >= 3:
                play.stop_program()
                return

            # Move basket directly under fruit to guarantee catches
            basket.x = fruit.x

            # Poll for collision
            if fruit.is_touching(basket):
                score[0] += 1
                score_text.words = f"Score: {score[0]}"
                respawn_fruit()

            # If fruit fell below basket, respawn
            if fruit.bottom < basket.y - 30:
                respawn_fruit()

        play.stop_program()

    play.start_program()

    # --- assertions ---
    assert frames_run[0] >= 1, "Game loop never ran"
    assert score[0] >= 1, f"Expected at least 1 catch, got {score[0]}"


if __name__ == "__main__":
    test_catch_game()
