import pytest

num_frames = 0
max_frames = 100


def test_hide():

    import pygame
    import pygame.surfarray as surfarray
    import play

    image = play.new_image(
        image="tests/objects_attributes/yellow.jpg", size=10, transparency=0
    )
    image_physics = play.new_image(
        image="tests/objects_attributes/yellow.jpg", size=10, transparency=0
    )
    image_physics.start_physics(obeys_gravity=False)

    box = play.new_box(x=200)
    box_physics = play.new_box(x=200)
    box_physics.start_physics(obeys_gravity=False)

    circle = play.new_circle(x=0)
    circle_physics = play.new_circle(x=0)
    circle_physics.start_physics(obeys_gravity=False)

    sprites = [image, image_physics, box, box_physics, circle, circle_physics]
    methods = ["hide", "show", "remove"]

    for method_name in methods:
        for sprite in sprites:
            callable_method = getattr(sprite, method_name)
            callable_method()
            callable_method()

    @play.repeat_forever
    def move():
        global num_frames
        global pixel_array
        num_frames += 1

        if num_frames == max_frames:
            the_surface = play.pygame.display.get_surface()
            pixel_array = surfarray.array3d(the_surface)
            play.stop_program()

    play.start_program()

    for row_index, row in enumerate(pixel_array):
        for column_index, (r, g, b) in enumerate(row):
            if (r, g, b) != (255, 255, 255):
                pytest.fail(
                    f"expected rgb to be {(255,255,255)} but the actual values are {(r,g,b)}"
                )


if __name__ == "__main__":
    test_hide()
