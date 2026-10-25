import pytest
import play


def test_size_scales_a_circle_and_what_can_be_touched():
    circle = play.new_circle(radius=100, size=150)
    assert circle.image.get_size() == (300, 300)
    assert circle.is_touching((140, 0))

    circle.size = 50
    circle.update()

    assert circle.image.get_size() == (100, 100)
    assert not circle.is_touching((60, 0))


def test_a_scaled_circle_keeps_an_even_diameter():
    # The radius is rounded and doubled, so the centre stays on a whole pixel.
    # Rounding the diameter instead gave 5 here, with a half-pixel centre.
    small = play.new_circle(radius=5, size=50)
    small.update()
    assert small.image.get_size() == (4, 4)

    odd = play.new_circle(radius=21, size=50)
    odd.update()
    assert odd.image.get_size() == (20, 20)


def test_a_tiny_but_positive_circle_is_still_a_dot():
    # Only size <= 0 means "nothing": a radius that rounds to zero is floored
    # at one, so the circle stays a 2x2 dot rather than vanishing.
    tiny = play.new_circle(radius=20, size=1)
    tiny.update()
    assert tiny.image.get_size() == (2, 2)


def test_a_circle_at_size_zero_draws_nothing():
    circle = play.new_circle(radius=20, size=0)

    assert circle.image.get_size() == (0, 0)
    assert not circle.is_touching((0, 0))
