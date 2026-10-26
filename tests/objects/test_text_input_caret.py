"""Tests for the TextInput caret: when it shows, when it blinks, when it redraws.

Mutation testing found this behaviour completely unconstrained — every
``_cursor_visible = True`` and ``_should_recompute = True`` in text_input.py
could be flipped with the whole suite still passing. The field could stop
showing a caret entirely, or stop redrawing after a keystroke, and nothing
would fail.

It matters because the caret is the only feedback that a field is focused and
where typing will land. A caret that never reappears after a keystroke reads as
a dead widget.

Time is controlled rather than waited on: the blink is a 500ms wall-clock
interval, and a test that slept for it would add a second to the suite and stay
flaky anyway.
"""

import pygame
import pytest

import play
from play.objects.widgets import text_input_registry as registry
from tests.conftest import click_at, count_color


@pytest.fixture
def field():
    """A text field in the middle of the screen holding "hello"."""
    return play.new_text_input(x=0, y=0, value="hello")


def _keydown(key):
    """A KEYDOWN event for *key* without modifier keys."""
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": 0})


# ---------------------------------------------------------------------------
# blinking
# ---------------------------------------------------------------------------


def test_a_field_shows_its_caret_as_soon_as_it_is_clicked(monkeypatch):
    """A field the user has just focused must show its caret at once."""
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 0)
    empty = play.new_text_input(x=0, y=0, text_color="red")
    empty._cursor_visible = False

    click_at(0, 0, empty)

    assert count_color(empty.image, (255, 0, 0)) > 0


def test_caret_toggles_after_the_blink_interval(field, monkeypatch):
    """Focused, the caret flips state every 500ms — that is the blink."""
    registry.focus(field)
    field._cursor_visible = True
    field._last_blink = 0

    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 500)
    field.update()

    assert field._cursor_visible is False, "the caret should have blinked off"

    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 1000)
    field.update()

    assert field._cursor_visible is True, "the caret should have blinked back on"


def test_caret_holds_still_inside_the_blink_interval(field, monkeypatch):
    """Before 500ms nothing changes — otherwise the caret flickers every frame."""
    registry.focus(field)
    field._cursor_visible = True
    field._last_blink = 0

    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 499)
    field.update()

    assert field._cursor_visible is True


def test_a_field_clicked_late_in_the_program_keeps_its_caret_for_half_a_second(
    monkeypatch,
):
    now = [10_000]
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: now[0])
    late = play.new_text_input(x=0, y=0, text_color="red")
    click_at(0, 0, late)

    now[0] = 10_400
    late.update()

    assert count_color(late.image, (255, 0, 0)) > 0


@pytest.mark.parametrize(
    "now",
    [
        0,
        pytest.param(
            10_000,
            marks=pytest.mark.xfail(
                strict=True,
                reason="Tab focuses a field without restarting its blink, "
                "so after the first half second it starts with the caret off",
            ),
        ),
    ],
    ids=["at the start", "later on"],
)
def test_a_field_reached_with_tab_shows_its_caret_at_once(monkeypatch, now):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: now)
    first = play.new_text_input(x=0, y=100)
    second = play.new_text_input(x=0, y=-100, text_color="red")
    click_at(0, 100, first)

    first._handle_keydown(_keydown(pygame.K_TAB))
    second.update()

    assert count_color(second.image, (255, 0, 0)) > 0


def test_blinking_redraws_the_field(field, monkeypatch):
    """A caret that changes state without a redraw never appears on screen.

    Asserts the redraw happened rather than that _should_recompute is set:
    update() ends by calling super().update(), which consumes the flag by
    redrawing, so reading it afterwards always shows False whether or not the
    redraw took place.
    """
    registry.focus(field)
    field._cursor_visible = True
    field._last_blink = 0

    renders = []
    monkeypatch.setattr(
        type(field), "_render", lambda self: renders.append(1), raising=True
    )

    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 100)
    field.update()
    before = len(renders)

    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 600)
    field.update()

    assert len(renders) > before, "the blink should have triggered a redraw"


def test_an_unfocused_field_does_not_blink(field, monkeypatch):
    """Only the focused field shows a caret, so only it should be blinking."""
    registry.clear_focus()
    field._cursor_visible = True
    field._last_blink = 0

    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 5000)
    field.update()

    assert field._cursor_visible is True, "an unfocused field should not blink"


# ---------------------------------------------------------------------------
# typing and moving put the caret back on
# ---------------------------------------------------------------------------


def test_typing_shows_the_caret_immediately(field):
    """Typing mid-blink must not leave the caret hidden.

    Otherwise a keystroke that lands during the off half of the blink types
    into a field with no visible cursor.
    """
    registry.focus(field)
    field._cursor_visible = False

    field._handle_text_input("x")

    assert field._cursor_visible is True
    assert field.value == "hellox"


@pytest.mark.parametrize(
    "key", [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_HOME, pygame.K_END]
)
def test_moving_the_caret_shows_it(field, key, monkeypatch):
    """Moving the caret is exactly when the user needs to see where it went."""
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 0)
    registry.focus(field)
    field._handle_keydown(_keydown(pygame.K_LEFT))
    field._handle_keydown(_keydown(pygame.K_LEFT))
    field._cursor_visible = False
    field.update()
    hidden = pygame.image.tobytes(field.image, "RGBA")

    field._handle_keydown(_keydown(key))
    field.update()

    assert field._cursor_visible is True
    assert pygame.image.tobytes(field.image, "RGBA") != hidden


def test_typing_resets_the_blink_clock(field, monkeypatch):
    """The caret should stay lit for a full interval after a keystroke.

    Without resetting the clock, a keystroke arriving just before the next
    blink tick shows the caret for a few milliseconds and then hides it.
    """
    registry.focus(field)
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 4000)

    field._handle_text_input("x")

    assert field._last_blink == 4000


# ---------------------------------------------------------------------------
# max_length
# ---------------------------------------------------------------------------


def test_a_full_field_accepts_nothing_more():
    """A field at max_length must drop the keystroke, not append past the limit."""
    full = play.new_text_input(x=0, y=0, value="abc", max_length=3)
    registry.focus(full)
    changes = []
    full.when_changed(changes.append)

    full._handle_text_input("d")

    assert full.value == "abc"
    assert changes == []


def test_a_nearly_full_field_takes_only_what_fits():
    """Pasting more than the remaining room keeps the prefix that fits."""
    nearly = play.new_text_input(x=0, y=0, value="ab", max_length=4)
    registry.focus(nearly)

    nearly._handle_text_input("cdef")

    assert nearly.value == "abcd"


# ---------------------------------------------------------------------------
# constructor defaults
# ---------------------------------------------------------------------------


def test_a_default_field_is_usable():
    """The no-argument defaults must produce an interactive field at the centre.

    Mutation testing flipped `disabled=False` to True with nothing failing: no
    test constructed a plain field and then used it.
    """
    plain = play.new_text_input()

    assert plain.x == 0 and plain.y == 0
    assert plain.disabled is False
    assert plain.readonly is False
    assert plain.password_mode is False

    registry.focus(plain)
    plain._handle_text_input("typed")

    assert plain.value == "typed", "a default field should accept typing"
