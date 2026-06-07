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
    dd = play.new_dropdown(options=["A", "B"], x=0, y=0, width=160, height=40, disabled=True)
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
