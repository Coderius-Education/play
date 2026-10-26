"""Tests for utility functions."""

import pytest


def test_color_name_to_rgb_valid():
    """Test color_name_to_rgb with valid color names."""
    from play.utils import color_name_to_rgb

    # Test basic colors
    red = color_name_to_rgb("red")
    assert red[0] == 255
    assert red[1] == 0
    assert red[2] == 0
    assert red[3] == 255  # default transparency

    blue = color_name_to_rgb("blue")
    assert blue[0] == 0
    assert blue[1] == 0
    assert blue[2] == 255


def test_color_name_to_rgb_with_transparency():
    """Test color_name_to_rgb with custom transparency."""
    from play.utils import color_name_to_rgb

    red = color_name_to_rgb("red", transparency=128)
    assert red[3] == 128


def test_color_name_to_rgb_variants():
    """Test color_name_to_rgb with different naming variants."""
    from play.utils import color_name_to_rgb

    # All these should work
    color1 = color_name_to_rgb("lightblue")
    color2 = color_name_to_rgb("light blue")
    color3 = color_name_to_rgb("light-blue")

    # All should produce the same result
    assert color1[:3] == color2[:3] == color3[:3]


def test_color_name_to_rgb_tuple_passthrough():
    """Test that tuples are passed through unchanged."""
    from play.utils import color_name_to_rgb

    color_tuple = (255, 128, 0)
    result = color_name_to_rgb(color_tuple)
    assert result == color_tuple


def test_color_name_to_rgb_invalid():
    """Test color_name_to_rgb with invalid color name."""
    from play.utils import color_name_to_rgb

    with pytest.raises(ValueError, match="You gave a color name we didn't understand"):
        color_name_to_rgb("not_a_real_color_12345")


def test_color_name_to_rgb_case_insensitive():
    """Test that color names are case insensitive."""
    from play.utils import color_name_to_rgb

    red1 = color_name_to_rgb("RED")
    red2 = color_name_to_rgb("red")
    red3 = color_name_to_rgb("Red")

    assert red1[:3] == red2[:3] == red3[:3]


def test_color_name_to_rgb_hex_six_digit():
    """Test color_name_to_rgb with 6-digit hex codes."""
    from play.utils import color_name_to_rgb

    red = color_name_to_rgb("#FF0000")
    assert red[0] == 255
    assert red[1] == 0
    assert red[2] == 0
    assert red[3] == 255  # default transparency

    green = color_name_to_rgb("#00FF00")
    assert green[0] == 0
    assert green[1] == 255
    assert green[2] == 0

    blue = color_name_to_rgb("#0000FF")
    assert blue[0] == 0
    assert blue[1] == 0
    assert blue[2] == 255


def test_color_name_to_rgb_hex_three_digit():
    """Test color_name_to_rgb with 3-digit shorthand hex codes."""
    from play.utils import color_name_to_rgb

    red = color_name_to_rgb("#F00")
    assert red[0] == 255
    assert red[1] == 0
    assert red[2] == 0

    white = color_name_to_rgb("#FFF")
    assert white[0] == 255
    assert white[1] == 255
    assert white[2] == 255

    black = color_name_to_rgb("#000")
    assert black[0] == 0
    assert black[1] == 0
    assert black[2] == 0


def test_color_name_to_rgb_hex_lowercase():
    """Test that hex codes are case insensitive."""
    from play.utils import color_name_to_rgb

    upper = color_name_to_rgb("#FF8800")
    lower = color_name_to_rgb("#ff8800")
    mixed = color_name_to_rgb("#Ff8800")

    assert upper[:3] == lower[:3] == mixed[:3]


def test_color_name_to_rgb_hex_with_transparency():
    """Test hex codes with custom transparency."""
    from play.utils import color_name_to_rgb

    red = color_name_to_rgb("#FF0000", transparency=128)
    assert red[0] == 255
    assert red[1] == 0
    assert red[2] == 0
    assert red[3] == 128


def test_color_name_to_rgb_hex_invalid():
    """Test that invalid hex codes raise ValueError."""
    from play.utils import color_name_to_rgb

    with pytest.raises(ValueError, match="color name we didn't understand"):
        color_name_to_rgb("#GGGGGG")

    with pytest.raises(ValueError, match="color name we didn't understand"):
        color_name_to_rgb("#12345")  # 5 digits — invalid length

    with pytest.raises(ValueError, match="color name we didn't understand"):
        color_name_to_rgb("#GGG")  # 3-digit shorthand with invalid hex chars

    with pytest.raises(ValueError, match="color name we didn't understand"):
        color_name_to_rgb("#")  # just the hash, no digits


def test_color_name_to_rgb_hex_whitespace():
    """Test that hex codes with surrounding whitespace are handled."""
    from play.utils import color_name_to_rgb

    red = color_name_to_rgb("  #FF0000  ")
    assert red[0] == 255
    assert red[1] == 0
    assert red[2] == 0


def test_scale_to_percent_rounds_each_side():
    """Scaling rounds, as play always has; scale_by truncates and would give
    (21, 15) and (42, 31) here."""
    import pygame
    from play.utils import scale_to_percent

    surface = pygame.Surface((64, 48))
    assert scale_to_percent(surface, 33).get_size() == (21, 16)
    assert scale_to_percent(surface, 66).get_size() == (42, 32)
    assert scale_to_percent(surface, 100).get_size() == (64, 48)


def test_scale_to_percent_of_zero_or_less_is_empty():
    import pygame
    from play.utils import scale_to_percent

    surface = pygame.Surface((64, 48))
    assert scale_to_percent(surface, 0).get_size() == (0, 0)
    assert scale_to_percent(surface, -10).get_size() == (0, 0)


def test_scale_to_percent_keeps_a_positive_size_at_least_one_pixel():
    """Only size <= 0 means "nothing". A tiny positive size still shows a dot,
    as it always has, and never a lopsided 1x0 surface (1% of 64x48 rounds to
    (1, 0) without the floor)."""
    import pygame
    from play.utils import scale_to_percent

    surface = pygame.Surface((64, 48))
    assert scale_to_percent(surface, 1).get_size() == (1, 1)
    assert scale_to_percent(surface, 0.4).get_size() == (1, 1)
    assert scale_to_percent(surface, 2).get_size() == (1, 1)


def test_scale_to_percent_multiplies_before_dividing():
    """25 * 218 / 100 is exactly 54.5 and rounds to even, 54. Computing the
    factor first gives 25 * 2.18 = 54.500000000000001, which rounds to 55.
    A brute force over nine million size/percent pairs found about one in
    ten thousand sitting on such a half, so the order has to match master."""
    import pygame
    from play.utils import scale_to_percent

    assert scale_to_percent(pygame.Surface((25, 25)), 218).get_size() == (54, 54)
    assert scale_to_percent(pygame.Surface((45, 45)), 70).get_size() == (32, 32)


def test_run_once_runs_the_function_only_the_first_time():
    from play.utils import run_once

    calls = []

    @run_once
    def start():
        calls.append(1)
        return "started"

    assert start() == "started"
    assert start() is None
    assert calls == [1]

    start.has_run = False
    assert start() == "started"
    assert calls == [1, 1]


def _text_width(font, text):
    """Width in pixels of *text* drawn in *font*."""
    return font.render(text, True, (0, 0, 0)).get_width()


def test_load_font_opens_the_font_file_it_is_given(monkeypatch):
    import os

    import pygame
    from play.utils import load_font

    path = os.path.join(
        os.path.dirname(pygame.__file__), pygame.font.get_default_font()
    )
    opened = []
    real_font = pygame.font.Font

    def font(name, size):
        opened.append((name, size))
        return real_font(name, size)

    monkeypatch.setattr(pygame.font, "Font", font)

    loaded = load_font(path, 30)

    assert opened == [(path, 30)]
    assert loaded.get_height() == real_font(path, 30).get_height()


@pytest.mark.parametrize("name", [None, "default", "missing.ttf", "empty.ttf"])
def test_load_font_falls_back_to_the_default_font(tmp_path, monkeypatch, name):
    import pygame
    from play.utils import load_font

    monkeypatch.chdir(tmp_path)
    (tmp_path / "empty.ttf").write_bytes(b"")

    font = load_font(name, 30)

    default = pygame.font.SysFont(None, 30)
    assert font.get_height() == default.get_height()
    assert _text_width(font, "Score: 10") == _text_width(default, "Score: 10")


def test_an_async_widget_callback_is_rejected_by_name():
    import functools
    from play.utils import reject_async_callback

    async def on_click():
        pass

    reject_async_callback(lambda: None, "when_clicked")
    with pytest.raises(TypeError, match="on_click is async. when_clicked callbacks"):
        reject_async_callback(on_click, "when_clicked")
    with pytest.raises(TypeError, match="is async. when_changed callbacks"):
        reject_async_callback(functools.partial(on_click), "when_changed")


def test_text_that_renders_to_nothing_keeps_the_line_height():
    import pygame
    from play.utils import render_text

    font = pygame.font.SysFont(None, 30)

    empty = render_text(font, "\u200b", True, (0, 0, 0))
    word = render_text(font, "Hi", True, (0, 0, 0))

    assert empty.get_size() == (0, font.get_height())
    assert word.get_width() > 0
