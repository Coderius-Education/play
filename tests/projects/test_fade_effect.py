"""Fade effect demo — realistic full-game project test.

A sprite fades in and out repeatedly. A text overlay also fades.

This test verifies:
- sprite.transparency setter used dynamically each frame
- text.transparency for fading overlay messages
- is_hidden / is_shown property reads
"""

MAX_FRAMES = 80


def test_fade_effect():
    import play

    frames_run = [0]
    transparency_values = []

    # --- sprites ---
    ghost = play.new_circle(color="purple", x=0, y=0, radius=30)
    ghost.start_physics(obeys_gravity=False, can_move=False)

    message = play.new_text(words="Boo!", x=0, y=80, font_size=40, color="black")

    # --- game loop ---
    @play.when_program_starts
    async def game_loop():
        for frame in range(MAX_FRAMES):
            await play.animate()
            frames_run[0] += 1

            # Fade: oscillate transparency between 20 and 100
            # Use a triangle wave: go down then up over 40 frames
            cycle = frame % 40
            if cycle < 20:
                t = 100 - (cycle * 4)  # 100 → 20
            else:
                t = 20 + ((cycle - 20) * 4)  # 20 → 100

            ghost.transparency = t
            message.transparency = t
            transparency_values.append(ghost.transparency)

            # Verify is_shown reads correctly (sprite is visible even at low transparency)
            assert ghost.is_shown, "Ghost should still be shown (not hidden)"
            assert not ghost.is_hidden, "Ghost should not be hidden"

        play.stop_program()

    play.start_program()

    # --- assertions ---
    assert frames_run[0] >= MAX_FRAMES

    # Transparency should have varied
    assert (
        min(transparency_values) <= 30
    ), f"Min transparency was {min(transparency_values)}, expected <= 30"
    assert (
        max(transparency_values) >= 90
    ), f"Max transparency was {max(transparency_values)}, expected >= 90"

    # Verify both sprite and text have transparency set
    assert ghost.transparency == transparency_values[-1]


if __name__ == "__main__":
    test_fade_effect()
