import pygame
import pygame.surfarray as surfarray

import play


def test_hiding_showing_and_removing_twice_leaves_an_empty_screen():
    frames = [0]
    screen_pixels = [None]

    image = play.new_image(image="tests/objects_attributes/yellow.jpg", size=10)
    image_physics = play.new_image(image="tests/objects_attributes/yellow.jpg", size=10)
    image_physics.start_physics(obeys_gravity=False)

    box = play.new_box(x=200)
    box_physics = play.new_box(x=200)
    box_physics.start_physics(obeys_gravity=False)

    circle = play.new_circle(x=0)
    circle_physics = play.new_circle(x=0)
    circle_physics.start_physics(obeys_gravity=False)

    sprites = [image, image_physics, box, box_physics, circle, circle_physics]
    for method_name in ["hide", "show", "remove"]:
        for sprite in sprites:
            getattr(sprite, method_name)()
            getattr(sprite, method_name)()

    @play.repeat_forever
    def look():
        frames[0] += 1
        if frames[0] == 3:
            screen_pixels[0] = surfarray.array3d(pygame.display.get_surface())
            play.stop_program()

    play.start_program()

    assert (screen_pixels[0] == 255).all(), "a removed sprite is still on screen"
    assert not any(sprite.alive() for sprite in sprites)
