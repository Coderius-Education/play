"""Tests for Text object creation and properties."""

import pytest


def test_text_creation_default():
    """Test creating a text object with default values."""
    import play

    test_results = {}
    num_frames = [0]

    text = play.new_text()

    @play.repeat_forever
    def check_values():
        if num_frames[0] > 0:
            return
        num_frames[0] += 1

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

    @play.repeat_forever
    def check_values():
        if num_frames[0] > 0:
            return
        num_frames[0] += 1

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

    text = play.new_text(words="Initial")

    @play.repeat_forever
    def check_values():
        if num_frames[0] > 0:
            return
        num_frames[0] += 1

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

    text = play.new_text(color="blue")

    @play.repeat_forever
    def check_values():
        if num_frames[0] > 0:
            return
        num_frames[0] += 1

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

    text = play.new_text(font_size=20)

    @play.repeat_forever
    def check_values():
        if num_frames[0] > 0:
            return
        num_frames[0] += 1

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

    text = play.new_text(x=50, y=60)

    @play.repeat_forever
    def check_values():
        if num_frames[0] > 0:
            return
        num_frames[0] += 1

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

    text = play.new_text(angle=0)

    @play.repeat_forever
    def check_values():
        if num_frames[0] > 0:
            return
        num_frames[0] += 1

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

    text = play.new_text(size=100)

    @play.repeat_forever
    def check_values():
        if num_frames[0] > 0:
            return
        num_frames[0] += 1

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

    text1 = play.new_text(
        words="Clone Me",
        x=100,
        y=200,
        font_size=30,
        color="purple",
        angle=45,
        size=150,
    )

    @play.repeat_forever
    def check_values():
        if num_frames[0] > 0:
            return
        num_frames[0] += 1

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

    text = play.new_text(words="Visible")

    @play.repeat_forever
    def check_values():
        if num_frames[0] > 0:
            return
        num_frames[0] += 1

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

    text = play.new_text(transparency=100)

    @play.repeat_forever
    def check_values():
        if num_frames[0] > 0:
            return
        num_frames[0] += 1

        # Transparency is stored as 0-1, so 100 becomes 1.0
        test_results["initial"] = text.transparency

        text.transparency = 50
        test_results["updated"] = text.transparency

        play.stop_program()

    play.start_program()

    assert test_results["initial"] == 100
    assert test_results["updated"] == 50


def test_text_angle_visually_applied():
    """Verify rotation is actually applied to the rendered surface, not just stored."""
    import play

    results = {}
    frames = [0]
    text = play.new_text(words="Hello", angle=0)

    @play.repeat_forever
    def check():
        if frames[0] > 0:
            return
        frames[0] += 1
        results["size_0"] = text._image.get_size()
        text.angle = 45
        text._should_recompute = True
        text.update()
        results["size_45"] = text._image.get_size()
        play.stop_program()

    play.start_program()
    assert results["size_0"] != results["size_45"]


def test_text_font_setter():
    """Verify the font setter reloads the pygame font object."""
    import play

    results = {}
    frames = [0]
    text = play.new_text()

    @play.repeat_forever
    def check():
        if frames[0] > 0:
            return
        frames[0] += 1
        first_font = text._pygame_font
        text.font = "default"
        results["font_name"] = text.font
        results["font_reloaded"] = text._pygame_font is not first_font
        play.stop_program()

    play.start_program()
    assert results["font_name"] == "default"
    assert results["font_reloaded"]


def test_text_font_invalid_name_falls_back(caplog):
    """Verify unknown font names fall back to default and emit a warning."""
    import logging
    import play

    frames = [0]

    with caplog.at_level(logging.WARNING, logger="play"):
        text = play.new_text(words="test", font="__nonexistent_xyz__")

        @play.repeat_forever
        def check():
            if frames[0] > 0:
                return
            frames[0] += 1
            play.stop_program()

        play.start_program()

    assert any("not found" in r.message for r in caplog.records)
    assert text._image is not None


def _find_non_default_font():
    """Return the name of any available system font that differs from pygame's built-in default.

    pygame's built-in is 'freesansbold.ttf'; skipping it ensures the chosen font
    produces different glyph metrics.  Returns None if no system fonts are available.
    """
    import pygame

    for name in pygame.font.get_fonts():
        if name == "freesansbold":
            continue
        if pygame.font.match_font(name):
            return name
    return None


def test_text_font_system_name_resolved():
    """Verify system font names are resolved via match_font, not silently ignored."""
    import play

    results = {}
    frames = [0]

    system_font = _find_non_default_font()
    if system_font is None:
        pytest.skip("No non-default system font available")

    text_default = play.new_text(words="Hello", font="default", font_size=40)
    text_system = play.new_text(words="Hello", font=system_font, font_size=40)

    @play.repeat_forever
    def check():
        if frames[0] > 0:
            return
        frames[0] += 1
        results["default_w"] = text_default._image.get_width()
        results["system_w"] = text_system._image.get_width()
        play.stop_program()

    play.start_program()
    assert (
        results["default_w"] != results["system_w"]
    ), "System font should produce different image width than default font"


def test_text_font_file_path():
    """Verify that an absolute file path triggers the os.path.isfile branch in _load_font."""
    import pygame
    import play

    results = {}
    frames = [0]

    system_font = _find_non_default_font()
    if system_font is None:
        pytest.skip("No non-default system font file available")
    font_path = pygame.font.match_font(system_font)

    text = play.new_text(words="Hello", font=font_path, font_size=40)
    text_default = play.new_text(words="Hello", font="default", font_size=40)

    @play.repeat_forever
    def check():
        if frames[0] > 0:
            return
        frames[0] += 1
        results["font"] = text.font
        results["width"] = text._image.get_width()
        results["default_width"] = text_default._image.get_width()
        play.stop_program()

    play.start_program()
    assert results["font"] == font_path
    assert (
        results["width"] != results["default_width"]
    ), "Font loaded from file path should produce different glyph metrics than default"


def test_text_font_setter_changes_rendering():
    """Verify that changing the font property produces different rendered glyph metrics."""
    import play

    results = {}
    frames = [0]

    system_font = _find_non_default_font()
    if system_font is None:
        pytest.skip("No non-default system font available")

    text = play.new_text(words="Hello", font="default", font_size=40)

    @play.repeat_forever
    def check():
        if frames[0] > 0:
            return
        frames[0] += 1
        results["default_w"] = text._image.get_width()
        text.font = system_font
        text._should_recompute = True
        text.update()
        results["system_w"] = text._image.get_width()
        play.stop_program()

    play.start_program()
    assert (
        results["default_w"] != results["system_w"]
    ), "Changing font should produce different image width"
