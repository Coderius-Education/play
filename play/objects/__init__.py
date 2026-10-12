"""This module contains all the objects that can be used in the game window.
Each object is a subclass of Sprite, which is a subclass of pygame.sprite.Sprite.
The objects are: Box, Circle, Text, and Group.
Each object has a corresponding new_* function that can be used to create the object.
For example, play.new_box() creates a new Box object.
"""

from play.objects.box import Box
from play.objects.widgets.button import Button
from play.objects.widgets.checkbox import Checkbox
from play.objects.circle import Circle
from play.objects.widgets.dropdown import Dropdown
from play.objects.widgets.progress_bar import ProgressBar
from play.objects.widgets.radio_button import RadioButton, RadioGroup
from play.objects.widgets.slider import Slider
from play.objects.sprite import Sprite
from play.objects.text import Text
from play.objects.image import Image
from play.objects.sound import Sound
from play.objects.widgets.text_input import TextInput
from play.objects.widgets.tooltip import Tooltip
from play.objects.video.video import Video
