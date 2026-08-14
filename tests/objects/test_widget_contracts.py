"""The shape of each widget's public API, pinned.

Two things are recorded here, both listed as known follow-ups on the PR that
introduced these widgets:

  - Dropdown's when_changed passes (value, index) while every other widget
    passes (value). Normalising that is a breaking change for anyone who has
    already written a handler, so it should be a decision rather than a
    surprise. These tests make it one.

  - Several constructor arguments have no matching readable property. The list
    lives in prose in the PR description, where nothing checks it. Here it is
    enumerated, so adding a property makes a test fail and the list gets
    updated instead of quietly rotting.

The point is not that the current shape is right. It is that changing it
becomes visible.
"""

import inspect

import pytest

import play


# ---------------------------------------------------------------------------
# when_changed signatures
# ---------------------------------------------------------------------------


def test_checkbox_when_changed_passes_only_the_value():
    seen = []
    box = play.new_checkbox(label="sound")
    box.when_changed(lambda *args: seen.append(args))

    box.checked = True

    assert seen == [(True,)], f"expected a single value argument, got {seen}"


def test_slider_when_changed_passes_only_the_value():
    seen = []
    slider = play.new_slider(min_value=0, max_value=10, value=0)
    slider.when_changed(lambda *args: seen.append(args))

    slider.value = 7

    assert seen == [(7,)], f"expected a single value argument, got {seen}"


def test_text_input_when_changed_passes_only_the_value():
    seen = []
    field = play.new_text_input(value="")
    field.when_changed(lambda *args: seen.append(args))

    field._handle_text_input("hi")

    assert seen == [("hi",)], f"expected a single value argument, got {seen}"


def test_radio_group_when_changed_passes_only_the_value():
    seen = []
    group = play.new_radio_group()
    play.new_radio_button(label="a", value="a", group=group)
    play.new_radio_button(label="b", value="b", group=group)
    group.when_changed(lambda *args: seen.append(args))

    group.selected_value = "b"

    assert seen == [("b",)], f"expected a single value argument, got {seen}"


def test_dropdown_when_changed_passes_value_and_index():
    """The odd one out, recorded deliberately.

    Every other widget hands the handler one argument. A student who learns
    the pattern on a checkbox and applies it to a dropdown gets a TypeError.
    Listed on the PR as a known follow-up; normalising it breaks existing
    handlers, so this test is what makes that a deliberate change.

    Driven through _select() because the selected_index setter does not
    notify at all — see the test below.
    """
    seen = []
    menu = play.new_dropdown(options=["a", "b"])
    menu.when_changed(lambda *args: seen.append(args))

    menu._select(1)

    assert seen == [("b", 1)], f"expected (value, index), got {seen}"


def test_setting_a_dropdown_in_code_does_not_notify():
    """The second inconsistency, and the one more likely to bite.

    checked=, value= and selected_value= all fire when_changed on the other
    widgets, so a game can set state in code and let its own handler react.
    Assigning selected_index does not, which means a dropdown changed by the
    game silently skips the handler that every sibling widget would run.

    Pinned as the current behaviour rather than asserted as correct: changing
    it is a behaviour change for anyone relying on either side of it.
    """
    seen = []
    menu = play.new_dropdown(options=["a", "b"])
    menu.when_changed(lambda *args: seen.append(args))

    menu.selected_index = 1

    assert menu.selected_value == "b", "the assignment should still take effect"
    assert seen == [], (
        "selected_index currently does not notify; if that changed, update "
        "this test and check it matches the other widgets"
    )


# ---------------------------------------------------------------------------
# constructor arguments without a matching property
# ---------------------------------------------------------------------------

# Constructor arguments that a reader would reasonably expect to be readable
# back, and currently are not. Adding a property should delete its entry here.
KNOWN_MISSING_PROPERTIES = {
    "new_slider": ["track_color", "thumb_color", "step"],
    "new_tooltip": ["text_color", "background_color"],
    "new_progress_bar": ["disabled"],
}

FACTORIES = {
    "new_slider": lambda: play.new_slider(min_value=0, max_value=10, value=5),
    "new_tooltip": lambda: play.new_tooltip(
        target=play.new_box(color="red", x=0, y=0, width=20, height=20), text="hi"
    ),
    "new_progress_bar": lambda: play.new_progress_bar(
        min_value=0, max_value=10, value=5
    ),
}


@pytest.mark.parametrize("factory_name", sorted(KNOWN_MISSING_PROPERTIES))
def test_known_missing_properties_are_still_missing(factory_name):
    """Fails when a gap is closed, so the list above stays honest."""
    widget = FACTORIES[factory_name]()
    still_missing = [
        name
        for name in KNOWN_MISSING_PROPERTIES[factory_name]
        if not hasattr(widget, name)
    ]

    assert still_missing == KNOWN_MISSING_PROPERTIES[factory_name], (
        f"{factory_name} has grown a property for "
        f"{set(KNOWN_MISSING_PROPERTIES[factory_name]) - set(still_missing)}; "
        "remove it from KNOWN_MISSING_PROPERTIES"
    )


@pytest.mark.parametrize(
    "factory_name,argument",
    [
        ("new_button", "text"),
        ("new_checkbox", "checked"),
        ("new_slider", "value"),
        ("new_progress_bar", "value"),
        ("new_dropdown", "selected_index"),
        ("new_text_input", "value"),
    ],
)
def test_core_constructor_arguments_round_trip(factory_name, argument):
    """The arguments a game actually reads back must be readable."""
    factory = getattr(play, factory_name)
    parameters = inspect.signature(factory).parameters
    assert argument in parameters, f"{factory_name} has no {argument} argument"

    widget = FACTORIES.get(factory_name, lambda: factory())()
    assert hasattr(
        widget, argument
    ), f"{factory_name} accepts {argument} but does not expose it to read back"
