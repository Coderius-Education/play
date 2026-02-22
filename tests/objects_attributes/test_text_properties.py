"""Tests for Text sprite properties."""

import pytest


def test_text_words_getter():
    """Test getting text words."""
    import play

    text = play.new_text(words="Hello")
    text.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(text.words)
        play.stop_program()

    play.start_program()

    assert result[0] == "Hello"


def test_text_words_setter():
    """Test setting text words."""
    import play

    text = play.new_text(words="Hello")
    text.start_physics()

    result = []

    @play.when_program_starts
    def check():
        text.words = "World"
        result.append(text.words)
        play.stop_program()

    play.start_program()

    assert result[0] == "World"


def test_text_color_getter():
    """Test getting text color."""
    import play

    text = play.new_text(words="Test", color="red")
    text.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(text.color)
        play.stop_program()

    play.start_program()

    assert result[0] == "red"


def test_text_color_setter():
    """Test setting text color."""
    import play

    text = play.new_text(words="Test", color="red")
    text.start_physics()

    result = []

    @play.when_program_starts
    def check():
        text.color = "blue"
        result.append(text.color)
        play.stop_program()

    play.start_program()

    assert result[0] == "blue"


def test_text_font_size_getter():
    """Test getting text font_size."""
    import play

    text = play.new_text(words="Test", font_size=30)
    text.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(text.font_size)
        play.stop_program()

    play.start_program()

    assert result[0] == 30


def test_text_font_size_setter():
    """Test setting text font_size."""
    import play

    text = play.new_text(words="Test", font_size=30)
    text.start_physics()

    result = []

    @play.when_program_starts
    def check():
        text.font_size = 50
        result.append(text.font_size)
        play.stop_program()

    play.start_program()

    assert result[0] == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
