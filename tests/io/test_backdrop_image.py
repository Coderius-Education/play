"""The backdrop: a colour or an image drawn behind the sprites every frame."""

import pygame
import pytest

import play
from play.globals import globals_list


def _colour_drawn_at(x, y):
    """The colour on screen at window point (x, y) in the first frame."""
    seen = []

    @play.repeat_forever
    def look():
        seen.append(tuple(globals_list.display.get_at((x, y)))[:3])
        play.stop_program()

    play.start_program()
    return seen[0]


def test_a_backdrop_colour_fills_the_screen():
    play.set_backdrop("blue")

    assert _colour_drawn_at(10, 10) == (0, 0, 255)


def test_the_backdrop_is_white_until_it_is_set():
    assert _colour_drawn_at(10, 10) == (255, 255, 255)


def test_a_backdrop_image_is_drawn_from_the_top_left_corner(tmp_path):
    image = pygame.Surface((20, 20))
    image.fill((200, 30, 40))
    path = tmp_path / "backdrop.png"
    pygame.image.save(image, str(path))

    play.set_backdrop_image(str(path))

    assert _colour_drawn_at(5, 5) == (200, 30, 40)


def test_a_backdrop_image_that_does_not_exist_is_reported():
    with pytest.raises(FileNotFoundError):
        play.set_backdrop_image("nonexistent_image.png")
