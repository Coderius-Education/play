"""The play.new_* widget functions hand every argument, and every default, on to the widget."""

import inspect

import pygame
import pytest

import play
from play.io.mouse import mouse
from play.objects.widgets.button import Button
from play.objects.widgets.checkbox import Checkbox
from play.objects.widgets.dropdown import Dropdown
from play.objects.widgets.progress_bar import ProgressBar
from play.objects.widgets.radio_button import RadioButton
from play.objects.widgets.slider import Slider
from play.objects.widgets.text_input import TextInput
from play.objects.widgets.tooltip import Tooltip
from tests.conftest import click_at


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


PAIRS = {
    "button": (play.new_button, Button),
    "checkbox": (play.new_checkbox, Checkbox),
    "dropdown": (play.new_dropdown, Dropdown),
    "progress_bar": (play.new_progress_bar, ProgressBar),
    "radio_button": (play.new_radio_button, RadioButton),
    "slider": (play.new_slider, Slider),
    "text_input": (play.new_text_input, TextInput),
    "tooltip": (play.new_tooltip, Tooltip),
}


def _defaults(function):
    return {
        name: parameter.default
        for name, parameter in inspect.signature(function).parameters.items()
        if name != "self"
    }


@pytest.mark.parametrize("name", sorted(PAIRS))
def test_a_new_function_has_the_same_arguments_and_defaults_as_its_widget(name):
    generator, widget_class = PAIRS[name]
    assert _defaults(generator) == _defaults(widget_class.__init__)


def _image(sprite):
    return pygame.image.tobytes(sprite.image, "RGBA")


def _hovered(widget, x):
    mouse.x, mouse.y = x, 0
    widget.update()
    return _image(widget)


def _probe_button(widget, x):
    return [_hovered(widget, x), widget.hover_color, widget.click_color]


def _probe_checkbox(widget, x):
    return [_image(widget), _hovered(widget, x), widget.checked, widget.label]


def _probe_slider(widget, x):
    seen = [_image(widget), widget.min_value, widget.max_value, widget.value]
    widget.value = 45
    return seen + [widget.value, _image(widget)]


def _probe_progress_bar(widget, x):
    return [_image(widget), widget.min_value, widget.max_value, widget.value]


def _probe_dropdown(widget, x):
    seen = [_image(widget), _hovered(widget, x), widget.selected_index]
    click_at(x, 0, widget)
    mouse.x, mouse.y = x, -60
    widget.update()
    return seen + [_image(widget), widget.layer]


def _probe_radio_button(widget, x):
    return [_image(widget), _hovered(widget, x), widget.selected, widget.value]


def _probe_text_input(widget, x):
    seen = [_image(widget), widget.value, widget.readonly, widget.password_mode]
    widget.readonly = False
    widget.value = ""
    widget._handle_text_input("abcdefgh")
    return seen + [widget.value, _image(widget)]


def _probe_tooltip(widget, x):
    mouse.x, mouse.y = 0, 0
    widget.update()
    return [_image(widget), widget.rect.topleft, widget.layer]


SETTINGS = {
    "button": dict(
        text="Go",
        width=120,
        height=40,
        color="blue",
        hover_color="green",
        click_color="orange",
        text_color="yellow",
        font_size=24,
        border_radius=3,
        transparency=80,
        size=90,
        layer=12,
        disabled=True,
        disabled_color="silver",
        disabled_text_color="red",
    ),
    "checkbox": dict(
        label="Sound",
        checked=True,
        size_px=30,
        color="yellow",
        check_color="green",
        border_color="blue",
        hover_border_color="red",
        label_color="purple",
        font_size=22,
        border_radius=2,
        transparency=90,
        layer=11,
    ),
    "slider": dict(
        min_value=10,
        max_value=90,
        value=30,
        width=150,
        height=16,
        track_color="yellow",
        fill_color="green",
        thumb_color="red",
        thumb_radius=8,
        border_radius=4,
        transparency=90,
        layer=11,
        show_value=True,
        font_size=18,
        value_color="purple",
        step=20,
    ),
    "progress_bar": dict(
        min_value=10,
        max_value=90,
        value=30,
        width=150,
        height=20,
        bar_color="green",
        background_color="yellow",
        border_color="blue",
        border_width=2,
        border_radius=2,
        transparency=90,
        layer=3,
        show_label=True,
        label_color="red",
        font_size=16,
    ),
    "dropdown": dict(
        options=["a", "b", "c"],
        selected_index=2,
        width=140,
        height=30,
        color="yellow",
        hover_color="orange",
        option_hover_color="red",
        text_color="blue",
        border_color="green",
        border_width=2,
        border_radius=2,
        font_size=16,
        transparency=90,
        layer=25,
    ),
    "radio_button": dict(
        label="Easy",
        value="e",
        size_px=26,
        color="yellow",
        selected_color="green",
        border_color="blue",
        hover_border_color="red",
        label_color="purple",
        font_size=20,
        transparency=90,
        layer=11,
        selected=True,
    ),
    "text_input": dict(
        placeholder="name",
        value="abcdef",
        width=150,
        height=30,
        color="yellow",
        active_color="orange",
        text_color="blue",
        placeholder_color="purple",
        font_size=18,
        border_color="green",
        border_width=2,
        border_radius=2,
        max_length=4,
        transparency=90,
        size=90,
        layer=11,
        readonly=True,
        password_mode=True,
    ),
    "tooltip": dict(
        text="tip",
        offset_x=20,
        offset_y=-30,
        color="yellow",
        text_color="blue",
        border_color="green",
        font_size=18,
        padding=4,
        border_radius=2,
        transparency=90,
        layer=99,
    ),
}

PROBES = {
    "button": _probe_button,
    "checkbox": _probe_checkbox,
    "dropdown": _probe_dropdown,
    "progress_bar": _probe_progress_bar,
    "radio_button": _probe_radio_button,
    "slider": _probe_slider,
    "text_input": _probe_text_input,
    "tooltip": _probe_tooltip,
}


def _build(name, factory, x):
    settings = dict(SETTINGS[name])
    if name == "tooltip":
        settings["target"] = play.new_box(x=0, y=0, width=40, height=40)
    else:
        settings.update(x=x, y=0)
    if name == "radio_button":
        settings["group"] = play.new_radio_group()
    return factory(**settings)


@pytest.mark.parametrize("name", sorted(PAIRS))
def test_a_new_function_builds_the_same_widget_as_its_class(name):
    generator, widget_class = PAIRS[name]
    from_function = _build(name, generator, x=-200)
    from_class = _build(name, widget_class, x=200)
    assert type(from_function) is widget_class
    assert PROBES[name](from_function, -200) == PROBES[name](from_class, 200)
