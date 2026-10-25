"""Spinner / animation demo — realistic full-game project test.

A box rotates continuously. The backdrop is set to a custom color.
The screen caption is updated each frame.

This test verifies:
- sprite.angle dynamic assignment every frame (rotation)
- set_backdrop(color) for background color
- screen.caption setter
- mouse.distance_to(x, y)
"""

MAX_FRAMES = 60


def test_spinner():
    import play
    from play.io.screen import screen
    from play.globals import globals_list

    import pygame
    from tests.conftest import post_mouse_motion

    frames_run = [0]
    angles_seen = []
    distances = []
    spinner_sizes = {}
    backdrop_pixels = []

    # --- setup ---
    play.set_backdrop("lightblue")
    screen.caption = "Spinner Demo"

    spinner = play.new_box(color="orange", x=0, y=0, width=60, height=20)
    spinner.start_physics(obeys_gravity=False, can_move=False)

    label = play.new_text(words="Angle: 0", x=0, y=-100, font_size=20)

    # --- game loop ---
    @play.when_program_starts
    async def game_loop():
        post_mouse_motion(int(screen.width / 2 + 30), int(screen.height / 2 - 40))
        for frame in range(MAX_FRAMES):
            await play.animate()
            frames_run[0] += 1

            # Rotate the spinner
            spinner.angle = frame * 6  # 6 degrees per frame
            angles_seen.append(spinner.angle)
            label.words = f"Angle: {int(spinner.angle)}"

            # Update caption with frame count
            screen.caption = f"Spinner - frame {frame}"

            # Measure distance from mouse to spinner
            dist = play.mouse.distance_to(spinner.x, spinner.y)
            distances.append(dist)

            if frame in (1, 16):
                spinner_sizes[frame - 1] = spinner.rect.size
            backdrop_pixels.append(tuple(globals_list.display.get_at((5, 5)))[:3])

        play.stop_program()

    play.start_program()

    # --- assertions ---
    assert (
        frames_run[0] >= MAX_FRAMES
    ), f"Expected {MAX_FRAMES} frames, got {frames_run[0]}"

    # Verify angle changed over time
    assert len(set(angles_seen)) > 10, "Angle should have changed many times"
    assert angles_seen[-1] > angles_seen[0], "Angle should have increased"

    assert set(backdrop_pixels[1:]) == {(173, 216, 230)}, "the backdrop is light blue"

    assert screen.caption == f"Spinner - frame {MAX_FRAMES - 1}"
    assert pygame.display.get_caption()[0] == screen.caption

    assert spinner_sizes[0] == (60, 20), "unturned, the spinner lies flat"
    width, height = spinner_sizes[15]
    assert (
        height > width
    ), f"at 90 degrees it should stand upright, got {width}x{height}"

    assert distances[-1] == 50, "the mouse is 30 right and 40 up from the spinner"


if __name__ == "__main__":
    test_spinner()
