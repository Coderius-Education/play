"""play.screen: its size, edges and caption."""

import pygame
import pytest

import play
from play.io.screen import convert_pos, pos_convert


@pytest.mark.parametrize(
    "name, value",
    [
        ("width", 800),
        ("height", 600),
        ("size", (800, 600)),
        ("top", 300),
        ("bottom", -300),
        ("left", -400),
        ("right", 400),
    ],
)
def test_an_800_by_600_screen_has_its_edges_half_its_size_from_the_middle(name, value):
    assert getattr(play.screen, name) == value


def test_the_caption_starts_as_coderius_play():
    assert play.screen.caption == "coderius-play"
    assert pygame.display.get_caption()[0] == "coderius-play"


def test_setting_the_caption_changes_the_window_title():
    play.screen.caption = "My Game"

    assert play.screen.caption == "My Game"
    assert pygame.display.get_caption()[0] == "My Game"


@pytest.mark.parametrize(
    "play_point, window_point",
    [((0, 0), (400, 300)), ((-400, 300), (0, 0)), ((100, -50), (500, 350))],
)
def test_play_points_and_window_points_convert_both_ways(play_point, window_point):
    assert convert_pos(*play_point) == window_point
    assert pos_convert(*window_point) == play_point


@pytest.mark.parametrize(
    "name, value, size", [("width", 500, (500, 600)), ("height", 400, (800, 400))]
)
def test_setting_one_side_of_the_screen_resizes_the_window(name, value, size):
    setattr(play.screen, name, value)

    assert pygame.display.get_surface().get_size() == size
    assert play.screen.size == size
