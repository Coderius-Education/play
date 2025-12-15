import pytest
import pygame
import pygame.surfarray as surfarray

num_frames = 0
max_frames = 100


def test_hide():
    import sys

    sys.path.insert(0, ".")
    import play

    image = play.new_image(
        image="tests/objects_attributes/yellow.jpg", size=10, transparency=0
    )
    box = play.new_box(x=200)
    circle = play.new_circle(x=0)

    @play.repeat_forever
    def move():
        global num_frames
        global pixel_array
        num_frames += 1

        box.hide()
        circle.hide()
        image.hide()

        if num_frames == max_frames:
            the_surface = play.pygame.display.get_surface()
            pixel_array = surfarray.array3d(the_surface)
            play.stop_program()

    play.start_program()

    for row in pixel_array:
        for r, g, b in row:
            if (r, g, b) != (255, 255, 255):
                pytest.fail(
                    f"expected rgb to be {(255,255,255)} but the actual values are {(r,g,b)}"
                )


if __name__ == "__main__":
    test_hide()
