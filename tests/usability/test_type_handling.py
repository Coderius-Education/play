import pytest
import play
import pygame


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_type_forgiveness_coordinates():
    """
    Beginners might accidentally pass strings instead of integers.
    The library should be forgiving and auto-cast string numbers gracefully.
    """
    # Create with string coordinates
    box = play.new_box(color="red", x="50", y="-30", width="100", height=100)

    # Assert auto-casting worked
    assert box.x == 50
    assert box.y == -30
    assert box.width == 100

    # Setting properties with strings after init
    box.x = "200"
    assert box.x == 200


def test_type_handling_bad_colors():
    """
    Passing an integer to a color field should raise a clear beginner-friendly ValueError.
    """
    # Some beginners might try passing raw integers instead of strings or RGB tuples.
    # We want to ensure it raises our custom ValueError with a helpful message,
    # rather than a raw dictionary AttributeError.
    with pytest.raises(ValueError) as exc_info:
        play.new_circle(color=123, x=0, y=0, radius=10)

    assert (
        "understand" in str(exc_info.value).lower()
        or "color" in str(exc_info.value).lower()
    )


def test_type_handling_bad_numbers():
    """
    Passing absolute garbage to a coordinate should raise a nice ValueError.
    """
    with pytest.raises(ValueError) as exc_info:
        play.new_box(color="blue", x="Not a number", y=0, width=10, height=10)

    assert (
        "number" in str(exc_info.value).lower()
        or "invalid" in str(exc_info.value).lower()
    )


def test_type_handling_physics_args():
    """
    Passing wrong types to physics should be caught gracefully.
    """
    box = play.new_box(color="red", x=0, y=0, width=10, height=10)
    with pytest.raises((TypeError, ValueError)):
        # Bounciness expects a float/int, not a list.
        box.start_physics(bounciness=[1, 2])
