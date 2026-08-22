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


def test_setting_a_dropdown_in_code_notifies():
    """Assigning selected_index fires when_changed, like every sibling widget.

    It used to be the exception: checked=, value= and selected_value= all
    notify, so a game could set state in code and let its own handler react,
    but a dropdown changed that way silently skipped the handler. Aligned
    deliberately — this test previously pinned the old behaviour and had to be
    rewritten when it changed, which is what it was for.
    """
    seen = []
    menu = play.new_dropdown(options=["a", "b"])
    menu.when_changed(lambda *args: seen.append(args))

    menu.selected_index = 1

    assert menu.selected_value == "b"
    assert seen == [("b", 1)], f"expected one (value, index) report, got {seen}"


def test_setting_a_dropdown_to_the_same_option_does_not_notify():
    """when_changed reports changes; re-selecting what is already selected
    is not one, and would otherwise fire on every assignment."""
    seen = []
    menu = play.new_dropdown(options=["a", "b"], selected_index=1)
    menu.when_changed(lambda *args: seen.append(args))

    menu.selected_index = 1

    assert seen == []


def test_clearing_a_dropdown_selection_reports_nothing_selected():
    """index -1 means nothing is selected, so the handler must not be handed
    the last option — which a bare `index < len(options)` check would do."""
    seen = []
    menu = play.new_dropdown(options=["a", "b"], selected_index=1)
    menu.when_changed(lambda *args: seen.append(args))

    menu.selected_index = -1

    assert menu.selected_value is None
    assert seen == [(None, -1)], f"expected (None, -1), got {seen}"


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


# ---------------------------------------------------------------------------
# range setters keep their bounds ordered
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "factory",
    [
        lambda: play.new_slider(min_value=0, max_value=10, value=5),
        lambda: play.new_progress_bar(min_value=0, max_value=10, value=5),
    ],
    ids=["slider", "progress_bar"],
)
def test_raising_min_above_max_keeps_the_range_ordered(factory):
    """A crossed range leaves a negative span, which reads as a frozen widget.

    Construction rejects a swapped range outright; the setters cannot, because
    `w.min_value = 100; w.max_value = 200` passes through an inverted state on
    its way to a perfectly good one. They keep the bounds ordered instead.
    """
    widget = factory()

    widget.min_value = 100

    assert (
        widget.max_value >= widget.min_value
    ), f"range inverted: {widget.min_value} > {widget.max_value}"


@pytest.mark.parametrize(
    "factory",
    [
        lambda: play.new_slider(min_value=0, max_value=10, value=5),
        lambda: play.new_progress_bar(min_value=0, max_value=10, value=5),
    ],
    ids=["slider", "progress_bar"],
)
def test_lowering_max_below_min_keeps_the_range_ordered(factory):
    widget = factory()

    widget.max_value = -50

    assert (
        widget.min_value <= widget.max_value
    ), f"range inverted: {widget.min_value} > {widget.max_value}"


def test_moving_a_slider_range_upwards_in_two_steps_works():
    """The sequence the setters deliberately tolerate rather than reject."""
    slider = play.new_slider(min_value=0, max_value=10, value=5)

    slider.min_value = 100
    slider.max_value = 200

    assert (slider.min_value, slider.max_value) == (100, 200)
    assert 100 <= slider.value <= 200


# ---------------------------------------------------------------------------
# dropdown layer bookkeeping
# ---------------------------------------------------------------------------


def test_setting_a_dropdowns_layer_while_open_survives_closing():
    """An open menu sits hoisted; an assignment means where it belongs.

    The resting layer is captured when the menu opens, so without recording a
    later assignment, closing would restore the old value and discard it.
    """
    menu = play.new_dropdown(options=["a", "b"], x=0, y=0, layer=10)
    menu._set_open(True)

    menu.layer = 50

    menu._set_open(False)
    assert menu.layer == 50, f"the assignment was discarded on close ({menu.layer})"


def test_opening_a_dropdown_repeatedly_does_not_escalate_its_layer():
    """_set_open drives the layer itself, so it must bypass the public setter.

    Going through it would record the boosted layer as the resting one and
    boost that again on the next open, climbing without limit.
    """
    menu = play.new_dropdown(options=["a", "b"], x=0, y=0, layer=10)

    for _ in range(5):
        menu._set_open(True)
        menu._set_open(False)

    assert menu.layer == 10, f"layer drifted to {menu.layer} after repeated opens"
