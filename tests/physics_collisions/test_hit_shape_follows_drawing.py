"""The pymunk shape used for touching and clicks matches what is drawn (#240)."""

import pymunk
import pytest

import play
from play.physics import physics_space

IMAGE = "tests/objects_attributes/yellow.jpg"


def _assert_hit_shape_matches_drawing(sprite):
    sprite.update()
    bb = sprite.physics._pymunk_shape.bb
    hit = (bb.right - bb.left, bb.top - bb.bottom)
    assert hit == pytest.approx(sprite.rect.size, abs=2)


def _space_has_shape_at(point):
    return bool(physics_space.point_query(point, 0, pymunk.ShapeFilter()))


def test_text_given_words_later():
    text = play.new_text(words="")
    text.words = "Hello world"
    _assert_hit_shape_matches_drawing(text)


def test_text_resized():
    text = play.new_text(words="Hello")
    text.size = 300
    _assert_hit_shape_matches_drawing(text)


def test_text_with_a_new_font_size():
    text = play.new_text(words="Hello")
    text.font_size = 120
    _assert_hit_shape_matches_drawing(text)


def test_image_resized():
    image = play.new_image(image=IMAGE)
    image.size = 300
    _assert_hit_shape_matches_drawing(image)


def test_text_created_at_an_angle():
    text = play.new_text(words="HELLO WORLD", angle=90)
    _assert_hit_shape_matches_drawing(text)


def test_a_static_box_turned_later():
    bar = play.new_box(width=200, height=20)
    bar.start_physics(can_move=False, obeys_gravity=False)
    bar.angle = 90
    assert _space_has_shape_at((0, 80))
    assert not _space_has_shape_at((80, 0))


def test_a_static_circle_given_a_bigger_radius():
    circle = play.new_circle(radius=20)
    circle.start_physics(can_move=False, obeys_gravity=False)
    circle.radius = 100
    assert _space_has_shape_at((0, 90))
    _assert_hit_shape_matches_drawing(circle)


@pytest.mark.parametrize("make", [play.new_box, play.new_circle, play.new_text])
def test_a_sprite_at_size_zero_touches_nothing(make):
    sprite = make()
    other = play.new_box(width=300, height=300)
    sprite.size = 0
    assert not sprite.is_touching((0, 0))
    assert not sprite.is_touching(other)


@pytest.mark.parametrize(
    "make, attribute",
    [(play.new_circle, "radius"), (play.new_box, "width"), (play.new_box, "height")],
)
def test_a_negative_dimension_draws_and_touches_nothing(make, attribute):
    sprite = make()
    setattr(sprite, attribute, -3)
    sprite.update()
    assert not sprite.is_touching((0, 0))


WIDGETS = {
    "box": play.new_box,
    "button": lambda: play.new_button("Go"),
    "checkbox": play.new_checkbox,
    "progress bar": play.new_progress_bar,
    "text input": play.new_text_input,
    "dropdown": lambda: play.new_dropdown(["a", "b"]),
}


@pytest.mark.parametrize("attribute", ["width", "height"])
@pytest.mark.parametrize("widget", WIDGETS)
def test_a_negative_size_draws_a_widget_as_nothing(widget, attribute):
    sprite = WIDGETS[widget]()
    setattr(sprite, attribute, -5)
    sprite._should_recompute = True
    sprite.update()
    assert 0 in sprite.image.get_size()


def _shown_tooltip():
    tooltip = play.new_tooltip("hello", target=play.new_button("Go"))
    tooltip.show()
    return tooltip


SIZED_WIDGETS = {
    **WIDGETS,
    "slider": play.new_slider,
    "radio button": lambda: play.new_radio_button("pick me"),
    "tooltip": _shown_tooltip,
}


@pytest.mark.parametrize("sizes", [[200], [300, 100]], ids=["grown", "grown and back"])
@pytest.mark.parametrize("widget", SIZED_WIDGETS)
def test_a_resized_widget_is_hit_where_it_is_drawn(widget, sizes):
    sprite = SIZED_WIDGETS[widget]()
    for size in sizes:
        sprite.size = size
        sprite._should_recompute = True
        sprite.update()
    _assert_hit_shape_matches_drawing(sprite)
