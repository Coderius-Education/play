import pytest
import play
import pygame


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_type_handling_bad_colors():
    """
    Passing an integer to a color field should raise an error.
    """
    with pytest.raises((ValueError, AttributeError)):
        play.new_circle(color=123, x=0, y=0, radius=10)


def test_type_handling_bad_numbers():
    """
    Passing absolute garbage to a coordinate should raise an error.
    """
    with pytest.raises((ValueError, TypeError)):
        play.new_box(color="blue", x="Not a number", y=0, width=10, height=10)


def test_type_handling_physics_args():
    """
    Passing wrong types to physics should be caught gracefully.
    """
    box = play.new_box(color="red", x=0, y=0, width=10, height=10)
    with pytest.raises((TypeError, ValueError)):
        # Bounciness expects a float/int, not a list.
        box.start_physics(bounciness=[1, 2])
