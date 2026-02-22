"""Tests for sprite event decorators like when_clicked."""

import pytest


def test_sprite_when_clicked_method():
    """Test sprite.when_clicked() method."""
    import play

    sprite = play.new_box(x=0, y=0, width=50, height=50)
    callback_called = []

    def on_click(sprite_arg):
        callback_called.append(sprite_arg)

    sprite.when_clicked(on_click, call_with_sprite=True)

    # Verify callback was registered
    from play.callback import callback_manager, CallbackType

    callbacks = list(
        callback_manager.get_callback([CallbackType.WHEN_CLICKED_SPRITE], id(sprite))
    )
    assert len(callbacks) > 0


def test_when_sprite_clicked_decorator():
    """Test play.when_sprite_clicked() decorator."""
    import play

    sprite = play.new_box(x=0, y=0, width=50, height=50)
    callback_called = []

    @play.when_sprite_clicked(sprite)
    def on_click(sprite_arg):
        callback_called.append(sprite_arg)

    # Verify callback was registered
    from play.callback import callback_manager, CallbackType

    callbacks = list(
        callback_manager.get_callback([CallbackType.WHEN_CLICKED_SPRITE], id(sprite))
    )
    assert len(callbacks) > 0


def test_when_sprite_clicked_multiple_sprites():
    """Test when_sprite_clicked with multiple sprites."""
    import play

    sprite1 = play.new_box(x=0, y=0, width=50, height=50)
    sprite2 = play.new_circle(x=100, y=100, radius=25)
    callback_called = []

    @play.when_sprite_clicked(sprite1, sprite2)
    def on_click(sprite_arg):
        callback_called.append(sprite_arg)

    # Verify callbacks were registered for both sprites
    from play.callback import callback_manager, CallbackType

    callbacks1 = list(
        callback_manager.get_callback([CallbackType.WHEN_CLICKED_SPRITE], id(sprite1))
    )
    callbacks2 = list(
        callback_manager.get_callback([CallbackType.WHEN_CLICKED_SPRITE], id(sprite2))
    )

    assert len(callbacks1) > 0
    assert len(callbacks2) > 0


def test_sprite_is_clicked_property():
    """Test sprite.is_clicked property."""
    import play

    sprite = play.new_box(x=0, y=0, width=50, height=50)

    # Initially not clicked
    assert sprite.is_clicked == False


def test_sprite_when_touching_decorator():
    """Test sprite.when_touching() decorator."""
    import play

    sprite1 = play.new_box(x=0, y=0, width=50, height=50)
    sprite2 = play.new_circle(x=0, y=0, radius=25)
    callback_called = []

    @sprite1.when_touching(sprite2)
    def on_touch():
        callback_called.append(True)

    # Verify callback was registered
    from play.callback import callback_manager, CallbackType

    callbacks = list(
        callback_manager.get_callback([CallbackType.WHEN_TOUCHING], id(sprite1))
    )
    assert len(callbacks) > 0


def test_sprite_when_clicked_call_with_sprite_true():
    """Test that when_clicked passes sprite as argument when call_with_sprite=True."""
    import play

    sprite = play.new_box(x=0, y=0)

    def callback_with_sprite(s):
        pass

    # Test with call_with_sprite=True (default)
    wrapper = sprite.when_clicked(callback_with_sprite, call_with_sprite=True)

    # Verify the wrapper was created
    assert callable(wrapper)


def test_sprite_when_clicked_call_with_sprite_false():
    """Test that when_clicked doesn't pass sprite when call_with_sprite=False."""
    import play

    sprite = play.new_box(x=0, y=0)

    def callback_without_sprite():
        pass

    # Test with call_with_sprite=False
    wrapper = sprite.when_clicked(callback_without_sprite, call_with_sprite=False)

    # Verify the wrapper was created
    assert callable(wrapper)


def test_sprite_when_click_released_method():
    """Test sprite.when_click_released() method."""
    import play

    sprite = play.new_box(x=0, y=0, width=50, height=50)
    callback_called = []

    def on_release(sprite_arg):
        callback_called.append(sprite_arg)

    sprite.when_click_released(on_release, call_with_sprite=True)

    # Verify callback was registered
    from play.callback import callback_manager, CallbackType

    callbacks = list(
        callback_manager.get_callback(
            [CallbackType.WHEN_CLICK_RELEASED_SPRITE], id(sprite)
        )
    )
    assert len(callbacks) > 0


def test_when_sprite_click_released_decorator():
    """Test play.when_sprite_click_released() decorator."""
    import play

    sprite = play.new_box(x=0, y=0, width=50, height=50)
    callback_called = []

    @play.when_sprite_click_released(sprite)
    def on_release(sprite_arg):
        callback_called.append(sprite_arg)

    # Verify callback was registered
    from play.callback import callback_manager, CallbackType

    callbacks = list(
        callback_manager.get_callback(
            [CallbackType.WHEN_CLICK_RELEASED_SPRITE], id(sprite)
        )
    )
    assert len(callbacks) > 0


def test_when_sprite_click_released_multiple_sprites():
    """Test when_sprite_click_released with multiple sprites."""
    import play

    sprite1 = play.new_box(x=0, y=0, width=50, height=50)
    sprite2 = play.new_circle(x=100, y=100, radius=25)
    callback_called = []

    @play.when_sprite_click_released(sprite1, sprite2)
    def on_release(sprite_arg):
        callback_called.append(sprite_arg)

    # Verify callbacks were registered for both sprites
    from play.callback import callback_manager, CallbackType

    callbacks1 = list(
        callback_manager.get_callback(
            [CallbackType.WHEN_CLICK_RELEASED_SPRITE], id(sprite1)
        )
    )
    callbacks2 = list(
        callback_manager.get_callback(
            [CallbackType.WHEN_CLICK_RELEASED_SPRITE], id(sprite2)
        )
    )

    assert len(callbacks1) > 0
    assert len(callbacks2) > 0


def test_sprite_when_click_released_call_with_sprite_false():
    """Test that when_click_released doesn't pass sprite when call_with_sprite=False."""
    import play

    sprite = play.new_box(x=0, y=0)

    def callback_without_sprite():
        pass

    # Test with call_with_sprite=False
    wrapper = sprite.when_click_released(
        callback_without_sprite, call_with_sprite=False
    )

    # Verify the wrapper was created
    assert callable(wrapper)


def _post_mouse_motion(screen_x, screen_y):
    """Post a MOUSEMOTION event to position the mouse."""
    import pygame

    motion = pygame.event.Event(
        pygame.MOUSEMOTION,
        {"pos": (screen_x, screen_y), "rel": (0, 0), "buttons": (0, 0, 0)},
    )
    pygame.event.post(motion)


def _post_mouse_down(screen_x, screen_y):
    """Post a MOUSEBUTTONDOWN event."""
    import pygame

    click = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"pos": (screen_x, screen_y), "button": 1}
    )
    pygame.event.post(click)


def _post_mouse_up(screen_x, screen_y):
    """Post a MOUSEBUTTONUP event."""
    import pygame

    release = pygame.event.Event(
        pygame.MOUSEBUTTONUP, {"pos": (screen_x, screen_y), "button": 1}
    )
    pygame.event.post(release)


def test_sprite_when_click_released_fires_on_release():
    """Test that when_click_released callback fires when click is released on sprite."""
    import play
    from play.io.screen import screen

    num_frames = [0]
    released = [False]

    box = play.new_box(x=0, y=0, width=100, height=100, color="blue")

    @box.when_click_released
    def on_release():
        released[0] = True

    @play.repeat_forever
    def check():
        num_frames[0] += 1
        cx = int(screen.width / 2)
        cy = int(screen.height / 2)

        if num_frames[0] == 5:
            _post_mouse_motion(cx, cy)
        if num_frames[0] == 6:
            _post_mouse_down(cx, cy)
        if num_frames[0] == 8:
            _post_mouse_up(cx, cy)
        if num_frames[0] == 15:
            play.stop_program()

    play.start_program()

    assert released[0], "when_click_released callback should have been triggered"


def test_sprite_when_click_released_not_fired_without_release():
    """Test that when_click_released does NOT fire if mouse is only pressed."""
    import play
    from play.io.screen import screen

    num_frames = [0]
    released = [False]

    box = play.new_box(x=0, y=0, width=100, height=100, color="green")

    @box.when_click_released
    def on_release():
        released[0] = True

    @play.repeat_forever
    def check():
        num_frames[0] += 1
        cx = int(screen.width / 2)
        cy = int(screen.height / 2)

        if num_frames[0] == 5:
            _post_mouse_motion(cx, cy)
        if num_frames[0] == 6:
            _post_mouse_down(cx, cy)
        # No mouse up
        if num_frames[0] == 15:
            play.stop_program()

    play.start_program()

    assert not released[
        0
    ], "when_click_released should NOT fire without a mouse release"


def test_sprite_when_click_released_not_fired_outside_sprite():
    """Test that when_click_released does NOT fire if mouse is released outside the sprite."""
    import play
    from play.io.screen import screen

    num_frames = [0]
    released = [False]

    box = play.new_box(x=0, y=0, width=50, height=50, color="red")

    @box.when_click_released
    def on_release():
        released[0] = True

    @play.repeat_forever
    def check():
        num_frames[0] += 1
        cx = int(screen.width / 2)
        cy = int(screen.height / 2)

        if num_frames[0] == 5:
            _post_mouse_motion(cx, cy)
        if num_frames[0] == 6:
            _post_mouse_down(cx, cy)
        # Move mouse far away from box, then release
        if num_frames[0] == 7:
            _post_mouse_motion(0, 0)
        if num_frames[0] == 8:
            _post_mouse_up(0, 0)
        if num_frames[0] == 15:
            play.stop_program()

    play.start_program()

    assert not released[
        0
    ], "when_click_released should NOT fire when released outside sprite"


def test_sprite_when_click_released_not_fired_if_clicked_outside():
    """Test that when_click_released does NOT fire if click started outside sprite."""
    import play
    from play.io.screen import screen

    num_frames = [0]
    released = [False]

    box = play.new_box(x=0, y=0, width=50, height=50, color="purple")

    @box.when_click_released
    def on_release():
        released[0] = True

    @play.repeat_forever
    def check():
        num_frames[0] += 1
        cx = int(screen.width / 2)
        cy = int(screen.height / 2)

        # Click outside the sprite (at corner)
        if num_frames[0] == 5:
            _post_mouse_motion(0, 0)
        if num_frames[0] == 6:
            _post_mouse_down(0, 0)
        # Move mouse over the sprite
        if num_frames[0] == 7:
            _post_mouse_motion(cx, cy)
        # Release on the sprite
        if num_frames[0] == 8:
            _post_mouse_up(cx, cy)
        if num_frames[0] == 15:
            play.stop_program()

    play.start_program()

    assert not released[
        0
    ], "when_click_released should NOT fire if click started outside sprite"
