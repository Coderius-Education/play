"""Generators for creating new objects."""

from typing import Optional

from ..db import Database
from ..objects import (
    Box as _Box,
    Button as _Button,
    Checkbox as _Checkbox,
    Circle as _Circle,
    Dropdown as _Dropdown,
    ProgressBar as _ProgressBar,
    RadioButton as _RadioButton,
    RadioGroup as _RadioGroup,
    Slider as _Slider,
    Sprite as _Sprite,
    Text as _Text,
    Image as _Image,
    Sound as _Sound,
    TextInput as _TextInput,
    Tooltip as _Tooltip,
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
    anchor: Optional[str] = None,
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
    anchor: Optional[str] = None,
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
    click_color: Optional[str] = None,
    text_color: str = "white",
    font_size: int = 20,
    font: Optional[str] = None,
    border_radius: int = 6,
    transparency: int = 100,
    size: int = 100,
    anchor: Optional[str] = None,
    layer: int = 10,
    disabled: bool = False,
    disabled_color: str = "gray",
    disabled_text_color: Optional[str] = None,
) -> _Button:
    """Make a new button with a text label and hover/press/disabled states.

    :param text: The label to display on the button.
    :param x: The x-coordinate (or inward offset when anchor is set).
    :param y: The y-coordinate (or inward offset when anchor is set).
    :param width: Width of the button in pixels.
    :param height: Height of the button in pixels.
    :param color: Background colour when not hovered.
    :param hover_color: Background colour when the mouse is over the button.
    :param click_color: Background colour while the mouse button is held down (None = auto-darken).
    :param text_color: Colour of the label text.
    :param font_size: Size of the label font.
    :param font: Path to a .ttf font file, or None for the system default.
    :param border_radius: Corner rounding radius.
    :param transparency: Transparency (0–100).
    :param size: Scale percentage.
    :param anchor: Pin to a screen edge/corner ("top-left", "bottom-center", etc.).
    :param layer: Render layer — defaults to 10 so UI sits above layer-0 game sprites.
    :param disabled: Start the button in a disabled (non-interactive, greyed-out) state.
    :param disabled_color: Background colour when disabled.
    :param disabled_text_color: Label colour when disabled (None = same as text_color).
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
        click_color=click_color,
        text_color=text_color,
        font_size=font_size,
        font=font,
        border_radius=border_radius,
        transparency=transparency,
        size=size,
        anchor=anchor,
        layer=layer,
        disabled=disabled,
        disabled_color=disabled_color,
        disabled_text_color=disabled_text_color,
    )


def new_checkbox(
    label: str = "",
    checked: bool = False,
    x: int = 0,
    y: int = 0,
    size_px: int = 24,
    color: str = "white",
    check_color: str = "royalblue",
    border_color: str = "darkgray",
    hover_border_color: str = "steelblue",
    label_color: str = "black",
    font_size: int = 18,
    font: Optional[str] = None,
    border_radius: int = 4,
    transparency: int = 100,
    anchor: Optional[str] = None,
    layer: int = 10,
    disabled: bool = False,
) -> _Checkbox:
    """Make a new checkbox widget.

    :param label: Optional text label shown to the right of the checkbox.
    :param checked: Initial checked state.
    :param x: The x-coordinate (or inward offset when anchor is set).
    :param y: The y-coordinate (or inward offset when anchor is set).
    :param size_px: Width and height of the checkbox square in pixels.
    :param color: Background colour.
    :param check_color: Colour of the checkmark fill.
    :param border_color: Border colour when not hovered.
    :param hover_border_color: Border colour when hovered.
    :param label_color: Colour of the label text.
    :param font_size: Font size for the label.
    :param font: Path to a .ttf font file, or None for the system default.
    :param border_radius: Corner rounding radius.
    :param transparency: Transparency (0–100).
    :param anchor: Pin to a screen edge/corner.
    :param layer: Render layer.
    :param disabled: Whether the checkbox is non-interactive.
    :return: A new Checkbox object.
    """
    return _Checkbox(
        label=label,
        checked=checked,
        x=x,
        y=y,
        size_px=size_px,
        color=color,
        check_color=check_color,
        border_color=border_color,
        hover_border_color=hover_border_color,
        label_color=label_color,
        font_size=font_size,
        font=font,
        border_radius=border_radius,
        transparency=transparency,
        anchor=anchor,
        layer=layer,
        disabled=disabled,
    )


def new_slider(
    min_value: float = 0,
    max_value: float = 100,
    value: float = 50,
    x: int = 0,
    y: int = 0,
    width: int = 200,
    height: int = 20,
    track_color: str = "lightgray",
    fill_color: str = "royalblue",
    thumb_color: str = "royalblue",
    thumb_radius: int = 12,
    border_radius: int = 10,
    transparency: int = 100,
    anchor: Optional[str] = None,
    layer: int = 10,
    disabled: bool = False,
    show_value: bool = False,
    font_size: int = 16,
    font: Optional[str] = None,
    value_color: str = "black",
    step: Optional[float] = None,
) -> _Slider:
    """Make a new slider (range input) widget.

    :param min_value: Minimum selectable value.
    :param max_value: Maximum selectable value.
    :param value: Initial value.
    :param x: The x-coordinate (or inward offset when anchor is set).
    :param y: The y-coordinate (or inward offset when anchor is set).
    :param width: Width of the slider track in pixels.
    :param height: Height of the slider track in pixels.
    :param track_color: Colour of the unfilled track portion.
    :param fill_color: Colour of the filled (left) track portion.
    :param thumb_color: Colour of the draggable thumb circle.
    :param thumb_radius: Radius of the thumb circle.
    :param border_radius: Corner rounding of the track.
    :param transparency: Transparency (0–100).
    :param anchor: Pin to a screen edge/corner.
    :param layer: Render layer.
    :param disabled: Whether the slider is non-interactive.
    :param show_value: Whether to render the current value as text to the right.
    :param font_size: Font size for the value label.
    :param font: Path to a .ttf font file, or None for the system default.
    :param value_color: Colour of the value label text.
    :param step: Snap interval (None = continuous).
    :return: A new Slider object.
    """
    return _Slider(
        min_value=min_value,
        max_value=max_value,
        value=value,
        x=x,
        y=y,
        width=width,
        height=height,
        track_color=track_color,
        fill_color=fill_color,
        thumb_color=thumb_color,
        thumb_radius=thumb_radius,
        border_radius=border_radius,
        transparency=transparency,
        anchor=anchor,
        layer=layer,
        disabled=disabled,
        show_value=show_value,
        font_size=font_size,
        font=font,
        value_color=value_color,
        step=step,
    )


def new_progress_bar(
    min_value: float = 0,
    max_value: float = 100,
    value: float = 50,
    x: int = 0,
    y: int = 0,
    width: int = 200,
    height: int = 24,
    bar_color: str = "royalblue",
    background_color: str = "lightgray",
    border_color: str = "gray",
    border_width: int = 1,
    border_radius: int = 4,
    transparency: int = 100,
    anchor: Optional[str] = None,
    layer: int = 0,
    show_label: bool = False,
    label_color: str = "white",
    font_size: int = 14,
    font: Optional[str] = None,
) -> _ProgressBar:
    """Make a new progress / health bar widget.

    :param min_value: Minimum value (left edge).
    :param max_value: Maximum value (right edge / full).
    :param value: Initial value.
    :param x: The x-coordinate (or inward offset when anchor is set).
    :param y: The y-coordinate (or inward offset when anchor is set).
    :param width: Width of the bar in pixels.
    :param height: Height of the bar in pixels.
    :param bar_color: Colour of the filled portion.
    :param background_color: Colour of the unfilled portion.
    :param border_color: Border colour.
    :param border_width: Border width in pixels.
    :param border_radius: Corner rounding radius.
    :param transparency: Transparency (0–100).
    :param anchor: Pin to a screen edge/corner.
    :param layer: Render layer.
    :param show_label: Whether to render a percentage label centred on the bar.
    :param label_color: Colour of the percentage label.
    :param font_size: Font size for the label.
    :param font: Path to a .ttf font file, or None for the system default.
    :return: A new ProgressBar object.
    """
    return _ProgressBar(
        min_value=min_value,
        max_value=max_value,
        value=value,
        x=x,
        y=y,
        width=width,
        height=height,
        bar_color=bar_color,
        background_color=background_color,
        border_color=border_color,
        border_width=border_width,
        border_radius=border_radius,
        transparency=transparency,
        anchor=anchor,
        layer=layer,
        show_label=show_label,
        label_color=label_color,
        font_size=font_size,
        font=font,
    )


def new_dropdown(
    options: Optional[list] = None,
    selected_index: int = 0,
    x: int = 0,
    y: int = 0,
    width: int = 160,
    height: int = 40,
    color: str = "white",
    hover_color: str = "lightyellow",
    option_hover_color: str = "cornflowerblue",
    text_color: str = "black",
    border_color: str = "gray",
    border_width: int = 1,
    border_radius: int = 4,
    font_size: int = 18,
    font: Optional[str] = None,
    transparency: int = 100,
    anchor: Optional[str] = None,
    layer: int = 20,
    disabled: bool = False,
    placeholder: str = "Select…",
) -> _Dropdown:
    """Make a new dropdown / select widget.

    :param options: List of option labels (strings or any str-able values).
    :param selected_index: Initially selected option index.
    :param x: The x-coordinate (or inward offset when anchor is set).
    :param y: The y-coordinate (or inward offset when anchor is set).
    :param width: Width in pixels.
    :param height: Height of the closed button row in pixels.
    :param color: Background colour of the button and options.
    :param hover_color: Button background colour on hover (closed state).
    :param option_hover_color: Option row background colour on hover (open state).
    :param text_color: Text colour for labels and options.
    :param border_color: Border colour.
    :param border_width: Border width in pixels.
    :param border_radius: Corner rounding radius (applied to button row).
    :param font_size: Font size.
    :param font: Path to a .ttf font file, or None for the system default.
    :param transparency: Transparency (0–100).
    :param anchor: Pin to a screen edge/corner.
    :param layer: Render layer — defaults to 20 so the open menu sits above other UI.
    :param disabled: Whether the dropdown is non-interactive.
    :param placeholder: Text shown when no option is selected.
    :return: A new Dropdown object.
    """
    return _Dropdown(
        options=options,
        selected_index=selected_index,
        x=x,
        y=y,
        width=width,
        height=height,
        color=color,
        hover_color=hover_color,
        option_hover_color=option_hover_color,
        text_color=text_color,
        border_color=border_color,
        border_width=border_width,
        border_radius=border_radius,
        font_size=font_size,
        font=font,
        transparency=transparency,
        anchor=anchor,
        layer=layer,
        disabled=disabled,
        placeholder=placeholder,
    )


def new_radio_group() -> _RadioGroup:
    """Create a new RadioGroup that manages mutually exclusive RadioButtons.

    :return: A new RadioGroup object.
    """
    return _RadioGroup()


def new_radio_button(
    label: str = "",
    value: str = "",
    group: Optional[_RadioGroup] = None,
    x: int = 0,
    y: int = 0,
    size_px: int = 22,
    color: str = "white",
    selected_color: str = "royalblue",
    border_color: str = "darkgray",
    hover_border_color: str = "steelblue",
    label_color: str = "black",
    font_size: int = 18,
    font: Optional[str] = None,
    transparency: int = 100,
    anchor: Optional[str] = None,
    layer: int = 10,
    disabled: bool = False,
    selected: bool = False,
) -> _RadioButton:
    """Make a new radio button widget.

    Pair with a RadioGroup so that selecting one button deselects the others::

        group = play.new_radio_group()
        r1 = play.new_radio_button("Easy",   value="easy",   group=group, x=-100, y=0)
        r2 = play.new_radio_button("Medium", value="medium", group=group, x=0,    y=0, selected=True)
        r3 = play.new_radio_button("Hard",   value="hard",   group=group, x=100,  y=0)

        @group.when_changed
        def on_changed(value):
            print("Selected:", value)

    :param label: Text label shown next to the radio button circle.
    :param value: Logical value associated with this button.
    :param group: The RadioGroup this button belongs to (or None for standalone).
    :param x: The x-coordinate (or inward offset when anchor is set).
    :param y: The y-coordinate (or inward offset when anchor is set).
    :param size_px: Diameter of the radio circle in pixels.
    :param color: Background colour of the circle.
    :param selected_color: Colour of the inner dot when selected.
    :param border_color: Circle border colour when not hovered.
    :param hover_border_color: Circle border colour on hover.
    :param label_color: Colour of the label text.
    :param font_size: Font size for the label.
    :param font: Path to a .ttf font file, or None for the system default.
    :param transparency: Transparency (0–100).
    :param anchor: Pin to a screen edge/corner.
    :param layer: Render layer.
    :param disabled: Whether the button is non-interactive.
    :param selected: Whether this button starts selected.
    :return: A new RadioButton object.
    """
    return _RadioButton(
        label=label,
        value=value,
        group=group,
        x=x,
        y=y,
        size_px=size_px,
        color=color,
        selected_color=selected_color,
        border_color=border_color,
        hover_border_color=hover_border_color,
        label_color=label_color,
        font_size=font_size,
        font=font,
        transparency=transparency,
        anchor=anchor,
        layer=layer,
        disabled=disabled,
        selected=selected,
    )


def new_tooltip(
    text: str = "",
    target: Optional[_Sprite] = None,
    offset_x: int = 12,
    offset_y: int = -12,
    color: str = "lightyellow",
    text_color: str = "black",
    border_color: str = "gray",
    font_size: int = 15,
    font: Optional[str] = None,
    padding: int = 6,
    border_radius: int = 4,
    transparency: int = 100,
    layer: int = 100,
) -> _Tooltip:
    """Make a tooltip that appears when the mouse hovers over *target*.

    :param text: Tooltip text (may include newlines).
    :param target: The sprite to attach the tooltip to.
    :param offset_x: Horizontal offset of the tooltip from the mouse cursor.
    :param offset_y: Vertical offset of the tooltip from the mouse cursor.
    :param color: Background colour of the tooltip bubble.
    :param text_color: Text colour.
    :param border_color: Border colour.
    :param font_size: Font size.
    :param font: Path to a .ttf font file, or None for the system default.
    :param padding: Inner padding around the text.
    :param border_radius: Corner rounding radius.
    :param transparency: Transparency (0–100).
    :param layer: Render layer — defaults to 100 so tooltips sit above everything.
    :return: A new Tooltip object.
    """
    return _Tooltip(
        text=text,
        target=target,
        offset_x=offset_x,
        offset_y=offset_y,
        color=color,
        text_color=text_color,
        border_color=border_color,
        font_size=font_size,
        font=font,
        padding=padding,
        border_radius=border_radius,
        transparency=transparency,
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
    anchor: Optional[str] = None,
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
    anchor: Optional[str] = None,
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
    font: Optional[str] = None,
    border_color: str = "gray",
    border_width: int = 1,
    border_radius: int = 4,
    max_length: Optional[int] = None,
    transparency: int = 100,
    size: int = 100,
    anchor: Optional[str] = None,
    layer: int = 10,
    disabled: bool = False,
    readonly: bool = False,
    password_mode: bool = False,
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
    :param font: Path to a .ttf font file, or None for the system default.
    :param border_color: Colour of the border.
    :param border_width: Width of the border in pixels.
    :param border_radius: Corner rounding radius.
    :param max_length: Maximum number of characters allowed (None = unlimited).
    :param transparency: Transparency (0–100).
    :param size: Scale percentage.
    :param anchor: Pin to a screen edge/corner ("top-left", "bottom-center", etc.).
    :param layer: Render layer — defaults to 10 so UI sits above layer-0 game sprites.
    :param disabled: Whether the field is non-interactive (cannot be focused or edited).
    :param readonly: Whether the field can be focused but not edited.
    :param password_mode: Whether to mask characters with bullet characters.
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
        font=font,
        border_color=border_color,
        border_width=border_width,
        border_radius=border_radius,
        max_length=max_length,
        transparency=transparency,
        size=size,
        anchor=anchor,
        layer=layer,
        disabled=disabled,
        readonly=readonly,
        password_mode=password_mode,
    )


def new_database(
    db_filename: str = "database.json",
) -> Database:
    """
    Create a new database with the specified name and table.
    :param db_filename: The name of the database file.
    """
    return Database(db_filename=db_filename)
