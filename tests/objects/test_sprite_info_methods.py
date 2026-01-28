"""Tests for sprite info() and physics_info() methods."""

import pytest
import sys
from io import StringIO

sys.path.insert(0, ".")


def test_info_method_runs():
    """Test that info() method runs without error."""
    import play

    box = play.new_box(color="blue", width=100, height=50)
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        # Capture stdout
        import sys
        from io import StringIO

        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured

        box.info()

        sys.stdout = old_stdout
        output = captured.getvalue()
        result.append(output)
        play.stop_program()

    play.start_program()

    assert "Box" in result[0]
    assert "blue" in result[0]


def test_info_method_circle():
    """Test info() method for circle."""
    import play

    circle = play.new_circle(color="red", radius=25)
    circle.start_physics()

    result = []

    @play.when_program_starts
    def check():
        import sys
        from io import StringIO

        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured

        circle.info()

        sys.stdout = old_stdout
        output = captured.getvalue()
        result.append(output)
        play.stop_program()

    play.start_program()

    assert "Circle" in result[0]
    assert "red" in result[0]
    assert "radius" in result[0]


def test_physics_info_method_runs():
    """Test that physics_info() method runs without error."""
    import play

    box = play.new_box()
    box.start_physics(can_move=True, stable=False)

    result = []

    @play.when_program_starts
    def check():
        import sys
        from io import StringIO

        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured

        box.physics_info()

        sys.stdout = old_stdout
        output = captured.getvalue()
        result.append(output)
        play.stop_program()

    play.start_program()

    assert "DYNAMIC" in result[0]
    assert "can_move=True" in result[0]


def test_physics_info_static():
    """Test physics_info() for STATIC body."""
    import play

    box = play.new_box()
    box.start_physics(can_move=False)

    result = []

    @play.when_program_starts
    def check():
        import sys
        from io import StringIO

        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured

        box.physics_info()

        sys.stdout = old_stdout
        output = captured.getvalue()
        result.append(output)
        play.stop_program()

    play.start_program()

    assert "STATIC" in result[0]
    assert "VAST" in result[0]


def test_physics_info_kinematic():
    """Test physics_info() for KINEMATIC body."""
    import play
    from play.physics import set_gravity

    set_gravity(-100)

    box = play.new_box()
    box.start_physics(can_move=True, stable=True, obeys_gravity=False)

    result = []

    @play.when_program_starts
    def check():
        import sys
        from io import StringIO

        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured

        box.physics_info()

        sys.stdout = old_stdout
        output = captured.getvalue()
        result.append(output)
        play.stop_program()

    play.start_program()

    assert "KINEMATIC" in result[0]
    assert "GESTUURD" in result[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
