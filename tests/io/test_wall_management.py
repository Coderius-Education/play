import pytest
import play
from play.globals import globals_list
from play.io.screen import remove_walls, remove_wall, create_walls, screen
from play.physics import physics_space


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_remove_walls_clears_all():
    """remove_walls() should remove all 4 wall segments from the physics space."""
    assert len(globals_list.walls) == 4

    remove_walls()

    assert len(globals_list.walls) == 0


def test_remove_walls_removes_from_physics_space():
    """After remove_walls(), the segments should no longer be in the pymunk space."""
    walls_before = list(globals_list.walls)
    remove_walls()

    for wall in walls_before:
        assert wall not in physics_space.shapes


def test_remove_wall_by_index():
    """remove_wall(index) should remove one specific wall."""
    assert len(globals_list.walls) == 4

    # Wall 0 is TOP
    top_wall = globals_list.walls[0]
    remove_wall(0)

    assert len(globals_list.walls) == 3
    assert top_wall not in physics_space.shapes


def test_remove_wall_out_of_range():
    """remove_wall() with an invalid index should raise IndexError."""
    with pytest.raises(IndexError):
        remove_wall(99)


def test_create_walls_after_remove():
    """Walls can be recreated after being removed."""
    remove_walls()
    assert len(globals_list.walls) == 0

    create_walls()
    assert len(globals_list.walls) == 4
