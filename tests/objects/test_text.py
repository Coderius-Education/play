"""Tests for Text object creation and properties."""

import pytest
import sys

sys.path.insert(0, ".")


def test_text_creation_default():
    """Test creating a text object with default values."""
    import play

    text = play.new_text()

    assert text.words == ""
    assert text.x == 0
    assert text.y == 0
    assert text.font == "default"
    assert text.font_size == 50
    assert text.color == "black"
    assert text.angle == 0
    assert text.size == 100


def test_text_creation_with_parameters():
    """Test creating a text object with specific parameters."""
    import play

    text = play.new_text(
        words="Hello World",
        x=100,
        y=200,
        font_size=30,
        color="red",
        angle=45,
        transparency=80,
        size=150,
    )

    assert text.words == "Hello World"
    assert text.x == 100
    assert text.y == 200
    assert text.font_size == 30
    assert text.color == "red"
    assert text.angle == 45
    assert text.size == 150


def test_text_words_setter():
    """Test setting the words property."""
    import play

    text = play.new_text(words="Initial")
    assert text.words == "Initial"

    text.words = "Updated"
    assert text.words == "Updated"

    # Test conversion to string
    text.words = 123
    assert text.words == "123"


def test_text_color_setter():
    """Test setting the color property."""
    import play

    text = play.new_text(color="blue")
    assert text.color == "blue"

    text.color = "green"
    assert text.color == "green"


def test_text_font_size_setter():
    """Test setting the font_size property."""
    import play

    text = play.new_text(font_size=20)
    assert text.font_size == 20

    text.font_size = 40
    assert text.font_size == 40


def test_text_position_setters():
    """Test setting x and y positions."""
    import play

    text = play.new_text(x=50, y=60)
    assert text.x == 50
    assert text.y == 60

    text.x = 100
    text.y = 200
    assert text.x == 100
    assert text.y == 200


def test_text_angle_setter():
    """Test setting the angle property."""
    import play

    text = play.new_text(angle=0)
    assert text.angle == 0

    text.angle = 90
    assert text.angle == 90


def test_text_size_setter():
    """Test setting the size property."""
    import play

    text = play.new_text(size=100)
    assert text.size == 100

    text.size = 200
    assert text.size == 200


def test_text_clone():
    """Test cloning a text object."""
    import play

    text1 = play.new_text(
        words="Clone Me", x=100, y=200, font_size=30, color="purple", angle=45, size=150
    )

    text2 = text1.clone()

    assert text2.words == text1.words
    assert text2.x == text1.x
    assert text2.y == text1.y
    assert text2.font_size == text1.font_size
    assert text2.color == text1.color
    assert text2.angle == text1.angle
    assert text2.size == text1.size

    # Verify they are different objects
    assert text1 is not text2


def test_text_invalid_words_type():
    """Test that non-string words raise TypeError."""
    import play

    with pytest.raises(TypeError, match="words for a text object must be a string"):
        play.new_text(words=123)


def test_text_hide_show():
    """Test hiding and showing text."""
    import play

    text = play.new_text(words="Visible")
    assert text.is_hidden == False

    text.hide()
    assert text.is_hidden == True

    text.show()
    assert text.is_hidden == False


def test_text_transparency():
    """Test setting transparency."""
    import play

    text = play.new_text(transparency=100)
    # Transparency is stored as 0-1, so 100 becomes 1.0
    assert text.transparency == 1.0

    text.transparency = 0.5
    assert text.transparency == 0.5
