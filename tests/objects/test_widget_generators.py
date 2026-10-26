"""The play.new_* widget functions hand every argument, and every default, on to the widget."""

import inspect

import pytest

import play
from play.api import generators
from play.objects.widgets.button import Button
from play.objects.widgets.checkbox import Checkbox
from play.objects.widgets.dropdown import Dropdown
from play.objects.widgets.progress_bar import ProgressBar
from play.objects.widgets.radio_button import RadioButton
from play.objects.widgets.slider import Slider
from play.objects.widgets.text_input import TextInput
from play.objects.widgets.tooltip import Tooltip


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
    """Each parameter of *function* (but self) mapped to its default."""
    return {
        name: parameter.default
        for name, parameter in inspect.signature(function).parameters.items()
        if name != "self"
    }


@pytest.mark.parametrize("name", sorted(PAIRS))
def test_a_new_function_has_the_same_arguments_and_defaults_as_its_widget(name):
    generator, widget_class = PAIRS[name]
    assert _defaults(generator) == _defaults(widget_class.__init__)


@pytest.mark.parametrize("name", sorted(PAIRS))
def test_a_new_function_hands_each_argument_to_the_same_widget_argument(
    name, monkeypatch
):
    generator, widget_class = PAIRS[name]
    received = []
    built = object()

    def record(*args, **kwargs):
        received.append(inspect.signature(widget_class).bind(*args, **kwargs))
        return built

    monkeypatch.setattr(generators, f"_{widget_class.__name__}", record)
    given = {
        parameter: object() for parameter in inspect.signature(generator).parameters
    }

    assert generator(**given) is built
    assert [call.arguments for call in received] == [given]
