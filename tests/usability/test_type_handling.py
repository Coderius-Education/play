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


@pytest.mark.parametrize(
    "make, attribute",
    [
        (lambda: play.new_text("hi"), "color"),
        (lambda: play.new_box(), "color"),
        (lambda: play.new_box(), "border_color"),
        (lambda: play.new_circle(), "color"),
        (lambda: play.new_circle(), "border_color"),
    ],
    ids=["text", "box", "box border", "circle", "circle border"],
)
def test_a_misspelt_color_fails_where_it_is_set(make, attribute):
    # Not a frame later in the sprite loop, where the student's line is gone.
    sprite = make()
    with pytest.raises(ValueError, match="purpel"):
        setattr(sprite, attribute, "purpel")


def test_a_color_can_be_a_list():
    play.set_backdrop([255, 0, 0])
    box = play.new_box(color=[0, 0, 255])
    box.update()
    assert box.image.get_at(box.image.get_rect().center)[:3] == (0, 0, 255)


def test_a_font_size_with_decimals_is_rounded():
    text = play.new_text("hi", font_size=20.5)
    text.font_size = 30.4
    assert (
        text._pygame_font.get_height()
        == play.new_text("hi", font_size=30)._pygame_font.get_height()
    )


def test_no_font_means_the_default_font():
    text = play.new_text("hi", font=None)
    assert text.image.get_width() > 0
