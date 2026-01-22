"""Tests for sprite visibility properties (is_hidden, is_shown)."""

import pytest
import sys

sys.path.insert(0, ".")


def test_is_hidden_default():
    """Test is_hidden is False by default."""
    import play

    box = play.new_box()
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(box.is_hidden)
        play.stop_program()

    play.start_program()

    assert result[0] is False


def test_is_hidden_after_hide():
    """Test is_hidden is True after hide()."""
    import play

    box = play.new_box()
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        box.hide()
        result.append(box.is_hidden)
        play.stop_program()

    play.start_program()

    assert result[0] is True


def test_is_hidden_setter():
    """Test is_hidden setter."""
    import play

    box = play.new_box()
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        box.is_hidden = True
        result.append(box.is_hidden)
        box.is_hidden = False
        result.append(box.is_hidden)
        play.stop_program()

    play.start_program()

    assert result[0] is True
    assert result[1] is False


def test_is_shown_default():
    """Test is_shown is True by default."""
    import play

    box = play.new_box()
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(box.is_shown)
        play.stop_program()

    play.start_program()

    assert result[0] is True


def test_is_shown_after_hide():
    """Test is_shown is False after hide()."""
    import play

    box = play.new_box()
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        box.hide()
        result.append(box.is_shown)
        play.stop_program()

    play.start_program()

    assert result[0] is False


def test_is_shown_setter():
    """Test is_shown setter."""
    import play

    box = play.new_box()
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        box.is_shown = False
        result.append(box.is_shown)
        result.append(box.is_hidden)
        box.is_shown = True
        result.append(box.is_shown)
        result.append(box.is_hidden)
        play.stop_program()

    play.start_program()

    assert result[0] is False
    assert result[1] is True
    assert result[2] is True
    assert result[3] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
