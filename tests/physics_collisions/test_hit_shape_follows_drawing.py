"""The pymunk shape used for touching and clicks matches what is drawn (#240)."""

import pygame
import pymunk
import pytest

import play
from play.io.screen import screen
from play.objects.sprite import Sprite
from play.physics import physics_space

IMAGE = "tests/objects_attributes/yellow.jpg"


def _assert_hit_shape_matches_drawing(sprite):
    sprite.update()
    bb = sprite.physics._pymunk_shape.bb
    hit = (bb.right - bb.left, bb.top - bb.bottom)
    assert hit == pytest.approx(sprite.rect.size, abs=2)
    drawn_centre = (
        sprite.rect.centerx - screen.width / 2,
        screen.height / 2 - sprite.rect.centery,
    )
    hit_centre = ((bb.left + bb.right) / 2, (bb.bottom + bb.top) / 2)
    assert hit_centre == pytest.approx(drawn_centre, abs=2)


def _space_has_shape_at(point):
    return bool(physics_space.point_query(point, 0, pymunk.ShapeFilter()))


def test_text_given_words_later_is_hit_where_it_is_drawn():
    text = play.new_text(words="")
    text.words = "Hello world"
    _assert_hit_shape_matches_drawing(text)


def test_a_resized_text_is_hit_where_it_is_drawn():
    text = play.new_text(words="Hello")
    text.size = 300
    _assert_hit_shape_matches_drawing(text)


def test_text_with_a_new_font_size_is_hit_where_it_is_drawn():
    text = play.new_text(words="Hello")
    text.font_size = 120
    _assert_hit_shape_matches_drawing(text)


def test_a_resized_image_is_hit_where_it_is_drawn():
    image = play.new_image(image=IMAGE)
    image.size = 300
    _assert_hit_shape_matches_drawing(image)


def test_text_created_at_an_angle_is_hit_where_it_is_drawn():
    text = play.new_text(words="HELLO WORLD", angle=90)
    _assert_hit_shape_matches_drawing(text)


def test_a_static_box_turned_later_blocks_where_it_is_drawn():
    bar = play.new_box(width=200, height=20)
    bar.start_physics(can_move=False, obeys_gravity=False)
    bar.angle = 90
    assert _space_has_shape_at((0, 80))
    assert not _space_has_shape_at((80, 0))


def test_a_static_circle_given_a_bigger_radius_blocks_where_it_is_drawn():
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


class _Flag(Sprite):
    def __init__(self):
        self.rect = pygame.Rect(0, 0, 40, 20)
        super().__init__()
        self.update()

    def _render(self):
        flag = pygame.Surface((40, 20), pygame.SRCALPHA)
        flag.fill((255, 0, 0))
        self._finalize_image(flag)


def test_a_sprite_subclass_is_hit_where_it_is_drawn_after_resizing():
    flag = _Flag()
    for size in (300, 100):
        flag.size = size
        flag.update()
    _assert_hit_shape_matches_drawing(flag)


def test_a_slider_with_its_value_shown_is_hit_on_its_track():
    slider = play.new_slider(width=200, show_value=True, font_size=40)
    slider.update()
    bb = slider.physics._pymunk_shape.bb
    assert (bb.left, bb.right) == pytest.approx((-100, 100), abs=1)
    assert not slider.is_touching((-110, 0))
    assert slider.is_touching((95, 0))


@pytest.mark.parametrize(
    "built_width, width, passes_through",
    [(50, 0, True), (50, 20, False), (0, 0, True)],
    ids=["shrunk to nothing", "grown back", "built without area"],
)
def test_only_a_sprite_with_area_blocks_and_touches(built_width, width, passes_through):
    ball = play.new_circle(radius=10)
    ball.start_physics(x_speed=200, obeys_gravity=False)
    wall = play.new_box(x=100, width=built_width, height=200)
    wall.start_physics(can_move=False, obeys_gravity=False)
    wall.width = 0
    wall.width = width
    hits = []
    ball.when_touching(wall)(lambda: hits.append(1))
    frames = [0]

    @play.repeat_forever
    def stop_later():
        frames[0] += 1
        if frames[0] == 60:
            play.stop_program()

    play.start_program()

    assert (ball.x > 150) is passes_through
    assert bool(hits) is not passes_through


def test_text_with_a_new_font_is_hit_where_it_is_drawn():
    other_font = pygame.font.match_font("dejavusans,arial,liberationsans")
    if other_font is None:
        pytest.skip("no second font on this machine")
    text = play.new_text(words="Hello world")
    text.font = other_font
    _assert_hit_shape_matches_drawing(text)


def test_an_image_given_a_new_file_is_hit_where_it_is_drawn(tmp_path):
    bigger = tmp_path / "bigger.png"
    pygame.image.save(pygame.Surface((300, 120)), str(bigger))
    image = play.new_image(image=IMAGE)
    image.image_filename = str(bigger)
    _assert_hit_shape_matches_drawing(image)


def _run_frames(frames, each_frame=None):
    counted = [0]

    @play.repeat_forever
    def step():
        counted[0] += 1
        if each_frame:
            each_frame(counted[0])
        if counted[0] == frames:
            play.stop_program()

    play.start_program()
    return counted[0]


@pytest.mark.parametrize(
    "make",
    [
        lambda: play.new_box(size=0),
        lambda: play.new_box(size=-5),
        lambda: play.new_box(width=0),
        lambda: play.new_circle(radius=0),
    ],
    ids=["box at size 0", "box at size -5", "box of width 0", "circle of radius 0"],
)
def test_a_sprite_without_area_can_move_under_physics(make):
    sprite = make()
    sprite.start_physics()

    assert _run_frames(30) == 30


@pytest.mark.parametrize("built_without_area", [False, True])
def test_a_sprite_without_area_stays_on_screen_and_comes_back(built_without_area):
    box = play.new_box(
        y=-200, width=40, height=40, size=0 if built_without_area else 100
    )
    box.start_physics()
    floor = screen.bottom

    def shrink_then_grow(frame):
        if frame == 30:
            box.size = 0
        if frame == 120:
            box.size = 100

    assert _run_frames(180, shrink_then_grow) == 180
    assert box.y > floor


def test_a_turned_line_without_area_neither_touches_nor_blocks():
    line = play.new_box(y=-100, width=0, height=200, angle=45)
    line.start_physics(can_move=False)
    ball = play.new_circle(y=0, radius=10)
    ball.start_physics(y_speed=-300, obeys_gravity=False)
    touching = []
    ball.when_touching(line)(lambda: touching.append("when_touching"))

    def watch(_frame):
        if ball.is_touching(line):
            touching.append("is_touching")

    _run_frames(60, watch)

    assert touching == []
    assert ball.y < -150
