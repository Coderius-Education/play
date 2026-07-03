"""Tests for RadioButton and RadioGroup widgets."""

import pytest
import play
from play.io.mouse import mouse
from play.core.mouse_loop import mouse_state
from play.utils import color_name_to_rgb
from tests.conftest import count_color


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


# ── RadioGroup ─────────────────────────────────────────────────────────────────


def test_radio_group_creation():
    g = play.new_radio_group()
    assert g.selected_value is None


def test_radio_group_selected_value_after_creation():
    g = play.new_radio_group()
    r = play.new_radio_button("A", value="a", group=g, selected=True)
    assert g.selected_value == "a"


def test_radio_group_deselects_others():
    g = play.new_radio_group()
    r1 = play.new_radio_button("A", value="a", group=g, x=-50, y=0, selected=True)
    r2 = play.new_radio_button("B", value="b", group=g, x=50, y=0)
    g._select(r2)
    assert r1._selected is False
    assert r2._selected is True


def test_radio_group_selected_value_returns_correct_value():
    g = play.new_radio_group()
    r1 = play.new_radio_button("A", value="a", group=g, x=-50, y=0)
    r2 = play.new_radio_button("B", value="b", group=g, x=50, y=0, selected=True)
    assert g.selected_value == "b"


def test_radio_group_selected_value_setter():
    g = play.new_radio_group()
    r1 = play.new_radio_button("A", value="a", group=g, x=-50, y=0, selected=True)
    r2 = play.new_radio_button("B", value="b", group=g, x=50, y=0)
    g.selected_value = "b"
    assert r1._selected is False
    assert r2._selected is True


def test_radio_group_when_changed_fires():
    g = play.new_radio_group()
    r1 = play.new_radio_button("A", value="a", group=g, x=-50, y=0)
    r2 = play.new_radio_button("B", value="b", group=g, x=50, y=0)
    received = []
    g.when_changed(received.append)
    g._select(r2)
    assert received == ["b"]


def test_radio_group_when_changed_fires_on_click():
    # The real interaction path: clicking a radio must fire the group callback.
    g = play.new_radio_group()
    r1 = play.new_radio_button("A", value="a", group=g, x=-120, y=0)
    r2 = play.new_radio_button("B", value="b", group=g, x=120, y=0)
    for r in (r1, r2):
        r.update()
    received = []
    g.when_changed(received.append)
    mouse.x, mouse.y = 120, 0
    mouse_state.click_happened = True
    for r in (r1, r2):
        r.update()
    mouse_state.click_happened = False
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


def test_radio_button_selected_default():
    r = play.new_radio_button(selected=True)
    assert r.selected is True


def test_radio_button_label_setter():
    r = play.new_radio_button("old")
    r.label = "new"
    assert r.label == "new"
    assert r._should_recompute is True


def test_radio_button_disabled_setter():
    r = play.new_radio_button()
    r.disabled = True
    assert r.disabled is True


def test_radio_button_disabled_ignores_click():
    g = play.new_radio_group()
    r = play.new_radio_button(
        "X", value="x", group=g, x=0, y=0, size_px=22, disabled=True
    )
    mouse.x = 0
    mouse.y = 0
    mouse_state.click_happened = True
    r.update()
    mouse_state.click_happened = False
    assert r._selected is False


def test_radio_button_click_selects():
    g = play.new_radio_group()
    r = play.new_radio_button("X", value="x", group=g, x=0, y=0, size_px=22)
    mouse.x = 0
    mouse.y = 0
    mouse_state.click_happened = True
    r.update()
    mouse_state.click_happened = False
    assert r._selected is True


def test_radio_button_hit_shape_matches_size():
    # Regression: the pymunk hit-shape must span the widget, not be a 0x0 point.
    r = play.new_radio_button("Label", value="x", x=0, y=0, size_px=22)
    bb = r.physics._pymunk_shape.bb
    assert (bb.right - bb.left) > 0
    assert (bb.top - bb.bottom) > 0


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
        mouse.x, mouse.y = -250, y
        mouse_state.click_happened = True
        for r in (top, mid, bot):
            r.update()
        mouse_state.click_happened = False

    click(155)
    assert g.selected_value == "mid"
    click(185)
    assert g.selected_value == "top"
    click(125)
    assert g.selected_value == "bot"


def test_radio_button_alive():
    r = play.new_radio_button()
    assert r.alive()


def test_radio_button_image_rendered():
    r = play.new_radio_button()
    assert r.image is not None
    assert r.image.get_width() > 0 and r.image.get_height() > 0


def test_radio_button_selected_dot_only_when_selected():
    dot_rgb = color_name_to_rgb("royalblue")
    off = play.new_radio_button("A", selected_color="royalblue", selected=False)
    on = play.new_radio_button("A", selected_color="royalblue", selected=True)
    assert count_color(off.image, dot_rgb) == 0
    assert count_color(on.image, dot_rgb) > 0


def test_radio_button_unregisters_on_remove():
    g = play.new_radio_group()
    r = play.new_radio_button("X", value="x", group=g)
    r.remove()
    assert r not in g._buttons


def test_radio_button_clone():
    g = play.new_radio_group()
    r = play.new_radio_button("X", value="x", group=g, selected=True)
    c = r.clone()
    assert c.label == "X"
    assert c.value == "x"
    assert c._selected is True
