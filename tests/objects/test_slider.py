"""Tests for the Slider widget."""

import pytest
import play
from play.io.mouse import mouse
from play.core.mouse_loop import mouse_state


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_slider_creation():
    s = play.new_slider(min_value=0, max_value=100, value=50)
    assert s.min_value == 0
    assert s.max_value == 100
    assert s.value == 50


def test_slider_clamps_initial_value():
    s = play.new_slider(min_value=0, max_value=10, value=200)
    assert s.value == 10


def test_slider_clamps_initial_value_low():
    s = play.new_slider(min_value=5, max_value=10, value=1)
    assert s.value == 5


def test_slider_value_setter_clamps():
    s = play.new_slider(min_value=0, max_value=100, value=50)
    s.value = 150
    assert s.value == 100
    s.value = -10
    assert s.value == 0


def test_slider_min_value_setter():
    s = play.new_slider(min_value=0, max_value=100, value=50)
    s.min_value = 60
    assert s.value == 60  # clamped up


def test_slider_max_value_setter():
    s = play.new_slider(min_value=0, max_value=100, value=80)
    s.max_value = 70
    assert s.value == 70  # clamped down


def test_slider_when_changed_fires():
    s = play.new_slider(min_value=0, max_value=100, value=50)
    results = []
    s.when_changed(results.append)
    s.value = 75
    assert results == [75]


def test_slider_when_changed_rejects_async():
    s = play.new_slider()
    with pytest.raises(TypeError):

        @s.when_changed
        async def bad(v):
            pass


def test_slider_disabled_default_false():
    s = play.new_slider()
    assert s.disabled is False


def test_slider_disabled_setter():
    s = play.new_slider()
    s.disabled = True
    assert s.disabled is True


def test_slider_alive():
    s = play.new_slider()
    assert s.alive()


def test_slider_image_rendered():
    s = play.new_slider()
    assert s.image is not None


def test_slider_clone():
    s = play.new_slider(min_value=10, max_value=90, value=40)
    c = s.clone()
    assert c.min_value == 10
    assert c.max_value == 90
    assert c.value == 40
