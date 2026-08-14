"""One click must produce exactly one action, for every interactive widget.

``update()`` runs once per physics sub-step, not once per frame — roughly ten
times per frame at the default ``num_sim_steps``. A widget action written the
obvious way (``checked = not checked``) therefore fires ten times per click and
lands back where it started, and a button calls the student's function ten
times over.

Each widget guards against this individually today. This checks the property
across all of them at once, so the tenth widget someone adds is covered the day
it is written rather than the day someone notices the bug.

Driven through the real game loop with real pygame events: the whole point is
the per-sub-step cadence, which only exists inside start_program().
"""

import pytest

import play
from tests.conftest import post_mouse_motion, post_mouse_down, post_mouse_up
from tests.projects.conftest import add_safety_timeout


def _screen_xy(screen, x, y):
    return int(screen.width / 2 + x), int(screen.height / 2 - y)


async def _click(screen, x, y):
    pos = _screen_xy(screen, x, y)
    post_mouse_motion(*pos)
    await play.animate()
    post_mouse_down(*pos)
    await play.animate()
    post_mouse_up(*pos)
    await play.animate()


def _run_one_click(build, x=0, y=0, frames=120):
    """Build a widget, click it once through the loop, return the recorded calls.

    `build` takes a `record` callback and returns the widget.
    """
    from play.io.screen import screen

    calls = []
    widget = build(calls.append)

    @play.when_program_starts
    async def driver():
        for _ in range(3):
            await play.animate()
        await _click(screen, x, y)
        play.stop_program()

    add_safety_timeout(frames)
    play.start_program()
    return widget, calls


# ---------------------------------------------------------------------------
# callbacks fire once
# ---------------------------------------------------------------------------


def test_button_calls_its_action_once():
    """The clearest case: a button that fires ten times fires the student's
    function ten times — ten bullets, ten points, ten lives lost."""

    def build(record):
        button = play.new_button(text="fire", x=0, y=0, width=160, height=50)
        button.when_clicked(lambda: record(1))
        return button

    _, calls = _run_one_click(build)

    assert len(calls) == 1, f"one click should fire one action, got {len(calls)}"


def test_checkbox_toggles_once():
    """A toggle is the action that cannot survive being run ten times.

    An even number of toggles lands back on the original value, so the bug
    shows up as a checkbox that will not tick at all.
    """

    def build(record):
        box = play.new_checkbox(label="sound", x=0, y=0, size_px=40)
        box.when_changed(record)
        return box

    box, calls = _run_one_click(build)

    assert box.checked is True, "one click should leave the box ticked"
    assert len(calls) == 1, f"one click should report one change, got {len(calls)}"


def test_radio_group_reports_one_change():
    """Selecting is idempotent, but the change notification is not."""

    def build(record):
        group = play.new_radio_group()
        play.new_radio_button(label="a", value="a", group=group, x=-60, y=0, size_px=30)
        target = play.new_radio_button(
            label="b", value="b", group=group, x=0, y=0, size_px=30
        )
        group.when_changed(record)
        return target

    target, calls = _run_one_click(build)

    assert target.selected is True
    assert len(calls) == 1, f"one click should report one change, got {len(calls)}"


def test_dropdown_opens_once():
    """Open/closed is a toggle, so ten dispatches would leave it shut."""

    def build(record):
        menu = play.new_dropdown(options=["easy", "hard"], x=0, y=0, width=160)
        menu.when_changed(lambda value, index: record(value))
        return menu

    menu, calls = _run_one_click(build)

    assert menu._dropdown_open is True, "one click should leave the menu open"
    assert not calls, "opening a menu is not choosing an option"


# ---------------------------------------------------------------------------
# repeated clicks stay in step
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("clicks", [2, 3])
def test_a_checkbox_follows_every_click(clicks):
    """Two clicks off, three clicks on — the count has to track exactly.

    Catches a widget that is idempotent within one click but loses or doubles
    across clicks, which a single-click test cannot see.
    """
    from play.io.screen import screen

    changes = []
    box = play.new_checkbox(label="sound", x=0, y=0, size_px=40)
    box.when_changed(changes.append)

    @play.when_program_starts
    async def driver():
        for _ in range(3):
            await play.animate()
        for _ in range(clicks):
            await _click(screen, 0, 0)
            for _ in range(2):
                await play.animate()
        play.stop_program()

    add_safety_timeout(200)
    play.start_program()

    assert len(changes) == clicks, f"expected {clicks} changes, got {len(changes)}"
    assert box.checked is (clicks % 2 == 1)


# ---------------------------------------------------------------------------
# non-interactive widgets stay out of the way
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "factory",
    [
        lambda: play.new_progress_bar(min_value=0, max_value=100, value=50, x=0, y=0),
        lambda: play.new_text(words="score", x=0, y=0),
    ],
)
def test_decorative_widgets_do_not_take_the_click(factory):
    """A progress bar or label over the playfield must not absorb clicks.

    They are decoration; taking ownership would make the game under them
    unresponsive wherever the HUD happens to sit.
    """
    from play.io.screen import screen

    sprite_clicks = []
    field = play.new_box(color="green", x=0, y=0, width=400, height=400)
    field.when_clicked(lambda: sprite_clicks.append(1))
    factory()

    @play.when_program_starts
    async def driver():
        for _ in range(3):
            await play.animate()
        await _click(screen, 0, 0)
        play.stop_program()

    add_safety_timeout(120)
    play.start_program()

    assert sprite_clicks, "a decorative widget should not swallow the click"
