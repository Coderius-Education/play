"""Coverage tests for play.core.keyboard_loop — KEYDOWN/KEYUP event processing."""

import pytest
import pygame
import play
from play.core.keyboard_loop import handle_keyboard_events
from play.io.keypress import keyboard_state, KEYS_TO_SKIP


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_handle_keydown_adds_to_pressed():
    """KEYDOWN event should add key name to keyboard_state.pressed."""
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_a})
    handle_keyboard_events(event)
    assert "a" in keyboard_state.pressed


def test_handle_keydown_no_duplicates():
    """Pressing the same key twice shouldn't duplicate it in pressed."""
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_b})
    handle_keyboard_events(event)
    handle_keyboard_events(event)
    assert keyboard_state.pressed.count("b") == 1


def test_handle_keyup_removes_from_pressed():
    """KEYUP event should remove key from pressed and add to released."""
    down = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_c})
    up = pygame.event.Event(pygame.KEYUP, {"key": pygame.K_c})
    handle_keyboard_events(down)
    assert "c" in keyboard_state.pressed

    handle_keyboard_events(up)
    assert "c" not in keyboard_state.pressed
    assert "c" in keyboard_state.released


def test_handle_keyup_without_keydown():
    """KEYUP for a key not in pressed should not crash or add to released."""
    up = pygame.event.Event(pygame.KEYUP, {"key": pygame.K_z})
    handle_keyboard_events(up)
    # z was never pressed, so it shouldn't be in released either
    assert "z" not in keyboard_state.released


def test_skipped_keys_ignored():
    """Keys in KEYS_TO_SKIP should not be added to pressed."""
    for skip_key in KEYS_TO_SKIP:
        event = pygame.event.Event(pygame.KEYDOWN, {"key": skip_key})
        handle_keyboard_events(event)

    # None of the skipped keys should appear in pressed
    assert len(keyboard_state.pressed) == 0
