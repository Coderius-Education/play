"""Global variables for the game"""

from dataclasses import dataclass, field

import pygame


@dataclass
class Globals:
    all_sprites: list = field(default_factory=list)
    sprites_group: pygame.sprite.Group = field(default_factory=pygame.sprite.Group)

    walls: list = field(default_factory=list)

    backdrop_type: str = "color"  # color or image
    backdrop: tuple = (255, 255, 255)

    frame_rate: int = 60
    width: int = 800
    height: int = 600

    gravity: object = None
    num_sim_steps: int = 10

    display: object = None  # This will be set in the screen module
    controllers: list = field(default_factory=list)
    on_first_sprite: object = None

    def reset(self):
        """Reset mutable game state to defaults.

        Note: ``gravity`` and ``display`` are intentionally NOT reset here.
        ``gravity`` requires re-initialisation with a pymunk Space object and
        is handled separately in the test conftest.  ``display`` needs an
        active pygame Surface and is managed by the screen module.
        """
        self.all_sprites.clear()
        self.sprites_group.empty()
        self.walls.clear()
        self.controllers.clear()
        self.backdrop_type = "color"
        self.backdrop = (255, 255, 255)
        self.frame_rate = 60
        self.width = 800
        self.height = 600
        self.num_sim_steps = 10


globals_list = Globals()
