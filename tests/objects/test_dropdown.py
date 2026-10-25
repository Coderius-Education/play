"""Tests for the Dropdown widget."""

import pygame
import pytest
import play
from play.io.mouse import mouse
from play.utils import color_name_to_rgb
from tests.conftest import click_at


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def _toggle(dropdown):
    click_at(dropdown.x, dropdown.y, dropdown)


def _image(sprite):
    return pygame.image.tobytes(sprite.image, "RGBA")


@pytest.mark.parametrize("index, value", [(0, "A"), (2, "C")])
def test_dropdown_selected_value_matches_the_selected_index(index, value):
    dd = play.new_dropdown(options=["A", "B", "C"], selected_index=index)
    assert dd.selected_value == value
    assert dd.selected_index == index


def test_dropdown_no_options():
    dd = play.new_dropdown(options=[])
    assert dd.selected_value is None
    assert dd.selected_index == -1


def test_dropdown_selected_index_setter():
    dd = play.new_dropdown(options=["A", "B", "C"], selected_index=0)
    dd.selected_index = 2
    assert dd.selected_value == "C"


@pytest.mark.parametrize("index, expected", [(9, 2), (-5, -1)])
def test_an_out_of_range_selected_index_is_clamped(index, expected):
    dd = play.new_dropdown(options=["A", "B", "C"], selected_index=1)
    dd.selected_index = index
    assert dd.selected_index == expected


def test_dropdown_options_setter():
    dd = play.new_dropdown(options=["A", "B"])
    before = _image(dd)
    dd.options = ["X", "Y", "Z"]
    assert dd.options == ["X", "Y", "Z"]
    dd.update()
    assert _image(dd) != before


def test_dropdown_options_setter_clamps_index():
    dd = play.new_dropdown(options=["A", "B", "C"], selected_index=2)
    dd.options = ["X"]
    assert dd.selected_index == 0


def test_each_click_on_the_button_opens_or_closes_the_menu_without_choosing():
    dd = play.new_dropdown(
        options=["A", "B"], selected_index=1, x=0, y=0, width=160, height=40
    )
    click_at(0, 0, dd)
    assert dd.is_open is True
    click_at(0, 0, dd)
    assert dd.is_open is False
    assert dd.selected_value == "B"


def test_dropdown_disabled_ignores_click():
    dd = play.new_dropdown(
        options=["A", "B"], x=0, y=0, width=160, height=40, disabled=True
    )
    click_at(0, 0, dd)
    assert dd.is_open is False


def test_the_option_row_under_the_mouse_is_highlighted():
    red = color_name_to_rgb("red")
    dd = play.new_dropdown(
        options=["A", "B", "C"],
        x=0,
        y=0,
        width=160,
        height=40,
        option_hover_color="red",
    )
    click_at(0, 0, dd)
    mouse.x, mouse.y = 0, -80
    dd.update()
    assert dd.image.get_at((20, 100)) == red
    assert dd.image.get_at((20, 60)) != red
    assert dd.image.get_at((20, 140)) != red


@pytest.mark.parametrize("row, value", [(0, "A"), (1, "B"), (2, "C")])
def test_dropdown_click_option_selects_and_closes(row, value):
    dd = play.new_dropdown(
        options=["A", "B", "C"], selected_index=-1, x=0, y=0, width=160, height=40
    )
    click_at(0, 0, dd)
    assert dd.is_open is True

    click_at(0, -40 * (row + 1), dd)
    assert dd.selected_index == row
    assert dd.selected_value == value
    assert dd.is_open is False


@pytest.mark.xfail(
    strict=True, reason="the default font has no ▲/▼ glyphs, so both draw the same box"
)
def test_the_arrow_on_the_button_flips_when_the_menu_opens():
    dd = play.new_dropdown(options=["A", "B"], x=0, y=0, width=160, height=40)
    mouse.x, mouse.y = 300, 250
    dd.update()
    closed_button = pygame.image.tobytes(dd.image.subsurface((0, 0, 160, 40)), "RGBA")
    click_at(0, 0, dd)
    mouse.x, mouse.y = 300, 250
    dd.update()
    open_button = pygame.image.tobytes(dd.image.subsurface((0, 0, 160, 40)), "RGBA")
    assert open_button != closed_button


def test_dropdown_click_option_fires_when_changed():
    dd = play.new_dropdown(options=["A", "B", "C"], x=0, y=0, width=160, height=40)
    received = []
    dd.when_changed(lambda v, i: received.append((v, i)))
    click_at(0, 0, dd)
    click_at(0, -120, dd)
    assert received == [("C", 2)]


def test_a_click_beside_the_open_list_closes_it_without_choosing():
    dd = play.new_dropdown(options=["A", "B", "C"], x=0, y=0, width=160, height=40)
    click_at(0, 0, dd)
    click_at(120, -80, dd)
    assert dd.is_open is False
    assert dd.selected_value == "A"


def test_dropdown_when_changed_rejects_async():
    dd = play.new_dropdown(options=["A"])
    with pytest.raises(TypeError):

        @dd.when_changed
        async def bad(v, i):
            pass


def test_disabling_an_open_dropdown_closes_it():
    dd = play.new_dropdown(options=["A", "B"], x=0, y=0)
    click_at(0, 0, dd)
    dd.disabled = True
    assert dd.disabled is True
    assert dd.is_open is False


def test_a_disabled_dropdown_is_dimmed():
    enabled = play.new_dropdown(options=["A", "B"], x=0, y=100)
    disabled = play.new_dropdown(options=["A", "B"], x=0, y=-100, disabled=True)
    assert _image(enabled) != _image(disabled)


def test_a_closed_dropdown_is_one_row_of_its_width_and_height():
    dd = play.new_dropdown(options=["A", "B"], width=160, height=40)
    assert dd.image.get_size() == (160, 40)


def test_a_dropdown_with_nothing_selected_shows_its_placeholder():
    nothing = play.new_dropdown(options=["A", "B"], selected_index=-1, x=0, y=100)
    empty = play.new_dropdown(options=[], x=0, y=-100)
    assert _image(nothing) == _image(empty)


def test_dropdown_click_uses_current_mouse_not_stale_hover():
    # Regression: the click must select the row under the mouse now, not the last hovered one.
    dd = play.new_dropdown(options=["A", "B", "C"], x=0, y=0, width=160, height=40)
    click_at(0, 0, dd)
    mouse.x, mouse.y = 0, -40
    dd.update()
    click_at(0, -120, dd)
    assert dd.selected_index == 2


def test_dropdown_anchor_rect_height_stays_closed_when_open():
    # Regression: the anchor/collision rect keeps the closed-button height so an
    # edge-anchored dropdown doesn't jump vertically when the menu opens.
    dd = play.new_dropdown(
        options=["A", "B", "C"], anchor="top-left", x=10, y=10, width=160, height=40
    )
    dd.update()
    assert dd.rect.height == 40
    _toggle(dd)
    assert dd.is_open is True
    assert dd.image.get_height() > 40  # the drawn image did expand
    assert dd.rect.height == 40  # but the anchor rect did not


def test_dropdown_open_image_taller_than_closed():
    # Opening must actually expand the drawn surface to show the option rows.
    dd = play.new_dropdown(options=["A", "B", "C"], x=0, y=0, width=160, height=40)
    dd.update()
    closed_h = dd.image.get_height()
    click_at(0, 0, dd)  # open
    assert dd.is_open is True
    assert dd.image.get_height() > closed_h


def test_a_cloned_dropdown_looks_like_the_original():
    dd = play.new_dropdown(
        options=["A", "B", "C"],
        selected_index=1,
        color="yellow",
        text_color="red",
        border_color="green",
        placeholder="Pick",
    )
    c = dd.clone()
    assert c.options == ["A", "B", "C"]
    assert c.selected_index == 1
    assert _image(c) == _image(dd)


def test_a_dropdown_cloned_while_open_rests_at_the_original_layer():
    dd = play.new_dropdown(options=["A", "B"], x=0, y=0, layer=20)
    click_at(0, 0, dd)
    assert dd.clone().layer == 20


def test_dropdown_constructor_clamps_selected_index():
    # Regression: an out-of-range index silently rendered the placeholder.
    dd = play.new_dropdown(options=["a", "b"], selected_index=5)
    assert dd.selected_index == 1
    assert dd.selected_value == "b"


def test_dropdown_constructor_clamps_negative_selected_index():
    dd = play.new_dropdown(options=["a", "b"], selected_index=-7)
    assert dd.selected_index == -1
    assert dd.selected_value is None


def test_dropdown_open_hoists_layer():
    # Regression: the open option list drew at the closed layer, so covered
    # rows were invisible yet still took clicks.
    dd = play.new_dropdown(options=["a"], x=0, y=0, layer=20)
    click_at(0, 0, dd)
    assert dd.is_open
    assert dd.layer > 20
    click_at(0, 0, dd)
    assert not dd.is_open
    assert dd.layer == 20


def test_open_menu_click_does_not_fall_through():
    # Regression: clicking an option on the open menu also clicked whatever
    # widget sat underneath the menu.
    dd = play.new_dropdown(options=["A", "B"], x=0, y=0, width=160, height=40)
    cb = play.new_checkbox(label="under the menu", x=0, y=-40)

    # Click the closed button to open the menu.
    click_at(0, 0, dd, cb)
    assert dd.is_open is True

    # Click option row 0, which overlaps the checkbox underneath.
    click_at(0, -40, dd, cb)

    assert dd.selected_value == "A"
    assert cb.checked is False  # the menu swallowed the click


def test_closed_dropdown_does_not_claim_clicks():
    dd = play.new_dropdown(options=["A", "B"], x=0, y=0, width=160, height=40)
    cb = play.new_checkbox(label="beside", x=0, y=-40)
    click_at(0, -40, dd, cb)
    assert dd.is_open is False
    assert cb.checked is True  # normal click still reaches the checkbox


def test_an_unturned_dropdown_at_a_fractional_x_keeps_its_place():
    dropdown = play.new_dropdown(options=["a", "bb"], x=1.5, width=121)
    dropdown.update()

    assert dropdown.rect.x == int(play.screen.width / 2 + 1.5 - 121 / 2)


def _a_full_turn_in_small_steps():
    angle = 0.0
    for _ in range(3600):
        angle += 0.1
    return angle


@pytest.mark.parametrize(
    "angle", [360, _a_full_turn_in_small_steps()], ids=["360", "3600_steps_of_0.1"]
)
def test_a_dropdown_turned_a_full_turn_keeps_its_closed_height_when_open(angle):
    dropdown = play.new_dropdown(options=["a", "bb", "ccc"], height=40)
    dropdown.angle = angle
    _toggle(dropdown)
    assert dropdown.is_open is True

    assert dropdown.rect.height == 40


@pytest.mark.parametrize("angle", [0, 30, 90])
def test_an_anchored_turned_dropdown_sits_at_its_anchor(angle):
    dropdown = play.new_dropdown(
        options=["a", "bb", "ccc"], width=120, anchor="bottom-left", x=10, y=10
    )
    dropdown.angle = angle
    dropdown.update()
    dropdown.update()
    assert dropdown.rect.left == pytest.approx(10, abs=1)
    assert dropdown.rect.bottom == pytest.approx(play.screen.height - 10, abs=1)


@pytest.mark.parametrize("angle", [30, 90])
def test_an_anchored_turned_dropdown_stays_put_when_it_opens(angle):
    dropdown = play.new_dropdown(
        options=["a", "bb", "ccc"], width=120, anchor="bottom-left", x=10, y=10
    )
    dropdown.angle = angle
    dropdown.update()
    dropdown.update()
    places = [(dropdown.x, dropdown.y)]
    for opened in (True, False):
        _toggle(dropdown)
        assert dropdown.is_open is opened
        places.append((dropdown.x, dropdown.y))

    assert places[0] == places[1] == places[2]


def test_a_dropdown_turned_a_quarter_turn_folds_its_list_out_sideways():
    dropdown = play.new_dropdown(options=["a", "bb", "ccc"], height=40)
    dropdown.angle = 90
    dropdown.update()
    closed = dropdown.rect.center
    _toggle(dropdown)
    assert dropdown.is_open is True
    opened = dropdown.rect.center

    assert opened[1] == pytest.approx(closed[1], abs=1)
    assert opened[0] > closed[0] + 40


@pytest.mark.xfail(
    strict=True, reason="option clicks on a turned open dropdown use unrotated rows"
)
def test_clicking_an_option_of_a_turned_open_dropdown_selects_it():
    dropdown = play.new_dropdown(
        options=["a", "bb", "ccc"], selected_index=2, width=160, height=40
    )
    dropdown.angle = 90
    _toggle(dropdown)
    click_at(40, 0, dropdown)
    assert dropdown.selected_value == "a"
