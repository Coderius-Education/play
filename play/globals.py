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


globals_list = Globals()
