"""Tests for RadioButton and RadioGroup widgets."""

import pygame
import pytest
import play
from play.io.mouse import mouse
from play.physics import physics_space
from play.utils import color_name_to_rgb
from tests.conftest import click_at, count_color


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def _image(sprite):
    return pygame.image.tobytes(sprite.image, "RGBA")


def _two_radios(selected="a"):
    g = play.new_radio_group()
    r1 = play.new_radio_button(
        "A", value="a", group=g, x=-50, y=0, selected=selected == "a"
    )
    r2 = play.new_radio_button(
        "B", value="b", group=g, x=50, y=0, selected=selected == "b"
    )
    return g, r1, r2


def test_radio_group_creation():
    g = play.new_radio_group()
    assert g.selected_value is None


@pytest.mark.parametrize("selected", ["a", "b"])
def test_a_group_reports_the_radio_created_selected(selected):
    g, _r1, _r2 = _two_radios(selected)
    assert g.selected_value == selected


def test_selecting_a_radio_in_code_deselects_the_rest_of_its_group():
    g, r1, r2 = _two_radios("a")
    received = []
    g.when_changed(received.append)
    r2.selected = True
    assert (r1.selected, r2.selected) == (False, True)
    assert g.selected_value == "b"
    assert received == ["b"]


def test_radio_group_selected_value_setter_fires_when_changed():
    # Regression: setting selected_value should fire when_changed, like the
    # TextInput.value and Slider.value setters do.
    g, r1, r2 = _two_radios("a")
    received = []
    g.when_changed(received.append)
    g.selected_value = "b"
    assert received == ["b"]
    assert r2.selected is True
    assert r1.selected is False


def test_radio_group_selected_value_setter_no_match_clears_without_firing():
    g, r1, r2 = _two_radios("a")
    received = []
    g.when_changed(received.append)
    g.selected_value = "does-not-exist"
    assert g.selected_value is None
    assert (r1.selected, r2.selected) == (False, False)
    assert received == []


def test_deselecting_a_grouped_radio_in_code_leaves_nothing_selected():
    g, r1, _r2 = _two_radios("a")
    received = []
    g.when_changed(received.append)
    r1.selected = False
    assert r1.selected is False
    assert g.selected_value is None
    assert received == []


def test_radio_group_when_changed_fires_on_click():
    # The real interaction path: clicking a radio must fire the group callback.
    g = play.new_radio_group()
    r1 = play.new_radio_button("A", value="a", group=g, x=-120, y=0)
    r2 = play.new_radio_button("B", value="b", group=g, x=120, y=0)
    for r in (r1, r2):
        r.update()
    received = []
    g.when_changed(received.append)
    click_at(120, 0, r1, r2)
    assert received == ["b"]
    assert g.selected_value == "b"


def test_radio_group_when_changed_rejects_async():
    g = play.new_radio_group()
    with pytest.raises(TypeError):

        @g.when_changed
        async def bad(v):
            pass


# ── RadioButton ────────────────────────────────────────────────────────────────


def test_radio_button_creation():
    r = play.new_radio_button("Option A", value="a")
    assert r.label == "Option A"
    assert r.value == "a"
    assert r.selected is False
    assert play.new_radio_button(selected=True).selected is True


def test_radio_button_label_setter():
    r = play.new_radio_button("old")
    before = _image(r)
    r.label = "new"
    assert r.label == "new"
    r.update()
    assert _image(r) != before


def test_a_disabled_radio_is_dimmed_and_ignores_clicks():
    g = play.new_radio_group()
    r = play.new_radio_button("X", value="x", group=g, x=0, y=0)
    enabled = _image(r)
    r.disabled = True
    assert r.disabled is True
    r.update()
    assert _image(r) != enabled
    click_at(0, 0, r)
    assert r.selected is False
    assert g.selected_value is None


def test_radio_button_click_selects():
    g = play.new_radio_group()
    r = play.new_radio_button("X", value="x", group=g, x=0, y=0, size_px=22)
    click_at(0, 0, r)
    assert r.selected is True


def test_a_radio_without_a_group_selects_itself_when_clicked():
    r = play.new_radio_button("X", value="x", x=0, y=0)
    click_at(0, 0, r)
    assert r.selected is True


def test_clicking_a_radios_label_selects_it():
    r = play.new_radio_button("A long label", value="x", x=0, y=0, size_px=22)
    r.update()
    click_at(r.image.get_width() / 2 - 5, 0, r)
    assert r.selected is True


def test_stacked_radios_select_independently():
    # Regression: a vertical stack of radios must each be clickable — a degenerate
    # hit-shape made every click land on the last radio.
    g = play.new_radio_group()
    top = play.new_radio_button("Top", value="top", group=g, x=-250, y=185)
    mid = play.new_radio_button("Mid", value="mid", group=g, x=-250, y=155)
    bot = play.new_radio_button("Bot", value="bot", group=g, x=-250, y=125)
    for r in (top, mid, bot):
        r.update()

    def click(y):
        click_at(-250, y, top, mid, bot)

    click(155)
    assert g.selected_value == "mid"
    click(185)
    assert g.selected_value == "top"
    click(125)
    assert g.selected_value == "bot"


def test_a_radio_without_a_label_is_a_circle_of_size_px():
    assert play.new_radio_button(size_px=30).image.get_size() == (30, 30)


@pytest.mark.parametrize("size, expected", [(100, (22, 22)), (200, (44, 44))])
def test_a_radios_drawing_scales_with_its_size(size, expected):
    r = play.new_radio_button(size_px=22)
    r.size = size
    r.update()
    assert r.image.get_size() == expected


def test_radio_button_label_change_does_not_leak_bodies():
    # Regression: the label setter must _remove() before _make_pymunk().
    r = play.new_radio_button("A", value="a", x=0, y=0, size_px=22)
    before = len(physics_space.bodies)
    for i in range(5):
        r.label = f"label {i}"
    assert len(physics_space.bodies) == before


def test_disabled_radio_ignores_hover():
    # Regression: a disabled radio must not show hover feedback.
    r = play.new_radio_button("A", value="a", x=0, y=0, size_px=22, disabled=True)
    mouse.x, mouse.y = 500, 500  # away
    r.update()
    away = _image(r)
    mouse.x, mouse.y = 0, 0  # over the radio
    r.update()
    assert _image(r) == away


def test_radio_button_hover_border_reacts():
    r = play.new_radio_button(
        "A", value="a", x=0, y=0, size_px=22, hover_border_color="red"
    )
    mouse.x, mouse.y = 500, 500
    r.update()
    assert count_color(r.image, (255, 0, 0)) == 0
    mouse.x, mouse.y = 0, 0
    r.update()
    assert count_color(r.image, (255, 0, 0)) > 0
    mouse.x, mouse.y = 500, 500
    r.update()
    assert count_color(r.image, (255, 0, 0)) == 0


def test_a_longer_label_is_clickable_after_the_label_changes():
    r = play.new_radio_button("A", value="a", x=0, y=0, size_px=22)
    r.update()
    narrow = r.image.get_width()
    r.label = "A considerably longer option label"
    r.update()
    click_at(narrow, 0, r)
    assert r.selected is True


def test_radio_button_selected_dot_only_when_selected():
    dot_rgb = color_name_to_rgb("royalblue")
    off = play.new_radio_button("A", selected_color="royalblue", selected=False)
    on = play.new_radio_button("A", selected_color="royalblue", selected=True)
    assert count_color(off.image, dot_rgb) == 0
    assert count_color(on.image, dot_rgb) > 0


def test_a_removed_radio_leaves_its_group():
    g, r1, r2 = _two_radios("a")
    r1.remove()
    assert g.selected_value is None
    g.selected_value = "a"
    assert g.selected_value is None
    assert r2.selected is False


def test_removing_a_radio_twice_is_harmless():
    g, r1, r2 = _two_radios("b")
    r1.remove()
    r1.remove()
    assert g.selected_value == "b"


def test_a_cloned_radio_joins_the_same_group():
    g, r1, _r2 = _two_radios("a")
    c = r1.clone()
    assert c.label == "A"
    assert c.value == "a"
    c.selected = True
    assert r1.selected is False
    assert g.selected_value == "a"


def test_a_cloned_radio_looks_like_the_original():
    r = play.new_radio_button(
        "X", value="x", color="yellow", selected_color="green", label_color="red"
    )
    assert _image(r.clone()) == _image(r)


def test_clone_selected_radio_keeps_single_selection():
    # Cloning a selected grouped radio must keep exactly one selection AND
    # must not mutate the original: the clone joins the group unselected.
    g = play.new_radio_group()
    r = play.new_radio_button("X", value="x", group=g, selected=True)
    c = r.clone()
    assert r.selected is True  # the original keeps its selection
    assert c.selected is False
    assert g.selected_value == "x"


def test_clone_ungrouped_radio_keeps_selected_state():
    r = play.new_radio_button("X", value="x", selected=True)
    c = r.clone()
    assert c.selected is True
    assert r.selected is True


def test_constructing_second_selected_radio_keeps_single_selection():
    g = play.new_radio_group()
    a = play.new_radio_button("A", value="a", group=g, selected=True)
    b = play.new_radio_button("B", value="b", group=g, selected=True)
    assert (a.selected, b.selected) == (False, True)
    assert g.selected_value == "b"
