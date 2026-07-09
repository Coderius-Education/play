"""Tests for the Dropdown widget."""

import pytest
import play
from play.io.mouse import mouse
from play.core.mouse_loop import mouse_state


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_dropdown_creation():
    dd = play.new_dropdown(options=["A", "B", "C"], selected_index=0)
    assert dd.selected_value == "A"
    assert dd.selected_index == 0


def test_dropdown_no_options():
    dd = play.new_dropdown(options=[])
    assert dd.selected_value is None
    assert dd.selected_index == -1


def test_dropdown_selected_value():
    dd = play.new_dropdown(options=["X", "Y", "Z"], selected_index=2)
    assert dd.selected_value == "Z"


def test_dropdown_selected_index_setter():
    dd = play.new_dropdown(options=["A", "B", "C"], selected_index=0)
    dd.selected_index = 2
    assert dd.selected_value == "C"


def test_dropdown_options_setter():
    dd = play.new_dropdown(options=["A", "B"])
    dd.options = ["X", "Y", "Z"]
    assert dd.options == ["X", "Y", "Z"]
    assert dd._should_recompute is True


def test_dropdown_options_setter_clamps_index():
    dd = play.new_dropdown(options=["A", "B", "C"], selected_index=2)
    dd.options = ["X"]
    assert dd.selected_index == 0


def test_dropdown_open_toggles_on_click():
    dd = play.new_dropdown(options=["A", "B"], x=0, y=0, width=160, height=40)
    mouse.x = 0
    mouse.y = 0
    mouse_state.click_happened = True
    dd.update()
    mouse_state.click_happened = False
    assert dd.is_open is True


def test_dropdown_disabled_ignores_click():
    dd = play.new_dropdown(
        options=["A", "B"], x=0, y=0, width=160, height=40, disabled=True
    )
    mouse.x = 0
    mouse.y = 0
    mouse_state.click_happened = True
    dd.update()
    mouse_state.click_happened = False
    assert dd.is_open is False


def test_dropdown_when_changed_fires():
    dd = play.new_dropdown(options=["A", "B", "C"])
    received = []

    @dd.when_changed
    def on_change(v, i):
        received.append((v, i))

    dd._select(1)
    assert received == [("B", 1)]


def test_dropdown_hovers_option_row_under_mouse():
    # With the menu open, mouse.y=-80 lands on the 2nd option row (index 1)
    # for a dropdown at y=0 with height=40 on the 800x600 test display.
    dd = play.new_dropdown(options=["A", "B", "C"], x=0, y=0, width=160, height=40)
    mouse.x, mouse.y = 0, 0
    mouse_state.click_happened = True
    dd.update()  # open
    mouse_state.click_happened = False
    mouse.x, mouse.y = 0, -80
    dd.update()  # tracks hovered option
    assert dd._hovered_option == 1


def test_dropdown_click_option_selects_and_closes():
    dd = play.new_dropdown(options=["A", "B", "C"], x=0, y=0, width=160, height=40)
    mouse.x, mouse.y = 0, 0
    mouse_state.click_happened = True
    dd.update()  # open
    mouse_state.click_happened = False
    assert dd.is_open is True

    # Hover the 2nd option row so _hovered_option is set before the click frame.
    mouse.x, mouse.y = 0, -80
    dd.update()
    assert dd._hovered_option == 1

    # Click selects the hovered option and closes the menu.
    mouse_state.click_happened = True
    dd.update()
    mouse_state.click_happened = False
    assert dd.selected_index == 1
    assert dd.selected_value == "B"
    assert dd.is_open is False


def test_dropdown_click_option_fires_when_changed():
    dd = play.new_dropdown(options=["A", "B", "C"], x=0, y=0, width=160, height=40)
    received = []
    dd.when_changed(lambda v, i: received.append((v, i)))
    mouse.x, mouse.y = 0, 0
    mouse_state.click_happened = True
    dd.update()  # open
    mouse_state.click_happened = False
    mouse.x, mouse.y = 0, -120  # 3rd option row (index 2)
    dd.update()
    assert dd._hovered_option == 2
    mouse_state.click_happened = True
    dd.update()
    mouse_state.click_happened = False
    assert received == [("C", 2)]


def test_dropdown_when_changed_rejects_async():
    dd = play.new_dropdown(options=["A"])
    with pytest.raises(TypeError):

        @dd.when_changed
        async def bad(v, i):
            pass


def test_dropdown_disabled_setter():
    dd = play.new_dropdown(options=["A"])
    dd.disabled = True
    assert dd.disabled is True


def test_dropdown_disabled_closes_when_disabled():
    dd = play.new_dropdown(options=["A", "B"], x=0, y=0)
    dd._dropdown_open = True
    dd.disabled = True
    assert dd._dropdown_open is False


def test_dropdown_alive():
    dd = play.new_dropdown(options=["A", "B"])
    assert dd.alive()


def test_dropdown_image_rendered():
    dd = play.new_dropdown(options=["A", "B"])
    assert dd.image is not None
    assert dd.image.get_width() > 0 and dd.image.get_height() > 0


def test_dropdown_click_uses_current_mouse_not_stale_hover():
    # Regression: the click must select the row under the mouse now, not the
    # cached _hovered_option from the previous frame.
    dd = play.new_dropdown(options=["A", "B", "C"], x=0, y=0, width=160, height=40)
    mouse.x, mouse.y = 0, 0
    mouse_state.click_happened = True
    dd.update()  # open
    mouse_state.click_happened = False
    # Stale hover points at row 0, but the mouse is really over row 2.
    dd._hovered_option = 0
    mouse.x, mouse.y = 0, -120
    mouse_state.click_happened = True
    dd.update()
    mouse_state.click_happened = False
    assert dd.selected_index == 2


def test_dropdown_anchor_rect_height_stays_closed_when_open():
    # Regression: the anchor/collision rect keeps the closed-button height so an
    # edge-anchored dropdown doesn't jump vertically when the menu opens.
    dd = play.new_dropdown(
        options=["A", "B", "C"], anchor="top-left", x=10, y=10, width=160, height=40
    )
    dd.update()
    assert dd.rect.height == 40
    dd._dropdown_open = True
    dd._should_recompute = True
    dd.update()
    assert dd.image.get_height() > 40  # the drawn image did expand
    assert dd.rect.height == 40  # but the anchor rect did not


def test_dropdown_open_image_taller_than_closed():
    # Opening must actually expand the drawn surface to show the option rows.
    dd = play.new_dropdown(options=["A", "B", "C"], x=0, y=0, width=160, height=40)
    dd.update()
    closed_h = dd.image.get_height()
    mouse.x, mouse.y = 0, 0
    mouse_state.click_happened = True
    dd.update()  # open
    mouse_state.click_happened = False
    assert dd.is_open is True
    assert dd.image.get_height() > closed_h


def test_dropdown_clone():
    dd = play.new_dropdown(options=["A", "B", "C"], selected_index=1)
    c = dd.clone()
    assert c.options == ["A", "B", "C"]
    assert c.selected_index == 1


def test_dropdown_when_changed_value_signature():
    dd = play.new_dropdown(options=["A", "B", "C"])
    values = []
    indices = []

    @dd.when_changed
    def on_change(v, i):
        values.append(v)
        indices.append(i)

    dd._select(2)
    assert values == ["C"]
    assert indices == [2]


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
    dd = play.new_dropdown(options=["a"], layer=20)
    dd._set_open(True)
    assert dd.is_open
    assert dd.layer > 20
    dd._set_open(False)
    assert not dd.is_open
    assert dd.layer == 20
