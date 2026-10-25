"""Run the real game loop, posting pygame events before chosen frames."""

import pygame

import play
from play.io.screen import screen


def play_frames(*frames, then=3):
    """Run the game, posting each item of *frames* (a list of events) before a frame of its own, then stop."""

    @play.when_program_starts
    async def driver():
        await play.animate()
        for events in frames:
            for event in events:
                pygame.event.post(event)
            await play.animate()
        for _ in range(then):
            await play.animate()
        play.stop_program()

    play.start_program()


def key_down(key):
    """A KEYDOWN event for a pygame key constant."""
    return pygame.event.Event(pygame.KEYDOWN, {"key": key})


def key_up(key):
    """A KEYUP event for a pygame key constant."""
    return pygame.event.Event(pygame.KEYUP, {"key": key})


def _screen_pos(x, y):
    """The window position of play's point (x, y)."""
    return int(screen.width / 2 + x), int(screen.height / 2 - y)


def mouse_move(x=0, y=0):
    """A MOUSEMOTION event to play's point (x, y)."""
    return pygame.event.Event(
        pygame.MOUSEMOTION,
        {"pos": _screen_pos(x, y), "rel": (0, 0), "buttons": (0, 0, 0)},
    )


def mouse_down(x=0, y=0, button=1):
    """A MOUSEBUTTONDOWN event at play's point (x, y)."""
    return pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"pos": _screen_pos(x, y), "button": button}
    )


def mouse_up(x=0, y=0, button=1):
    """A MOUSEBUTTONUP event at play's point (x, y)."""
    return pygame.event.Event(
        pygame.MOUSEBUTTONUP, {"pos": _screen_pos(x, y), "button": button}
    )


def button_down(button, instance_id=0):
    """A JOYBUTTONDOWN event from the controller with an SDL instance id."""
    return pygame.event.Event(
        pygame.JOYBUTTONDOWN, {"instance_id": instance_id, "button": button}
    )


def button_up(button, instance_id=0):
    """A JOYBUTTONUP event from the controller with an SDL instance id."""
    return pygame.event.Event(
        pygame.JOYBUTTONUP, {"instance_id": instance_id, "button": button}
    )


def axis_moved(axis, value, instance_id=0):
    """A JOYAXISMOTION event from the controller with an SDL instance id."""
    return pygame.event.Event(
        pygame.JOYAXISMOTION,
        {"instance_id": instance_id, "axis": axis, "value": value},
    )
