"""Tests for hide() and show() methods, both inside and outside callbacks."""

import pytest
import pygame
import pygame.surfarray as surfarray
import sys

sys.path.insert(0, ".")


def get_pixel_at(x, y):
    """Get the RGB value at screen coordinates (x, y)."""
    from play.io.screen import screen

    the_surface = pygame.display.get_surface()
    pixel_array = surfarray.array3d(the_surface)
    # Convert play coordinates to pygame coordinates
    screen_x = int(x + screen.width / 2)
    screen_y = int(screen.height / 2 - y)
    if 0 <= screen_x < pixel_array.shape[0] and 0 <= screen_y < pixel_array.shape[1]:
        return tuple(pixel_array[screen_x][screen_y])
    return None


def has_non_white_pixels_in_region(x, y, width, height):
    """Check if there are any non-white pixels in a region around (x, y)."""
    from play.io.screen import screen

    the_surface = pygame.display.get_surface()
    pixel_array = surfarray.array3d(the_surface)

    screen_x = int(x + screen.width / 2)
    screen_y = int(screen.height / 2 - y)

    for dx in range(-width // 2, width // 2):
        for dy in range(-height // 2, height // 2):
            px, py = screen_x + dx, screen_y + dy
            if 0 <= px < pixel_array.shape[0] and 0 <= py < pixel_array.shape[1]:
                r, g, b = pixel_array[px][py]
                if (r, g, b) != (255, 255, 255):
                    return True
    return False


def test_hide_outside_callback():
    """Test hide() called before start_program()."""
    import play

    num_frames = [0]
    box_visible = [None]

    box = play.new_box(x=0, y=0, width=50, height=50, color="red")
    box.hide()  # Hide before starting

    @play.repeat_forever
    def check():
        num_frames[0] += 1
        if num_frames[0] == 10:
            box_visible[0] = has_non_white_pixels_in_region(0, 0, 60, 60)
            play.stop_program()

    play.start_program()

    assert box_visible[0] == False, "Box should not be visible after hide()"


def test_show_outside_callback():
    """Test show() called before start_program() after hide()."""
    import play

    num_frames = [0]
    box_visible = [None]

    box = play.new_box(x=0, y=0, width=50, height=50, color="red")
    box.hide()
    box.show()  # Show again before starting

    @play.repeat_forever
    def check():
        num_frames[0] += 1
        if num_frames[0] == 10:
            box_visible[0] = has_non_white_pixels_in_region(0, 0, 60, 60)
            play.stop_program()

    play.start_program()

    assert box_visible[0] == True, "Box should be visible after show()"


def test_hide_inside_callback():
    """Test hide() called inside a callback."""
    import play

    num_frames = [0]
    visible_before = [None]
    visible_after = [None]

    box = play.new_box(x=0, y=0, width=50, height=50, color="blue")

    @play.repeat_forever
    def check():
        num_frames[0] += 1
        if num_frames[0] == 5:
            visible_before[0] = has_non_white_pixels_in_region(0, 0, 60, 60)
        if num_frames[0] == 10:
            box.hide()
        if num_frames[0] == 20:
            visible_after[0] = has_non_white_pixels_in_region(0, 0, 60, 60)
            play.stop_program()

    play.start_program()

    assert visible_before[0] == True, "Box should be visible before hide()"
    assert visible_after[0] == False, "Box should not be visible after hide()"


def test_show_inside_callback():
    """Test show() called inside a callback after hide()."""
    import play

    num_frames = [0]
    visible_after_show = [None]

    box = play.new_box(x=0, y=0, width=50, height=50, color="green")
    box.hide()

    @play.repeat_forever
    def check():
        num_frames[0] += 1
        if num_frames[0] == 10:
            box.show()
        if num_frames[0] == 20:
            visible_after_show[0] = has_non_white_pixels_in_region(0, 0, 60, 60)
            play.stop_program()

    play.start_program()

    assert visible_after_show[0] == True, "Box should be visible after show()"


def test_multiple_hide_calls():
    """Test that multiple hide() calls don't cause errors."""
    import play

    num_frames = [0]
    error_occurred = [False]

    box = play.new_box(x=0, y=0, width=50, height=50, color="red")

    @play.repeat_forever
    def check():
        num_frames[0] += 1
        try:
            if num_frames[0] == 5:
                box.hide()
            if num_frames[0] == 6:
                box.hide()  # Second hide should not error
            if num_frames[0] == 7:
                box.hide()  # Third hide should not error
        except Exception as e:
            error_occurred[0] = True
            print(f"Error: {e}")

        if num_frames[0] == 20:
            play.stop_program()

    play.start_program()

    assert error_occurred[0] == False, "Multiple hide() calls should not cause errors"


def test_multiple_show_calls():
    """Test that multiple show() calls don't cause errors."""
    import play

    num_frames = [0]
    error_occurred = [False]

    box = play.new_box(x=0, y=0, width=50, height=50, color="red")

    @play.repeat_forever
    def check():
        num_frames[0] += 1
        try:
            if num_frames[0] == 5:
                box.show()  # Already shown, should not error
            if num_frames[0] == 6:
                box.show()
            if num_frames[0] == 7:
                box.show()
        except Exception as e:
            error_occurred[0] = True
            print(f"Error: {e}")

        if num_frames[0] == 20:
            play.stop_program()

    play.start_program()

    assert error_occurred[0] == False, "Multiple show() calls should not cause errors"


def test_hide_then_change_physics_property():
    """Test that changing physics properties after hide() doesn't cause errors."""
    import play

    num_frames = [0]
    error_occurred = [False]
    error_message = [None]

    box = play.new_box(x=0, y=0, width=50, height=50, color="red")

    @play.repeat_forever
    def check():
        num_frames[0] += 1
        try:
            if num_frames[0] == 5:
                box.hide()
            if num_frames[0] == 10:
                box.physics.can_move = False  # This should not error
            if num_frames[0] == 15:
                box.physics.stable = True  # This should not error
            if num_frames[0] == 20:
                box.show()  # Show should work after property changes
        except Exception as e:
            error_occurred[0] = True
            error_message[0] = str(e)

        if num_frames[0] == 30:
            play.stop_program()

    play.start_program()

    assert (
        error_occurred[0] == False
    ), f"Changing physics properties after hide() should not error: {error_message[0]}"


def test_circle_hide_show():
    """Test hide/show on circle sprites."""
    import play

    num_frames = [0]
    visible_before = [None]
    visible_after_hide = [None]
    visible_after_show = [None]

    circle = play.new_circle(x=0, y=0, radius=30, color="purple")

    @play.repeat_forever
    def check():
        num_frames[0] += 1
        if num_frames[0] == 5:
            visible_before[0] = has_non_white_pixels_in_region(0, 0, 70, 70)
        if num_frames[0] == 10:
            circle.hide()
        if num_frames[0] == 20:
            visible_after_hide[0] = has_non_white_pixels_in_region(0, 0, 70, 70)
        if num_frames[0] == 25:
            circle.show()
        if num_frames[0] == 35:
            visible_after_show[0] = has_non_white_pixels_in_region(0, 0, 70, 70)
            play.stop_program()

    play.start_program()

    assert visible_before[0] == True, "Circle should be visible initially"
    assert visible_after_hide[0] == False, "Circle should not be visible after hide()"
    assert visible_after_show[0] == True, "Circle should be visible after show()"


def test_text_hide_show():
    """Test hide/show on text sprites."""
    import play

    num_frames = [0]
    visible_before = [None]
    visible_after_hide = [None]
    visible_after_show = [None]

    text = play.new_text(words="Hello", x=0, y=0, color="black", font_size=30)

    @play.repeat_forever
    def check():
        num_frames[0] += 1
        if num_frames[0] == 5:
            visible_before[0] = has_non_white_pixels_in_region(0, 0, 100, 50)
        if num_frames[0] == 10:
            text.hide()
        if num_frames[0] == 20:
            visible_after_hide[0] = has_non_white_pixels_in_region(0, 0, 100, 50)
        if num_frames[0] == 25:
            text.show()
        if num_frames[0] == 35:
            visible_after_show[0] = has_non_white_pixels_in_region(0, 0, 100, 50)
            play.stop_program()

    play.start_program()

    assert visible_before[0] == True, "Text should be visible initially"
    assert visible_after_hide[0] == False, "Text should not be visible after hide()"
    assert visible_after_show[0] == True, "Text should be visible after show()"


def test_hide_in_when_clicked_callback():
    """Test hide() called inside a when_clicked callback using pygame events."""
    import play
    from play.io.screen import screen

    num_frames = [0]
    box_hidden = [False]
    visible_after_click = [None]

    box = play.new_box(x=0, y=0, width=100, height=100, color="red")

    @box.when_clicked
    def on_click():
        box.hide()
        box_hidden[0] = True

    @play.repeat_forever
    def check():
        num_frames[0] += 1

        # Move mouse to box center so mouse.is_touching works
        if num_frames[0] == 9:
            screen_x = int(screen.width / 2)
            screen_y = int(screen.height / 2)
            motion_event = pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": (screen_x, screen_y), "rel": (0, 0), "buttons": (0, 0, 0)},
            )
            pygame.event.post(motion_event)

        # Post a real pygame click event at frame 10
        if num_frames[0] == 10:
            # Convert play coordinates (0, 0) to pygame screen coordinates
            screen_x = int(screen.width / 2)
            screen_y = int(screen.height / 2)
            # Post mouse button down event
            click_event = pygame.event.Event(
                pygame.MOUSEBUTTONDOWN, {"pos": (screen_x, screen_y), "button": 1}
            )
            pygame.event.post(click_event)

        if num_frames[0] == 12:
            # Post mouse button up event
            screen_x = int(screen.width / 2)
            screen_y = int(screen.height / 2)
            release_event = pygame.event.Event(
                pygame.MOUSEBUTTONUP, {"pos": (screen_x, screen_y), "button": 1}
            )
            pygame.event.post(release_event)

        if num_frames[0] == 30:
            visible_after_click[0] = has_non_white_pixels_in_region(0, 0, 110, 110)
            play.stop_program()

    play.start_program()

    assert box_hidden[0] == True, "Click callback should have been triggered"
    assert (
        visible_after_click[0] == False
    ), "Box should not be visible after hide() in callback"


def test_hide_show_rapid_toggle():
    """Test rapidly toggling hide/show doesn't cause issues."""
    import play

    num_frames = [0]
    error_occurred = [False]
    final_visible = [None]

    box = play.new_box(x=0, y=0, width=50, height=50, color="orange")

    @play.repeat_forever
    def check():
        num_frames[0] += 1
        try:
            # Rapidly toggle every frame for 20 frames
            if 10 <= num_frames[0] < 30:
                if num_frames[0] % 2 == 0:
                    box.hide()
                else:
                    box.show()

            # End with show
            if num_frames[0] == 30:
                box.show()

            if num_frames[0] == 40:
                final_visible[0] = has_non_white_pixels_in_region(0, 0, 60, 60)
                play.stop_program()

        except Exception as e:
            error_occurred[0] = True
            print(f"Error during rapid toggle: {e}")
            play.stop_program()

    play.start_program()

    assert error_occurred[0] == False, "Rapid toggle should not cause errors"
    assert final_visible[0] == True, "Box should be visible after ending with show()"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
