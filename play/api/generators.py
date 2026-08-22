"""Generators for creating new objects."""

from ..db import Database
from ..objects import (
    Box as _Box,
    Circle as _Circle,
    Text as _Text,
    Image as _Image,
    Sound as _Sound,
    Video as _Video,
)


def new_text(
    words: str = "",
    x: int = 0,
    y: int = 0,
    font: str = "default",
    font_size: int = 50,
    color: str = "black",
    angle: int = 0,
    transparency: int = 100,
    size: int = 100,
) -> _Text:
    """Make a new text object.
    :param words: The text to display.
    :param x: The x-coordinate of the text.
    :param y: The y-coordinate of the text.
    :param font: The font to use.
    :param font_size: The size of the font.
    :param color: The color of the text.
    :param angle: The angle of the text.
    :param transparency: The transparency of the text.
    :param size: The size of the text.
    :return: A new text object.
    """
    if not isinstance(words, str):
        raise TypeError("words for a text object must be a string")

    return _Text(
        words=words,
        x=x,
        y=y,
        font=font,
        font_size=font_size,
        color=color,
        angle=angle,
        transparency=transparency,
        size=size,
    )


def new_box(
    color: str = "black",
    x: int = 0,
    y: int = 0,
    width: int = 100,
    height: int = 200,
    border_color: str = "light blue",
    border_width: int = 0,
    border_radius: int = 0,
    angle: int = 0,
    transparency: int = 100,
    size: int = 100,
) -> _Box:
    """Make a new box object.
    :param color: The color of the box.
    :param x: The x-coordinate of the box.
    :param y: The y-coordinate of the box.
    :param width: The width of the box.
    :param height: The height of the box.
    :param border_color: The color of the border of the box.
    :param border_width: The width of the border of the box.
    :param border_radius: The radius of the border (rounding).
    :param angle: The angle of the box.
    :param transparency: The transparency of the box.
    :param size: The size of the box.
    :return: A new box object.
    """
    return _Box(
        color=color,
        x=x,
        y=y,
        width=width,
        height=height,
        border_color=border_color,
        border_width=border_width,
        border_radius=border_radius,
        angle=angle,
        transparency=transparency,
        size=size,
    )


def new_circle(
    color: str = "black",
    x: int = 0,
    y: int = 0,
    radius: int = 100,
    border_color: str = "light blue",
    border_width: int = 0,
    transparency: int = 100,
    size: int = 100,
    angle: int = 0,
) -> _Circle:
    """Make a new circle object.
    :param color: The color of the circle.
    :param x: The x-coordinate of the circle.
    :param y: The y-coordinate of the circle.
    :param radius: The radius of the circle.
    :param border_color: The color of the border of the circle.
    :param border_width: The width of the border of the circle.
    :param transparency: The transparency of the circle.
    :param size: The size of the circle.
    :param angle: The angle of the circle.
    :return: A new circle object.
    """
    return _Circle(
        color=color,
        x=x,
        y=y,
        radius=radius,
        border_color=border_color,
        border_width=border_width,
        transparency=transparency,
        size=size,
        angle=angle,
    )


def new_image(
    image: str = "/path/to/image",
    x: int = 0,
    y: int = 0,
    size: int = 100,
    angle: int = 0,
    transparency: int = 100,
) -> _Image:
    """Make a new image object.
    :param image: The image to display.
    :param x: The x-coordinate of the image.
    :param y: The y-coordinate of the image.
    :param size: The size of the image.
    :param angle: The angle of the image.
    :param transparency: The transparency of the image.
    :return: A new image object.
    """
    return _Image(
        image=image, x=x, y=y, size=size, angle=angle, transparency=transparency
    )


def new_sound(
    file_name: str = "file.mp3",
    volume: float = 1.0,
    loops: int = 0,
) -> _Sound:
    """
    Initialize the Sound object.
    :param file_name: The sound file to load (a file path if not in the same directory as the .py).
    :param volume: The initial volume (0.0 to 1.0).
    :param loops: Number of times to loop the sound (-1 for infinite, 0 for no loop).
    """

    return _Sound(file_name=file_name, volume=volume, loops=loops)


def new_database(
    db_filename: str = "database.json",
) -> Database:
    """
    Create a new database with the specified name and table.
    :param db_filename: The name of the database file.
    """
    return Database(db_filename=db_filename)


def new_video(  # pylint: disable=too-many-locals
    file_name: str = "video.mp4",
    x: int = 0,
    y: int = 0,
    width: int = None,
    height: int = None,
    size: int = 100,
    angle: int = 0,
    transparency: int = 100,
    volume: float = 1.0,
    speed: float = 1.0,
    loop: bool = False,
    autoplay: bool = False,
    controls: bool = True,
    muted: bool = False,
) -> _Video:
    """Make a new video that plays on screen.

    :param file_name: The video file to play, for example 'clip.mp4'.
    :param x: The x-coordinate of the video.
    :param y: The y-coordinate of the video.
    :param width: How wide the video is on screen. Defaults to the video's
        own width. Giving only a width or only a height keeps the shape.
    :param height: How tall the video is on screen.
    :param size: The size of the video, as a percentage.
    :param angle: The angle of the video.
    :param transparency: The transparency of the video (0 to 100).
    :param volume: How loud the video's sound is (0.0 to 1.0).
    :param speed: How fast the video plays. This also changes the pitch.
    :param loop: Whether the video starts again when it ends.
    :param autoplay: Whether the video starts playing straight away.
    :param controls: Whether to show the built-in controls when the mouse is
        over the video.
    :param muted: Whether the video starts with its sound turned off.
    :return: A new video object.
    """
    return _Video(
        file_name=file_name,
        x=x,
        y=y,
        width=width,
        height=height,
        size=size,
        angle=angle,
        transparency=transparency,
        volume=volume,
        speed=speed,
        loop=loop,
        autoplay=autoplay,
        controls=controls,
        muted=muted,
    )
