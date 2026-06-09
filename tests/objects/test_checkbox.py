"""Tests for the Checkbox widget."""

import pytest
import play
from play.io.mouse import mouse
from play.core.mouse_loop import mouse_state


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_checkbox_creation():
    cb = play.new_checkbox(label="Enable sound", checked=True)
    assert cb.checked is True
    assert cb.label == "Enable sound"


def test_checkbox_default_unchecked():
    cb = play.new_checkbox()
    assert cb.checked is False


def test_checkbox_toggles_on_click():
    cb = play.new_checkbox(x=0, y=0, size_px=24)
    mouse.x = 0
    mouse.y = 0
    mouse_state.click_happened = True
    cb.update()
    assert cb.checked is True
    mouse_state.click_happened = False


def test_checkbox_when_changed_fires():
    cb = play.new_checkbox(x=0, y=0, size_px=24)
    results = []
    cb.when_changed(results.append)
    mouse.x = 0
    mouse.y = 0
    mouse_state.click_happened = True
    cb.update()
    mouse_state.click_happened = False
    assert results == [True]


def test_checkbox_when_changed_rejects_async():
    cb = play.new_checkbox()
    with pytest.raises(TypeError):

        @cb.when_changed
        async def bad(v):
            pass


def test_checkbox_disabled_ignores_click():
    cb = play.new_checkbox(x=0, y=0, size_px=24, disabled=True)
    mouse.x = 0
    mouse.y = 0
    mouse_state.click_happened = True
    cb.update()
    mouse_state.click_happened = False
    assert cb.checked is False


def test_checkbox_checked_setter():
    cb = play.new_checkbox()
    cb.checked = True
    assert cb.checked is True
    cb.checked = False
    assert cb.checked is False


def test_checkbox_label_setter():
    cb = play.new_checkbox(label="old")
    cb.label = "new"
    assert cb.label == "new"
    assert cb._should_recompute is True


def test_checkbox_disabled_setter():
    cb = play.new_checkbox()
    cb.disabled = True
    assert cb.disabled is True


def test_checkbox_alive():
    cb = play.new_checkbox()
    assert cb.alive()


def test_checkbox_image_rendered():
    cb = play.new_checkbox()
    assert cb.image is not None


def test_checkbox_clone():
    cb = play.new_checkbox(label="X", checked=True, disabled=True)
    c = cb.clone()
    assert c.label == "X"
    assert c.checked is True
    assert c.disabled is True
