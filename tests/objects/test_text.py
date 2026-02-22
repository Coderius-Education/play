"""Tests for Text object creation and properties."""

import pytest


def test_text_creation_default():
    """Test creating a text object with default values."""
    import play

    test_results = {}
    num_frames = [0]

    @play.repeat_forever
    def check_values():
        if num_frames[0] > 0:
            return
        num_frames[0] += 1

        text = play.new_text()

        test_results["words"] = text.words
        test_results["x"] = text.x
        test_results["y"] = text.y
        test_results["font"] = text.font
        test_results["font_size"] = text.font_size
        test_results["color"] = text.color
        test_results["angle"] = text.angle
        test_results["size"] = text.size
        play.stop_program()

    play.start_program()

    assert test_results["words"] == ""
    assert test_results["x"] == 0
    assert test_results["y"] == 0
    assert test_results["font"] == "default"
    assert test_results["font_size"] == 50
    assert test_results["color"] == "black"
    assert test_results["angle"] == 0
    assert test_results["size"] == 100


def test_text_creation_with_parameters():
    """Test creating a text object with specific parameters."""
    import play

    test_results = {}
    num_frames = [0]

    @play.repeat_forever
    def check_values():
        if num_frames[0] > 0:
            return
        num_frames[0] += 1

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

        test_results["words"] = text.words
        test_results["x"] = text.x
        test_results["y"] = text.y
        test_results["font_size"] = text.font_size
        test_results["color"] = text.color
        test_results["angle"] = text.angle
        test_results["size"] = text.size
        play.stop_program()

    play.start_program()

    assert test_results["words"] == "Hello World"
    assert test_results["x"] == 100
    assert test_results["y"] == 200
    assert test_results["font_size"] == 30
    assert test_results["color"] == "red"
    assert test_results["angle"] == 45
    assert test_results["size"] == 150


def test_text_words_setter():
    """Test setting the words property."""
    import play

    test_results = {}
    num_frames = [0]

    @play.repeat_forever
    def check_values():
        if num_frames[0] > 0:
            return
        num_frames[0] += 1

        text = play.new_text(words="Initial")

        test_results["initial"] = text.words

        text.words = "Updated"
        test_results["updated"] = text.words

        # Test conversion to string
        text.words = 123
        test_results["numeric"] = text.words

        play.stop_program()

    play.start_program()

    assert test_results["initial"] == "Initial"
    assert test_results["updated"] == "Updated"
    assert test_results["numeric"] == "123"


def test_text_color_setter():
    """Test setting the color property."""
    import play

    test_results = {}
    num_frames = [0]

    @play.repeat_forever
    def check_values():
        if num_frames[0] > 0:
            return
        num_frames[0] += 1

        text = play.new_text(color="blue")

        test_results["initial"] = text.color

        text.color = "green"
        test_results["updated"] = text.color

        play.stop_program()

    play.start_program()

    assert test_results["initial"] == "blue"
    assert test_results["updated"] == "green"


def test_text_font_size_setter():
    """Test setting the font_size property."""
    import play

    test_results = {}
    num_frames = [0]

    @play.repeat_forever
    def check_values():
        if num_frames[0] > 0:
            return
        num_frames[0] += 1

        text = play.new_text(font_size=20)

        test_results["initial"] = text.font_size

        text.font_size = 40
        test_results["updated"] = text.font_size

        play.stop_program()

    play.start_program()

    assert test_results["initial"] == 20
    assert test_results["updated"] == 40


def test_text_position_setters():
    """Test setting x and y positions."""
    import play

    test_results = {}
    num_frames = [0]

    @play.repeat_forever
    def check_values():
        if num_frames[0] > 0:
            return
        num_frames[0] += 1

        text = play.new_text(x=50, y=60)

        test_results["initial_x"] = text.x
        test_results["initial_y"] = text.y

        text.x = 100
        text.y = 200
        test_results["updated_x"] = text.x
        test_results["updated_y"] = text.y

        play.stop_program()

    play.start_program()

    assert test_results["initial_x"] == 50
    assert test_results["initial_y"] == 60
    assert test_results["updated_x"] == 100
    assert test_results["updated_y"] == 200


def test_text_angle_setter():
    """Test setting the angle property."""
    import play

    test_results = {}
    num_frames = [0]

    @play.repeat_forever
    def check_values():
        if num_frames[0] > 0:
            return
        num_frames[0] += 1

        text = play.new_text(angle=0)

        test_results["initial"] = text.angle

        text.angle = 90
        test_results["updated"] = text.angle

        play.stop_program()

    play.start_program()

    assert test_results["initial"] == 0
    assert test_results["updated"] == 90


def test_text_size_setter():
    """Test setting the size property."""
    import play

    test_results = {}
    num_frames = [0]

    @play.repeat_forever
    def check_values():
        if num_frames[0] > 0:
            return
        num_frames[0] += 1

        text = play.new_text(size=100)

        test_results["initial"] = text.size

        text.size = 200
        test_results["updated"] = text.size

        play.stop_program()

    play.start_program()

    assert test_results["initial"] == 100
    assert test_results["updated"] == 200


def test_text_clone():
    """Test cloning a text object."""
    import play

    test_results = {}
    num_frames = [0]

    @play.repeat_forever
    def check_values():
        if num_frames[0] > 0:
            return
        num_frames[0] += 1

        text1 = play.new_text(
            words="Clone Me",
            x=100,
            y=200,
            font_size=30,
            color="purple",
            angle=45,
            size=150,
        )

        text2 = text1.clone()

        test_results["words_match"] = text2.words == text1.words
        test_results["x_match"] = text2.x == text1.x
        test_results["y_match"] = text2.y == text1.y
        test_results["font_size_match"] = text2.font_size == text1.font_size
        test_results["color_match"] = text2.color == text1.color
        test_results["angle_match"] = text2.angle == text1.angle
        test_results["size_match"] = text2.size == text1.size
        test_results["different_objects"] = text1 is not text2

        play.stop_program()

    play.start_program()

    assert test_results["words_match"]
    assert test_results["x_match"]
    assert test_results["y_match"]
    assert test_results["font_size_match"]
    assert test_results["color_match"]
    assert test_results["angle_match"]
    assert test_results["size_match"]
    assert test_results["different_objects"]


def test_text_invalid_words_type():
    """Test that non-string words raise TypeError."""
    import play

    with pytest.raises(TypeError, match="words for a text object must be a string"):
        play.new_text(words=123)


def test_text_hide_show():
    """Test hiding and showing text."""
    import play

    test_results = {}
    num_frames = [0]

    @play.repeat_forever
    def check_values():
        if num_frames[0] > 0:
            return
        num_frames[0] += 1

        text = play.new_text(words="Visible")

        test_results["initial"] = text.is_hidden

        text.hide()
        test_results["after_hide"] = text.is_hidden

        text.show()
        test_results["after_show"] = text.is_hidden

        play.stop_program()

    play.start_program()

    assert test_results["initial"] == False
    assert test_results["after_hide"] == True
    assert test_results["after_show"] == False


def test_text_transparency():
    """Test setting transparency."""
    import play

    test_results = {}
    num_frames = [0]

    @play.repeat_forever
    def check_values():
        if num_frames[0] > 0:
            return
        num_frames[0] += 1

        text = play.new_text(transparency=100)

        # Transparency is stored as 0-1, so 100 becomes 1.0
        test_results["initial"] = text.transparency

        text.transparency = 50
        test_results["updated"] = text.transparency

        play.stop_program()

    play.start_program()

    assert test_results["initial"] == 100
    assert test_results["updated"] == 50
