"""This module contains all the objects that can be used in the game window.
Each object is a subclass of Sprite, which is a subclass of pygame.sprite.Sprite.
The objects are: Box, Circle, Text, and Group.
Each object has a corresponding new_* function that can be used to create the object.
For example, play.new_box() creates a new Box object.
"""

from .box import Box
from .button import Button
from .checkbox import Checkbox
from .circle import Circle
from .dropdown import Dropdown
from .progress_bar import ProgressBar
from .radio_button import RadioButton, RadioGroup
from .slider import Slider
from .sprite import Sprite
from .text import Text
from .image import Image
from .sound import Sound
from .text_input import TextInput
from .tooltip import Tooltip
