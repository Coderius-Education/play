"""play's messages reach the terminal with their level and where they came from."""

import logging

from play.io.logging import play_logger


def _terminal_handlers(level):
    """The handlers of play's logger that print messages of *level*."""
    return [h for h in play_logger.handlers if h.level <= level]


def test_warnings_such_as_a_forgotten_await_are_printed():
    assert play_logger.isEnabledFor(logging.WARNING)
    assert _terminal_handlers(logging.WARNING)


def test_a_printed_message_shows_its_level_and_its_place():
    record = play_logger.makeRecord(
        "play", logging.WARNING, "game.py", 7, "check this", None, None
    )

    printed = _terminal_handlers(logging.WARNING)[0].format(record)

    assert "WARNING" in printed
    assert "check this" in printed
    assert "(game.py:7)" in printed
