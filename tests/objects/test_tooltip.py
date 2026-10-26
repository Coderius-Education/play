"""Tests for the Tooltip widget."""

import pytest
import play
from play.io.mouse import mouse
from play.io.screen import screen
from play.objects.sprite import point_touching_sprite
from play.physics import physics_space
from play.utils import load_font
from tests.conftest import image_bytes
from tests.objects.clone_checks import BUNDLED_FONT, appearance


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def _make(text="Hi", target_x=200):
    """A 100x100 target box away from the mouse, and a tooltip on it."""
    target = play.new_box(color="red", x=target_x, y=0, width=100, height=100)
    tip = play.new_tooltip(text, target=target)
    return target, tip


def test_tooltip_text_change_does_not_leak_bodies():
    # Regression: the text setter must _remove() before _make_pymunk(), otherwise
    # each update orphans a body+shape in the physics space.
    _target, tip = _make()
    tip.show()  # unpause so the body is in the space
    before = len(physics_space.bodies)
    for i in range(5):
        tip.text = f"update {i}"
    assert len(physics_space.bodies) == before


def test_tooltip_is_sensor_and_hidden_leaves_space():
    _target, tip = _make()
    # Hidden by default: its body should not be in the physics space.
    assert tip.is_hidden is True
    assert tip.physics._pymunk_body not in physics_space.bodies
    # And it is a sensor so it never blocks other sprites when shown.
    tip.show()
    assert tip.physics.sensor is True


def test_tooltip_text_and_target_stored():
    target, tip = _make()
    assert tip.text == "Hi"
    assert tip.target is target


def test_a_tooltip_shows_only_while_the_mouse_is_over_its_target():
    _target, tip = _make()
    assert tip.is_hidden is True
    mouse.x, mouse.y = 200, 0
    tip.update()
    assert tip.is_hidden is False
    mouse.x, mouse.y = 0, 0
    tip.update()
    assert tip.is_hidden is True


def test_the_bubble_hangs_above_right_of_the_mouse_by_its_offset():
    _target, tip = _make()
    mouse.x, mouse.y = 200, 0
    tip.update()
    assert (tip.x, tip.y) == (200 + 12, 0 - 12)
    assert tip.rect.left == screen.width / 2 + 200 + 12
    assert tip.rect.bottom == screen.height / 2 + 12


def test_the_bubble_follows_the_mouse_up_and_down():
    _target, tip = _make()
    mouse.x, mouse.y = 200, 0
    tip.update()
    mouse.y = 30
    tip.update()
    assert tip.y == 30 - 12
    assert tip.rect.bottom == screen.height / 2 - 30 + 12


def test_tooltip_no_target_stays_hidden():
    tip = play.new_tooltip("orphan")
    tip.update()
    assert tip.is_hidden is True


def test_tooltip_text_setter_redraws_the_bubble():
    _target, tip = _make()
    mouse.x, mouse.y = 200, 0
    tip.update()
    before = image_bytes(tip)
    tip.text = "Updated"
    assert tip.text == "Updated"
    tip.update()
    assert image_bytes(tip) != before


def test_a_tooltip_moved_to_another_target_follows_that_target():
    _target, tip = _make()
    other = play.new_box(color="blue", x=-200, y=0)
    tip.target = other
    assert tip.target is other
    mouse.x, mouse.y = 200, 0
    tip.update()
    assert tip.is_hidden is True
    mouse.x, mouse.y = -200, 0
    tip.update()
    assert tip.is_hidden is False


def test_a_visible_bubble_is_its_text_plus_the_padding_on_each_side():
    _target, tip = _make()
    mouse.x, mouse.y = 200, 0
    tip.update()
    text_w, text_h = load_font(None, 15).render("Hi", True, (0, 0, 0)).get_size()
    assert tip.image.get_size() == (text_w + 12, text_h + 12)


def test_tooltip_multiline_taller_than_single_line():
    target = play.new_box(color="red", x=200, y=0, width=100, height=100)
    single = play.new_tooltip("A", target=target)
    multi = play.new_tooltip("A\nB\nC", target=target)
    mouse.x, mouse.y = 200, 0
    single.update()
    multi.update()
    assert multi.image.get_height() > single.image.get_height()


def test_a_visible_tooltip_is_hit_where_it_is_drawn():
    _target, tip = _make("Hello there")
    mouse.x, mouse.y = 200, 0
    tip.update()
    centre_x = tip.rect.centerx - screen.width / 2
    centre_y = screen.height / 2 - tip.rect.centery
    assert point_touching_sprite((centre_x, centre_y), tip)
    assert not point_touching_sprite((centre_x + 100, centre_y), tip)


def test_tooltip_stays_a_sensor_after_stop_physics():
    # The tooltip used to set its sensor flag by hand after construction, so
    # stop_physics() rebuilt a solid body under it.
    _target, tip = _make()
    tip.stop_physics()
    assert tip.physics.sensor is True


def test_a_cloned_tooltip_shows_the_same_bubble_in_the_same_place():
    # Regression: the inherited Sprite.clone() passed an unsupported image= kwarg.
    target = play.new_box(color="red", x=200, y=0, width=100, height=100)
    tip = play.new_tooltip(
        "Hi",
        target=target,
        offset_x=30,
        offset_y=20,
        color="yellow",
        text_color="red",
        border_color="green",
        font_size=24,
        font=BUNDLED_FONT,
        padding=9,
        border_radius=5,
        transparency=70,
        layer=90,
    )
    c = tip.clone()
    assert c.text == tip.text
    assert c.target is target
    mouse.x, mouse.y = 200, 0
    assert appearance(c) == appearance(tip)
