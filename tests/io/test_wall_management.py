"""Taking the screen's walls away and putting them back."""

import pytest

from play.callback.collision_callbacks import WallSide
from play.globals import globals_list
from play.io.screen import create_walls, remove_wall, remove_walls
from play.physics import physics_space


def test_remove_walls_takes_all_four_out_of_the_physics():
    walls = list(globals_list.walls)

    remove_walls()

    assert len(walls) == 4
    assert globals_list.walls == []
    assert not set(walls) & set(physics_space.shapes)


@pytest.mark.parametrize(
    "index, side",
    [
        (0, WallSide.TOP),
        (1, WallSide.BOTTOM),
        (2, WallSide.LEFT),
        (3, WallSide.RIGHT),
    ],
)
def test_remove_wall_takes_out_the_side_its_index_names(index, side):
    remove_wall(index)

    left = {wall.wall_side for wall in globals_list.walls}
    assert left == set(WallSide) - {side}
    assert {
        wall.wall_side for wall in physics_space.shapes if hasattr(wall, "wall_side")
    } == left


def test_remove_wall_with_an_index_beyond_the_four_walls_raises():
    with pytest.raises(IndexError):
        remove_wall(4)


def test_walls_can_be_put_back_after_removing_them():
    remove_walls()

    create_walls()

    assert {wall.wall_side for wall in globals_list.walls} == set(WallSide)
