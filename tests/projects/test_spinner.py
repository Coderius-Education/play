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

    frames_run = [0]
    angles_seen = []
    distances = []

    # --- setup ---
    play.set_backdrop("lightblue")
    screen.caption = "Spinner Demo"

    spinner = play.new_box(color="orange", x=0, y=0, width=60, height=20)
    spinner.start_physics(obeys_gravity=False, can_move=False)

    label = play.new_text(words="Angle: 0", x=0, y=-100, font_size=20)

    # --- game loop ---
    @play.when_program_starts
    async def game_loop():
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

        play.stop_program()

    play.start_program()

    # --- assertions ---
    assert (
        frames_run[0] >= MAX_FRAMES
    ), f"Expected {MAX_FRAMES} frames, got {frames_run[0]}"

    # Verify angle changed over time
    assert len(set(angles_seen)) > 10, "Angle should have changed many times"
    assert angles_seen[-1] > angles_seen[0], "Angle should have increased"

    # Verify backdrop was set
    assert globals_list.backdrop_type == "color"
    assert globals_list.backdrop is not None

    # Verify caption was updated
    assert screen.caption == f"Spinner - frame {MAX_FRAMES - 1}"

    # Verify distance_to returned valid numbers
    assert all(isinstance(d, (int, float)) for d in distances)


if __name__ == "__main__":
    test_spinner()
