"""Helpers for checking that a cloned widget copies everything it was given."""

import os

import pygame

from play.io.screen import screen
from tests.conftest import image_bytes

BUNDLED_FONT = os.path.join(
    os.path.dirname(pygame.__file__), pygame.font.get_default_font()
)


def appearance(sprite):
    """What *sprite* shows after a frame: its picture, opacity, layer and place."""
    sprite.update()
    return (
        image_bytes(sprite),
        sprite.image.get_alpha(),
        sprite.layer,
        tuple(sprite.rect),
    )


def middle_of(sprite):
    """The play coordinates of the middle of *sprite* as drawn."""
    return (
        sprite.rect.centerx - screen.width / 2,
        screen.height / 2 - sprite.rect.centery,
    )
