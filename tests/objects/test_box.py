import pytest
import play


def test_size_scales_a_box_and_what_can_be_touched():
    box = play.new_box(width=200, height=150, size=200)
    assert box.image.get_size() == (400, 300)
    assert box.is_touching((190, 0))

    box.size = 50
    box.update()

    assert box.image.get_size() == (100, 75)
    assert not box.is_touching((60, 0))


@pytest.mark.parametrize("width, height", [(-10, 20), (20, -10), (0, 20)])
def test_a_side_of_zero_or_less_draws_nothing_instead_of_crashing(width, height):
    box = play.new_box(width=width, height=height)

    assert 0 in box.image.get_size()
    assert not box.is_touching((0, 0))
