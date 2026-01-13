# pylint: skip-file
"""The library to make pygame easier to use."""
import pygame

pygame.init()
from .api import *
from .io.controllers import controllers
from .io.mouse import mouse
from .io.screen import screen
