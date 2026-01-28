"""Tests for core game loop functionality."""

import pytest
import sys

sys.path.insert(0, ".")


def test_game_loop_runs():
    """Test that game loop runs and can be stopped."""
    import play

    result = []

    @play.when_program_starts
    def check():
        result.append("started")
        play.stop_program()

    play.start_program()

    assert result == ["started"]


def test_repeat_forever_runs_multiple_times():
    """Test that repeat_forever callback runs multiple frames."""
    import play

    frame_count = [0]
    result = []

    @play.repeat_forever
    def count_frames():
        frame_count[0] += 1
        if frame_count[0] >= 5:
            result.append(frame_count[0])
            play.stop_program()

    play.start_program()

    assert result[0] >= 5


def test_game_loop_updates_sprite_position():
    """Test that game loop updates sprite positions based on physics."""
    import play

    box = play.new_box(x=0)
    box.start_physics(x_speed=100, obeys_gravity=False)

    positions = []
    frame_count = [0]

    @play.repeat_forever
    def track():
        frame_count[0] += 1
        if frame_count[0] == 1:
            positions.append(box.x)
        if frame_count[0] == 10:
            positions.append(box.x)
            play.stop_program()

    play.start_program()

    # Position should have changed
    assert positions[1] > positions[0]


def test_game_loop_handles_backdrop_color():
    """Test that game loop handles backdrop color."""
    import play
    from play.globals import globals_list

    box = play.new_box()
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        play.set_backdrop("blue")
        result.append(globals_list.backdrop_type)
        play.stop_program()

    play.start_program()

    assert result[0] == "color"


def test_game_loop_physics_simulation():
    """Test that physics simulation runs in game loop."""
    import play
    from play.physics import set_gravity

    set_gravity(-500)

    box = play.new_box(y=100)
    box.start_physics(obeys_gravity=True)

    positions = []
    frame_count = [0]

    @play.repeat_forever
    def track():
        frame_count[0] += 1
        if frame_count[0] == 1:
            positions.append(box.y)
        if frame_count[0] == 20:
            positions.append(box.y)
            play.stop_program()

    play.start_program()

    # Y position should decrease due to gravity
    assert positions[1] < positions[0]


def test_game_loop_sprite_collision():
    """Test that collision detection works in game loop."""
    import play

    box1 = play.new_box(x=-100)
    box1.start_physics(x_speed=200, obeys_gravity=False)

    box2 = play.new_box(x=100)
    box2.start_physics(can_move=False)

    collision_happened = [False]
    frame_count = [0]

    @box1.when_touching(box2)
    def on_collision():
        collision_happened[0] = True

    @play.repeat_forever
    def check():
        frame_count[0] += 1
        if frame_count[0] > 60 or collision_happened[0]:
            play.stop_program()

    play.start_program()

    assert collision_happened[0] is True


def test_game_loop_keyboard_state_cleared():
    """Test that keyboard state is cleared each frame."""
    import play
    from play.core import keyboard_state

    result = []

    @play.when_program_starts
    def check():
        # Keyboard state should be empty at start
        result.append(len(keyboard_state.pressed))
        play.stop_program()

    play.start_program()

    assert result[0] == 0


def test_game_loop_mouse_state_cleared():
    """Test that mouse state is cleared each frame."""
    import play
    from play.core import mouse_state

    result = []

    @play.when_program_starts
    def check():
        # Mouse state should be cleared
        result.append(mouse_state.click_happened)
        result.append(mouse_state.click_release_happened)
        play.stop_program()

    play.start_program()

    assert result[0] is False
    assert result[1] is False


def test_frame_rate_setting():
    """Test that frame rate can be accessed."""
    import play
    from play.globals import globals_list

    result = []

    @play.when_program_starts
    def check():
        result.append(globals_list.FRAME_RATE)
        play.stop_program()

    play.start_program()

    assert result[0] == 60  # default frame rate


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
