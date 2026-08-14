"""Every widget that renders user text, against text users actually paste.

A soft hyphen in a checkbox label crashes the program with
``pygame.error: Text has zero width``. That was found by an existing property
test drawing a random label, which means it is a family rather than a one-off:
any character that renders to nothing takes the same path.

The audience is beginners, and a label is the most likely place for a stray
character to arrive — pasted from a worksheet, a website, or a chat message.
Crashing the whole game because a label contains a soft hyphen is not a
reasonable response to that.

Each case is a real thing text does, not fuzzing for its own sake.
"""

import pytest

import play

# Strings that render to zero width. These are the crashing family.
ZERO_WIDTH = {
    "soft_hyphen": "\xad",
    "zero_width_space": "\u200b",
    "zero_width_joiner": "\u200d",
}

# Unusual but rendering fine today. These are the regression guard for any fix
# to the family above: the fix must not become "reject anything unusual".
AWKWARD = {
    "empty": "",
    "space": " ",
    "newline": "a\nb",
    "tab": "a\tb",
    "emoji": "\U0001f600",
    "combining_sequence": "\u00e1",
    # A lone combining accent carries no width of its own yet still renders,
    # so it belongs here rather than with the crashing set.
    "combining_acute_alone": "\u0301",
    "rtl": "\u05d0\u05d1",
    "long": "x" * 500,
    "quotes": 'it\'s "quoted"',
}

# Every widget that puts user-supplied text through font.render().
WIDGETS = {
    "button": lambda t: play.new_button(text=t),
    "checkbox": lambda t: play.new_checkbox(label=t, size_px=24),
    "dropdown": lambda t: play.new_dropdown(options=[t, "other"]),
    "radio_button": lambda t: play.new_radio_button(
        label=t, value="v", group=play.new_radio_group()
    ),
    "text": lambda t: play.new_text(words=t),
    "text_input": lambda t: play.new_text_input(value=t),
    "tooltip": lambda t: play.new_tooltip(
        target=play.new_box(color="red", x=0, y=0, width=20, height=20), text=t
    ),
}


@pytest.mark.parametrize("widget_name", sorted(WIDGETS))
@pytest.mark.parametrize("case_name", sorted(AWKWARD))
def test_awkward_text_renders(widget_name, case_name):
    """Unusual but well-formed text must render without taking the game down."""
    widget = WIDGETS[widget_name](AWKWARD[case_name])
    widget.update()


@pytest.mark.xfail(
    strict=True,
    reason=(
        "pygame's font.render() raises 'Text has zero width' for text that "
        "renders to nothing, and every widget passes user text straight to "
        "it. One invisible character pasted into a label ends the program. "
        "Fixing it means a guarded render shared by all nine widget modules, "
        "which is a rendering change across the whole widget set"
    ),
)
@pytest.mark.parametrize("widget_name", sorted(WIDGETS))
@pytest.mark.parametrize("case_name", sorted(ZERO_WIDTH))
def test_zero_width_text_does_not_crash(widget_name, case_name):
    """Text that renders to nothing must render as nothing, not raise.

    pygame's font.render() raises "Text has zero width" for these. Every
    widget passes user text straight to it, so a single invisible character
    anywhere in a label ends the program.
    """
    widget = WIDGETS[widget_name](ZERO_WIDTH[case_name])
    widget.update()
