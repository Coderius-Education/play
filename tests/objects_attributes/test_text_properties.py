"""What changing a text's properties does to the text on screen."""

import logging

import pytest

import play
from tests.conftest import count_color, image_bytes

RED = (255, 0, 0)
BLUE = (0, 0, 255)


def test_new_words_are_drawn_and_can_be_touched_where_they_are_drawn():
    text = play.new_text(words="Hi", font_size=40)
    short_width = text.image.get_width()
    assert not text.is_touching((short_width, 0))

    text.words = "Hello there, everyone"
    text.update()

    assert text.words == "Hello there, everyone"
    assert text.image.get_width() > 3 * short_width
    assert text.is_touching((short_width, 0))


def test_a_number_given_as_words_is_drawn_like_the_same_number_as_text():
    text = play.new_text(words="hi")
    as_string = play.new_text(words="42")

    text.words = 42
    text.update()

    assert image_bytes(text) == image_bytes(as_string)


def test_a_new_text_colour_is_drawn_on_the_next_frame():
    text = play.new_text(words="Hello", color="red", font_size=50)
    assert count_color(text.image, RED) > 0

    text.color = "blue"
    text.update()

    assert text.color == "blue"
    assert count_color(text.image, BLUE) > 0
    assert count_color(text.image, RED) == 0


def test_a_mistyped_text_colour_is_refused_where_it_is_set():
    text = play.new_text(words="Hello", color="red")

    with pytest.raises(ValueError, match="blu"):
        text.color = "blu"

    assert text.color == "red"


def test_a_bigger_font_size_draws_bigger_letters_that_can_be_touched():
    text = play.new_text(words="Hello", font_size=20)
    small = text.image.get_size()
    assert not text.is_touching((0, small[1]))

    text.font_size = 60
    text.update()

    assert text.font_size == 60
    assert text.image.get_height() > 2 * small[1]
    assert text.image.get_width() > 2 * small[0]
    assert text.is_touching((0, small[1]))


def test_setting_an_unknown_font_warns_and_keeps_the_default_letters(caplog):
    text = play.new_text(words="Hello", font_size=40)
    default_size = text.image.get_size()

    with caplog.at_level(logging.WARNING, logger="play"):
        text.font = "__no_such_font__"
    text.update()

    assert text.font == "__no_such_font__"
    assert any("__no_such_font__" in r.getMessage() for r in caplog.records)
    assert text.image.get_size() == default_size
