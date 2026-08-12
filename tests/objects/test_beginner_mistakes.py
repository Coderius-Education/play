"""What happens when a beginner gets it wrong.

This library is aimed at people learning to program, so a mistake has three
possible outcomes and only two of them are acceptable:

1. the library forgives it and does something sensible (out-of-range values
   get clamped, an empty label is fine),
2. it raises immediately, at the line the student wrote, with a message that
   names the problem and suggests a fix,
3. it does nothing at all, or crashes later inside pygame/pymunk with a
   traceback that points at library internals.

Outcome 3 is what leaves a twelve-year-old stuck, and it is what these tests
exist to prevent. Each one pins a mistake to outcome 1 or 2.
"""

import pytest
import play


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


# Every widget factory, with the smallest call that builds one.
WIDGET_FACTORIES = {
    "button": lambda **kw: play.new_button("Go", **kw),
    "checkbox": lambda **kw: play.new_checkbox("Sound", **kw),
    "slider": lambda **kw: play.new_slider(**kw),
    "progress_bar": lambda **kw: play.new_progress_bar(**kw),
    "dropdown": lambda **kw: play.new_dropdown(options=["A", "B"], **kw),
    "radio_button": lambda **kw: play.new_radio_button("A", value="a", **kw),
    "text_input": lambda **kw: play.new_text_input(**kw),
}
FACTORY_NAMES = sorted(WIDGET_FACTORIES)

# Not every widget spells its main colour `color`: Slider and ProgressBar use
# their own names, so `play.new_slider(color="blue")` is a TypeError. That is
# a real papercut for a beginner, tracked as a naming follow-up on the PR.
COLOUR_ARG = {
    "button": "color",
    "checkbox": "color",
    "dropdown": "color",
    "radio_button": "color",
    "text_input": "color",
    "slider": "track_color",
    "progress_bar": "background_color",
}


# ── a mistyped colour is caught at the line that made the widget ──────────────


@pytest.mark.parametrize("name", FACTORY_NAMES)
def test_mistyped_colour_fails_immediately_with_a_helpful_message(name):
    # "blu" instead of "blue" is the archetypal beginner typo. It must not
    # sail through construction and then explode three frames later inside
    # _render, where the traceback points at the library, not their code.
    with pytest.raises(ValueError, match="color name we didn't understand"):
        WIDGET_FACTORIES[name](**{COLOUR_ARG[name]: "blu"})


def test_the_colour_error_repeats_the_word_they_typed():
    # Naming the offending value is what lets a student find it in their file.
    with pytest.raises(ValueError, match="reddd"):
        play.new_button("Go", color="reddd")


# ── a back-to-front range is explained, not silently dead ─────────────────────


@pytest.mark.parametrize("factory", ["slider", "progress_bar"])
def test_swapped_min_and_max_says_so(factory):
    # Left alone this is silent nonsense: every value clamps to min_value and
    # the span is negative, so a slider freezes and a bar reads empty while
    # .value claims otherwise.
    with pytest.raises(ValueError, match="min_value has to be smaller"):
        WIDGET_FACTORIES[factory](min_value=100, max_value=0)


@pytest.mark.parametrize("factory", ["slider", "progress_bar"])
def test_equal_min_and_max_says_so(factory):
    with pytest.raises(ValueError, match="min_value has to be smaller"):
        WIDGET_FACTORIES[factory](min_value=50, max_value=50)


def test_the_range_error_suggests_the_swap():
    with pytest.raises(ValueError, match=r"min_value=0, max_value=100"):
        play.new_slider(min_value=100, max_value=0)


# ── an async handler is rejected by name ──────────────────────────────────────


def test_async_handler_is_rejected_and_names_the_function():
    # `async def` is copied from tutorials constantly. Silently never calling
    # the handler would be the worst outcome here.
    checkbox = play.new_checkbox("Sound")
    with pytest.raises(TypeError, match="on_change"):

        @checkbox.when_changed
        async def on_change(_checked):
            pass


# ── forgiving where forgiveness is right ──────────────────────────────────────


def test_value_outside_the_range_is_clamped_not_rejected():
    # Guessing a value outside the range is a slip, not a bug worth stopping
    # for -- the widget should just do the sensible thing.
    assert play.new_slider(min_value=0, max_value=10, value=999).value == 10
    assert play.new_slider(min_value=0, max_value=10, value=-999).value == 0
    assert play.new_progress_bar(min_value=0, max_value=10, value=999).value == 10


def test_dropdown_index_past_the_end_is_clamped():
    dd = play.new_dropdown(options=["A", "B"], selected_index=99)
    assert dd.selected_value in ("A", "B")


def test_empty_and_missing_labels_are_fine():
    assert play.new_checkbox("").label == ""
    assert play.new_button("").text == ""
    assert play.new_dropdown(options=[]).selected_value is None


@pytest.mark.parametrize("name", FACTORY_NAMES)
def test_a_widget_can_be_built_with_no_arguments_at_all(name):
    # The first thing a student types is `play.new_slider()`. It has to work.
    widget = WIDGET_FACTORIES[name]()
    widget.update()
    assert widget.image is not None


# ── a removed widget stays quiet ──────────────────────────────────────────────


@pytest.mark.parametrize("name", FACTORY_NAMES)
def test_updating_a_removed_widget_does_not_crash(name):
    # Students remove things and keep the variable around. That must not blow
    # up the whole game on the next frame.
    widget = WIDGET_FACTORIES[name]()
    widget.remove()
    widget.update()
    widget.update()
