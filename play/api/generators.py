"""Generators for creating new objects."""

from ..db import Database
from ..objects import (
    Box as _Box,
    Button as _Button,
    Circle as _Circle,
    Text as _Text,
    Image as _Image,
    Sound as _Sound,
    TextInput as _TextInput,
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
    anchor: str = None,
    layer: int = 0,
) -> _Text:
    """Make a new text object.
    :param words: The text to display.
    :param x: The x-coordinate (or inward offset when anchor is set).
    :param y: The y-coordinate (or inward offset when anchor is set).
    :param font: The font to use.
    :param font_size: The size of the font.
    :param color: The color of the text.
    :param angle: The angle of the text.
    :param transparency: The transparency of the text.
    :param size: The size of the text.
    :param anchor: Pin to a screen edge/corner ("top-left", "top-right", etc.).
    :param layer: Render layer — higher layers draw on top (default 0).
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
        anchor=anchor,
        layer=layer,
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
    anchor: str = None,
    layer: int = 0,
) -> _Box:
    """Make a new box object.
    :param color: The color of the box.
    :param x: The x-coordinate (or inward offset when anchor is set).
    :param y: The y-coordinate (or inward offset when anchor is set).
    :param width: The width of the box.
    :param height: The height of the box.
    :param border_color: The color of the border of the box.
    :param border_width: The width of the border of the box.
    :param border_radius: The radius of the border (rounding).
    :param angle: The angle of the box.
    :param transparency: The transparency of the box.
    :param size: The size of the box.
    :param anchor: Pin to a screen edge/corner ("top-left", "top-right", etc.).
    :param layer: Render layer — higher layers draw on top (default 0).
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
        anchor=anchor,
        layer=layer,
    )


def new_button(
    text: str = "Button",
    x: int = 0,
    y: int = 0,
    width: int = 160,
    height: int = 50,
    color: str = "royalblue",
    hover_color: str = "steelblue",
    text_color: str = "white",
    font_size: int = 20,
    border_radius: int = 6,
    transparency: int = 100,
    size: int = 100,
    anchor: str = None,
    layer: int = 10,
) -> _Button:
    """Make a new button with a text label and hover highlight.

    :param text: The label to display on the button.
    :param x: The x-coordinate (or inward offset when anchor is set).
    :param y: The y-coordinate (or inward offset when anchor is set).
    :param width: Width of the button in pixels.
    :param height: Height of the button in pixels.
    :param color: Background colour when not hovered.
    :param hover_color: Background colour when the mouse is over the button.
    :param text_color: Colour of the label text.
    :param font_size: Size of the label font.
    :param border_radius: Corner rounding radius.
    :param transparency: Transparency (0–100).
    :param size: Scale percentage.
    :param anchor: Pin to a screen edge/corner ("top-left", "bottom-center", etc.).
    :param layer: Render layer — defaults to 10 so UI sits above layer-0 game sprites.
    :return: A new Button object.
    """
    return _Button(
        text=text,
        x=x,
        y=y,
        width=width,
        height=height,
        color=color,
        hover_color=hover_color,
        text_color=text_color,
        font_size=font_size,
        border_radius=border_radius,
        transparency=transparency,
        size=size,
        anchor=anchor,
        layer=layer,
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
    anchor: str = None,
    layer: int = 0,
) -> _Circle:
    """Make a new circle object.
    :param color: The color of the circle.
    :param x: The x-coordinate (or inward offset when anchor is set).
    :param y: The y-coordinate (or inward offset when anchor is set).
    :param radius: The radius of the circle.
    :param border_color: The color of the border of the circle.
    :param border_width: The width of the border of the circle.
    :param transparency: The transparency of the circle.
    :param size: The size of the circle.
    :param angle: The angle of the circle.
    :param anchor: Pin to a screen edge/corner ("top-left", "top-right", etc.).
    :param layer: Render layer — higher layers draw on top (default 0).
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
        anchor=anchor,
        layer=layer,
    )


def new_image(
    image: str = "/path/to/image",
    x: int = 0,
    y: int = 0,
    size: int = 100,
    angle: int = 0,
    transparency: int = 100,
    anchor: str = None,
    layer: int = 0,
) -> _Image:
    """Make a new image object.
    :param image: The image to display.
    :param x: The x-coordinate (or inward offset when anchor is set).
    :param y: The y-coordinate (or inward offset when anchor is set).
    :param size: The size of the image.
    :param angle: The angle of the image.
    :param transparency: The transparency of the image.
    :param anchor: Pin to a screen edge/corner ("top-left", "top-right", etc.).
    :param layer: Render layer — higher layers draw on top (default 0).
    :return: A new image object.
    """
    return _Image(
        image=image,
        x=x,
        y=y,
        size=size,
        angle=angle,
        transparency=transparency,
        anchor=anchor,
        layer=layer,
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


def new_text_input(
    placeholder: str = "",
    value: str = "",
    x: int = 0,
    y: int = 0,
    width: int = 200,
    height: int = 40,
    color: str = "white",
    active_color: str = "lightyellow",
    text_color: str = "black",
    placeholder_color: str = "gray",
    font_size: int = 20,
    border_color: str = "gray",
    border_width: int = 1,
    border_radius: int = 4,
    max_length: int = None,
    transparency: int = 100,
    size: int = 100,
    anchor: str = None,
    layer: int = 10,
) -> _TextInput:
    """Make a new text input field.

    :param placeholder: Hint text shown when the field is empty and unfocused.
    :param value: Initial text value.
    :param x: The x-coordinate (or inward offset when anchor is set).
    :param y: The y-coordinate (or inward offset when anchor is set).
    :param width: Width of the input in pixels.
    :param height: Height of the input in pixels.
    :param color: Background colour when not focused.
    :param active_color: Background colour when the field has keyboard focus.
    :param text_color: Colour of the typed text.
    :param placeholder_color: Colour of the placeholder text.
    :param font_size: Size of the text font.
    :param border_color: Colour of the border.
    :param border_width: Width of the border in pixels.
    :param border_radius: Corner rounding radius.
    :param max_length: Maximum number of characters allowed (None = unlimited).
    :param transparency: Transparency (0–100).
    :param size: Scale percentage.
    :param anchor: Pin to a screen edge/corner ("top-left", "bottom-center", etc.).
    :param layer: Render layer — defaults to 10 so UI sits above layer-0 game sprites.
    :return: A new TextInput object.
    """
    return _TextInput(
        placeholder=placeholder,
        value=value,
        x=x,
        y=y,
        width=width,
        height=height,
        color=color,
        active_color=active_color,
        text_color=text_color,
        placeholder_color=placeholder_color,
        font_size=font_size,
        border_color=border_color,
        border_width=border_width,
        border_radius=border_radius,
        max_length=max_length,
        transparency=transparency,
        size=size,
        anchor=anchor,
        layer=layer,
    )


def new_database(
    db_filename: str = "database.json",
) -> Database:
    """
    Create a new database with the specified name and table.
    :param db_filename: The name of the database file.
    """
    return Database(db_filename=db_filename)
