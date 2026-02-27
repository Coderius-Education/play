"""Hover button menu — realistic full-game project test.

A simple menu with two buttons.  When the mouse hovers over a button it
changes color (highlight effect).  Clicking a button triggers an action.
This is how students typically build menus with hover feedback.

This test verifies:
- play.mouse.is_touching(sprite) for hover detection
- per-frame polling of mouse position against sprites
- sprite color change on hover
- when_clicked for button activation
- the game completes after a button is clicked
"""

from tests.conftest import post_mouse_motion, post_mouse_down, post_mouse_up

max_frames = 200


def test_hover_button():
    import play
    from play.io.screen import screen

    hover_detected = [False]
    button_clicked = [False]
    hover_frames = [0]

    # --- sprites -----------------------------------------------------------
    button = play.new_box(color="gray", x=0, y=0, width=120, height=40)
    label = play.new_text(words="Click me", x=0, y=0, font_size=20)

    # --- hover detection (polling) -----------------------------------------
    @play.repeat_forever
    def check_hover():
        if play.mouse.is_touching(button):
            button.color = "lightblue"
            hover_detected[0] = True
            hover_frames[0] += 1
        else:
            button.color = "gray"

    # --- click handler -----------------------------------------------------
    @button.when_clicked
    def on_click():
        button_clicked[0] = True
        label.words = "Clicked!"
        play.stop_program()

    # --- driver: move mouse over button, then click ------------------------
    @play.when_program_starts
    async def driver():
        # Move mouse to center of the button (screen coords)
        sx = int(screen.width / 2)
        sy = int(screen.height / 2)

        # First hover over the button for a few frames
        post_mouse_motion(sx, sy)
        for _ in range(20):
            await play.animate()

        # Click the button
        post_mouse_down(sx, sy)
        await play.animate()
        post_mouse_up(sx, sy)
        await play.animate()

        # Safety: wait a few more frames for the click to process
        for _ in range(max_frames):
            await play.animate()
        play.stop_program()

    play.start_program()

    # --- assertions --------------------------------------------------------
    assert hover_detected[0], "mouse.is_touching(button) should have detected hover"
    assert hover_frames[0] > 0, "hover should have been detected for multiple frames"
    assert button_clicked[0], "button should have been clicked"


if __name__ == "__main__":
    test_hover_button()
