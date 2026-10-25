"""is_touching_wall() and get_touching_walls()."""

import pytest

import play
from play.callback.collision_callbacks import WallSide


@pytest.mark.parametrize(
    "place, walls",
    [
        ({"x": 0, "y": 0}, []),
        ({"x": 380, "y": 0, "width": 50}, [WallSide.RIGHT]),
        ({"x": -380, "y": 0, "width": 50}, [WallSide.LEFT]),
        ({"x": 0, "y": 280, "height": 50}, [WallSide.TOP]),
        ({"x": 0, "y": -280, "height": 50}, [WallSide.BOTTOM]),
        (
            {"x": 380, "y": 280, "width": 50, "height": 50},
            [WallSide.TOP, WallSide.RIGHT],
        ),
    ],
    ids=["middle", "right", "left", "top", "bottom", "top-right corner"],
)
def test_a_sprite_reports_the_walls_it_overlaps(place, walls):
    box = play.new_box(**place)
    box.start_physics()
    result = []

    @play.when_program_starts
    def check():
        result.append((box.is_touching_wall(), box.get_touching_walls()))
        play.stop_program()

    play.start_program()

    assert result == [(bool(walls), walls)]


def test_a_hidden_sprite_touches_no_wall():
    box = play.new_box(x=380, width=50)
    box.start_physics()
    box.hide()

    assert not box.is_touching_wall()
    assert box.get_touching_walls() == []
