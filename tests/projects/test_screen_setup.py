"""Screen setup game — realistic full-game project test.

A game that resizes the screen and sets the caption before creating sprites.
This is a common beginner pattern: configure the window first, then build the game.

This test verifies:
- screen.resize() before sprite creation
- screen.caption setter for window title
- screen.width / screen.height after resize
- sprites created after resize use correct coordinates
"""

MAX_FRAMES = 30


def test_screen_setup():
    import play
    from play.io.screen import screen

    frames_run = [0]

    # --- screen setup (must come before sprites) ---
    screen.resize(640, 480)
    screen.caption = "My Game"

    assert screen.width == 640
    assert screen.height == 480
    assert screen.caption == "My Game"

    # Verify edge properties updated
    assert screen.right == 320  # 640 / 2
    assert screen.left == -320
    assert screen.top == 240  # 480 / 2
    assert screen.bottom == -240

    # --- sprites (created after resize) ---
    player = play.new_circle(color="blue", x=0, y=0, radius=20)
    player.start_physics(obeys_gravity=False, can_move=False)

    # Sprite at the edge should be within bounds
    edge_box = play.new_box(color="red", x=screen.right - 20, y=0, width=10, height=10)
    edge_box.start_physics(obeys_gravity=False, can_move=False)

    score = play.new_text(words="0", x=0, y=screen.top - 25, font_size=20)

    # --- game loop ---
    @play.when_program_starts
    async def game_loop():
        for frame in range(MAX_FRAMES):
            await play.animate()
            frames_run[0] += 1

            score.words = str(frame)

        play.stop_program()

    play.start_program()

    # --- assertions ---
    assert frames_run[0] >= MAX_FRAMES
    assert score.words == str(MAX_FRAMES - 1)
    # Edge box should be near the right edge
    assert edge_box.x == screen.right - 20


if __name__ == "__main__":
    test_screen_setup()
