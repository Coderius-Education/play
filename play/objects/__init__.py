"""This module contains all the objects that can be used in the game window.
Each object is a subclass of Sprite, which is a subclass of pygame.sprite.Sprite.
The objects are: Box, Circle, Text, and Group.
Each object has a corresponding new_* function that can be used to create the object.
For example, play.new_box() creates a new Box object.
"""

from .box import Box
from play.objects.ui.button.button import Button
from play.objects.ui.button.checkbox import Checkbox
from .circle import Circle
from play.objects.ui.button.dropdown import Dropdown
from play.objects.ui.progress_bar import ProgressBar
from play.objects.ui.button.radio_button import RadioButton, RadioGroup
from play.objects.ui.button.slider import Slider
from .sprite import Sprite
from play.objects.ui.text.text import Text
from play.objects.ui.image import Image
from .sound import Sound
from play.objects.ui.text.text_input import TextInput
from play.objects.ui.text.tooltip import Tooltip
from play.objects.video.video import Video
