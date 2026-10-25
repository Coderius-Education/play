"""screen.when_resized runs when the player resizes the window."""

import pygame

from play.io.screen import screen
from tests.events.frames import play_frames


def _resize(width, height):
    """A VIDEORESIZE event, as the window sends when the player drags its edge."""
    return pygame.event.Event(pygame.VIDEORESIZE, {"w": width, "h": height})


def test_when_resized_runs_with_the_new_size_in_place():
    sizes = []

    @screen.when_resized
    def layout():
        sizes.append(screen.size)

    play_frames([_resize(1000, 700)], [], [_resize(640, 480)])

    assert sizes == [(1000, 700), (640, 480)]
    assert pygame.display.get_surface().get_size() == (640, 480)


def test_when_resized_leaves_the_function_callable():
    @screen.when_resized
    def layout():
        return "laid out"

    assert layout() == "laid out"
