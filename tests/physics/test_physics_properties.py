"""Tests for physics property setters."""

import pytest



def test_physics_x_speed_setter():
    """Test setting x_speed after physics initialization."""
    import play

    box = play.new_box()
    box.start_physics(x_speed=0)

    result = []

    @play.when_program_starts
    def check():
        result.append(box.physics.x_speed)
        box.physics.x_speed = 100
        result.append(box.physics.x_speed)
        play.stop_program()

    play.start_program()

    assert result[0] == 0
    assert result[1] == 100


def test_physics_y_speed_setter():
    """Test setting y_speed after physics initialization."""
    import play

    box = play.new_box()
    box.start_physics(y_speed=0)

    result = []

    @play.when_program_starts
    def check():
        result.append(box.physics.y_speed)
        box.physics.y_speed = 50
        result.append(box.physics.y_speed)
        play.stop_program()

    play.start_program()

    assert result[0] == 0
    assert result[1] == 50


def test_physics_can_move_getter():
    """Test getting can_move property."""
    import play

    box = play.new_box()
    box.start_physics(can_move=True)

    result = []

    @play.when_program_starts
    def check():
        result.append(box.physics.can_move)
        play.stop_program()

    play.start_program()

    assert result[0] is True


def test_physics_stable_getter():
    """Test getting stable property."""
    import play

    box = play.new_box()
    box.start_physics(stable=True)

    result = []

    @play.when_program_starts
    def check():
        result.append(box.physics.stable)
        play.stop_program()

    play.start_program()

    assert result[0] is True


def test_physics_obeys_gravity_getter():
    """Test getting obeys_gravity property."""
    import play

    box = play.new_box()
    box.start_physics(obeys_gravity=False)

    result = []

    @play.when_program_starts
    def check():
        result.append(box.physics.obeys_gravity)
        play.stop_program()

    play.start_program()

    assert result[0] is False


def test_physics_obeys_gravity_setter():
    """Test setting obeys_gravity property."""
    import play

    box = play.new_box()
    box.start_physics(obeys_gravity=False)

    result = []

    @play.when_program_starts
    def check():
        result.append(box.physics.obeys_gravity)
        box.physics.obeys_gravity = True
        result.append(box.physics.obeys_gravity)
        play.stop_program()

    play.start_program()

    assert result[0] is False
    assert result[1] is True


def test_physics_mass_getter():
    """Test getting mass property."""
    import play

    box = play.new_box()
    box.start_physics(mass=5)

    result = []

    @play.when_program_starts
    def check():
        result.append(box.physics.mass)
        play.stop_program()

    play.start_program()

    assert result[0] == 5


def test_physics_bounciness_getter():
    """Test getting bounciness property."""
    import play

    box = play.new_box()
    box.start_physics(bounciness=0.5)

    result = []

    @play.when_program_starts
    def check():
        result.append(box.physics.bounciness)
        play.stop_program()

    play.start_program()

    assert result[0] == 0.5


def test_physics_pause_unpause():
    """Test pausing and unpausing physics."""
    import play

    box = play.new_box()
    box.start_physics(x_speed=100)

    positions = []

    frame_count = [0]

    @play.repeat_forever
    def track():
        frame_count[0] += 1

        if frame_count[0] == 5:
            positions.append(box.x)
            box.physics.pause()

        if frame_count[0] == 15:
            positions.append(box.x)  # Should be same as frame 5

        if frame_count[0] == 16:
            box.physics.unpause()

        if frame_count[0] == 25:
            positions.append(box.x)  # Should be different
            play.stop_program()

    play.start_program()

    # Position should not change while paused
    assert positions[0] == positions[1]
    # Position should change after unpause
    assert positions[2] != positions[1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
