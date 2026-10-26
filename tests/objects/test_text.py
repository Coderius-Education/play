"""Tests for Text object creation and drawing."""

import logging

import pygame
import pytest

import play
from play.io.screen import convert_pos


def test_text_creation_default():
    text = play.new_text()

    assert text.words == ""
    assert (text.x, text.y) == (0, 0)
    assert text.font == "default"
    assert text.font_size == 50
    assert text.color == "black"
    assert text.angle == 0
    assert text.size == 100
    assert text.transparency == 100


def test_moving_a_text_moves_its_drawing():
    text = play.new_text("Hello", x=50, y=60)
    assert text.rect.center == convert_pos(50, 60)

    text.x = 100
    text.y = -200
    text.update()

    assert (text.x, text.y) == (100, -200)
    assert text.rect.center == convert_pos(100, -200)


def test_turning_a_text_turns_its_drawing():
    text = play.new_text("Hello", font_size=40)
    upright = text.image

    text.angle = 90
    text.update()

    assert text.angle == 90
    assert text.image.get_size() == (upright.get_height(), upright.get_width())


def test_size_scales_the_drawing_of_a_text():
    text = play.new_text("Hello", font_size=40)
    width, height = text.image.get_size()

    text.size = 200
    text.update()

    assert text.size == 200
    assert text.image.get_size() == (width * 2, height * 2)


def test_a_cloned_text_looks_exactly_like_the_original():
    text = play.new_text(
        words="Clone Me",
        x=100,
        y=200,
        font_size=30,
        color="purple",
        angle=45,
        size=150,
        transparency=60,
    )

    clone = text.clone()

    assert clone is not text
    assert clone.words == text.words
    assert clone.rect == text.rect
    assert pygame.image.tobytes(clone.image, "RGBA") == pygame.image.tobytes(
        text.image, "RGBA"
    )


def test_text_invalid_words_type():
    with pytest.raises(TypeError, match="must be a string or a number"):
        play.new_text(words=["score"])


def test_text_words_can_be_a_number_like_the_setter_allows():
    score = play.new_text(words=0)
    assert score.words == "0"
    assert play.new_text(words=1.5).words == "1.5"
    score.words = 10
    assert score.words == "10"


def test_text_font_invalid_name_falls_back(caplog):
    with caplog.at_level(logging.WARNING, logger="play"):
        text = play.new_text(words="test", font="__nonexistent_xyz__")
    default = play.new_text(words="test")

    assert any("not found" in r.message for r in caplog.records)
    assert text.font == "__nonexistent_xyz__"
    assert text.image.get_size() == default.image.get_size()


def _find_non_default_font():
    """Return the name of any available system font whose glyph metrics differ from
    pygame's built-in default (freesansbold.ttf) at size 40.
    Returns None if no such font is available.
    """
    pygame.font.init()
    probe = "AaBbCcDdEeFf"
    default_w = pygame.font.Font(pygame.font.get_default_font(), 40).size(probe)[0]

    for name in pygame.font.get_fonts():
        if name == "freesansbold":
            continue
        path = pygame.font.match_font(name)
        if not path:
            continue
        try:
            if pygame.font.Font(path, 40).size(probe)[0] != default_w:
                return name
        except Exception:
            continue
    return None


@pytest.fixture
def system_font():
    """A system font that draws differently from the default one."""
    name = _find_non_default_font()
    if name is None:
        pytest.skip("No non-default system font available")
    return name


def test_text_font_system_name_resolved(system_font):
    text_default = play.new_text(words="Hello", font="default", font_size=40)
    text_system = play.new_text(words="Hello", font=system_font, font_size=40)

    assert text_default.image.get_width() != text_system.image.get_width()


def test_text_font_file_path(system_font):
    font_path = pygame.font.match_font(system_font)

    text = play.new_text(words="Hello", font=font_path, font_size=40)
    by_name = play.new_text(words="Hello", font=system_font, font_size=40)

    assert text.font == font_path
    assert text.image.get_size() == by_name.image.get_size()


def test_changing_the_font_changes_the_drawing_and_changing_back_restores_it(
    system_font,
):
    text = play.new_text(words="Hello", font="default", font_size=40)
    default_size = text.image.get_size()

    text.font = system_font
    text.update()
    assert text.image.get_size() != default_size

    text.font = "default"
    text.update()
    assert text.image.get_size() == default_size
