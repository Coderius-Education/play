"""Whole games that mix physics sprites with UI widgets.

Both real bugs found in this branch lived at exactly this seam: collision
callbacks keyed on a shared slot, and a disabled widget swallowing a click that
belonged to what was underneath it. Widgets are tested on their own under
tests/objects/, sprites on their own under tests/physics_collisions/, and
neither notices what happens when the two share a frame.

These run through play.start_program() with real pygame events, so the whole
path runs: event draining, click-ownership resolution, physics sub-steps and
update_sprites() — including the detail that update() runs once per sub-step
rather than once per frame, which is what makes widget actions fire ten times
if they are not gated.
"""

from tests.conftest import post_mouse_motion, post_mouse_down, post_mouse_up
from tests.projects.conftest import add_safety_timeout

max_frames = 400


def _screen_xy(screen, x, y):
    """Play-coordinates to pygame screen coordinates."""
    return int(screen.width / 2 + x), int(screen.height / 2 - y)


async def _click(screen, x, y):
    """Press and release at play-coordinates, a frame apart like a real click."""
    import play

    pos = _screen_xy(screen, x, y)
    post_mouse_motion(*pos)
    await play.animate()
    post_mouse_down(*pos)
    await play.animate()
    post_mouse_up(*pos)
    await play.animate()


# ---------------------------------------------------------------------------
# a widget on top of a sprite
# ---------------------------------------------------------------------------


def test_clicking_a_button_does_not_click_the_sprite_under_it():
    """A UI panel over the playfield must absorb the click.

    Widgets default to a layer above plain sprites so the UI draws on top. A
    click that reaches both fires the game action the button was covering —
    the player presses Pause and their character jumps.
    """
    import play
    from play.io.screen import screen

    button_clicks = []
    sprite_clicks = []

    target = play.new_box(color="red", x=0, y=0, width=200, height=200)
    button = play.new_button(text="Pause", x=0, y=0, width=160, height=50)

    target.when_clicked(lambda: sprite_clicks.append(1))
    button.when_clicked(lambda: button_clicks.append(1))

    @play.when_program_starts
    async def driver():
        for _ in range(3):
            await play.animate()
        await _click(screen, 0, 0)
        play.stop_program()

    add_safety_timeout(max_frames)
    play.start_program()

    assert button_clicks, "the button should have been clicked"
    assert not sprite_clicks, "the sprite underneath should not also react"


def test_clicking_beside_the_button_still_reaches_the_sprite():
    """The guard above must not be the button swallowing everything.

    Without this, a bug that made the button eat every click on screen would
    satisfy the previous test perfectly.
    """
    import play
    from play.io.screen import screen

    sprite_clicks = []

    target = play.new_box(color="red", x=0, y=0, width=300, height=300)
    play.new_button(text="Pause", x=0, y=120, width=100, height=40)

    target.when_clicked(lambda: sprite_clicks.append(1))

    @play.when_program_starts
    async def driver():
        for _ in range(3):
            await play.animate()
        await _click(screen, 0, -100)  # well below the button
        play.stop_program()

    add_safety_timeout(max_frames)
    play.start_program()

    assert sprite_clicks, "a click away from the button should reach the sprite"


# ---------------------------------------------------------------------------
# collisions driving a widget
# ---------------------------------------------------------------------------


def test_a_progress_bar_tracks_damage_from_collisions():
    """A health bar updated from a collision callback.

    The collision fires inside the physics step and the widget redraws in
    update_sprites(); this checks the value actually survives that trip rather
    than being overwritten by the widget's own update.
    """
    import play

    health = [100]

    ball = play.new_circle(color="black", x=-150, y=0, radius=10)
    block = play.new_box(color="blue", x=0, y=0, width=40, height=400)
    bar = play.new_progress_bar(min_value=0, max_value=100, value=100, x=0, y=200)

    ball.start_physics(
        obeys_gravity=False, x_speed=200, y_speed=0, friction=0, mass=10, bounciness=1.0
    )
    block.start_physics(
        obeys_gravity=False, can_move=False, friction=0, mass=10, bounciness=1.0
    )

    @ball.when_touching(block)
    def took_damage():
        health[0] -= 25
        bar.value = health[0]
        if health[0] <= 50:
            play.stop_program()

    add_safety_timeout(max_frames)
    play.start_program()

    assert health[0] <= 50, "the ball should have hit the block at least twice"
    assert (
        bar.value == health[0]
    ), f"the bar should show the current health ({health[0]}), not {bar.value}"


# ---------------------------------------------------------------------------
# a widget driving the physics
# ---------------------------------------------------------------------------


def test_a_checkbox_can_freeze_and_release_a_moving_sprite():
    """Pausing physics from a widget, then resuming it.

    A pause implemented by zeroing speed and a pause implemented by removing
    the body look identical while frozen. Resuming is what tells them apart,
    and it is where the body can fail to come back.
    """
    import play
    from play.io.screen import screen

    ball = play.new_circle(color="black", x=-200, y=0, radius=10)
    ball.start_physics(
        obeys_gravity=False, x_speed=150, y_speed=0, friction=0, mass=10, bounciness=1.0
    )
    freeze = play.new_checkbox(label="freeze", x=0, y=200, size_px=30)

    positions = {}

    @freeze.when_changed
    def on_toggle(checked):
        if checked:
            ball.physics.pause()
        else:
            ball.physics.unpause()

    @play.when_program_starts
    async def driver():
        for _ in range(10):
            await play.animate()

        await _click(screen, 0, 200)  # freeze
        positions["frozen_at"] = ball.x
        for _ in range(20):
            await play.animate()
        positions["after_freeze"] = ball.x

        await _click(screen, 0, 200)  # release
        for _ in range(20):
            await play.animate()
        positions["after_release"] = ball.x
        play.stop_program()

    add_safety_timeout(max_frames)
    play.start_program()

    assert freeze.checked is False, "two clicks should leave the box unchecked"
    assert positions["after_freeze"] == positions["frozen_at"], (
        "the ball should not move while frozen "
        f"({positions['frozen_at']} -> {positions['after_freeze']})"
    )
    assert positions["after_release"] > positions["after_freeze"], (
        "the ball should move again once released, but it stayed at "
        f"{positions['after_release']}"
    )


# ---------------------------------------------------------------------------
# widgets and sprite lifetime
# ---------------------------------------------------------------------------


def test_a_button_can_remove_a_physics_sprite_mid_game():
    """Removing a simulated sprite from a widget callback.

    The callback runs while the physics space is mid-frame, so this is the
    ordering most likely to leave a body behind — which the project watchdog
    checks on every frame that follows.
    """
    import play
    from play.io.screen import screen

    ball = play.new_circle(color="black", x=-200, y=0, radius=10)
    ball.start_physics(
        obeys_gravity=False, x_speed=100, y_speed=0, friction=0, mass=10, bounciness=1.0
    )
    remove_button = play.new_button(text="remove", x=0, y=200, width=120, height=40)

    remove_button.when_clicked(ball.remove)

    @play.when_program_starts
    async def driver():
        for _ in range(5):
            await play.animate()
        await _click(screen, 0, 200)
        for _ in range(20):
            await play.animate()
        play.stop_program()

    add_safety_timeout(max_frames)
    play.start_program()

    assert not ball.alive(), "the button should have removed the ball"


def test_a_tooltip_survives_its_target_being_removed():
    """A tooltip holds a reference to the sprite it describes.

    When a game removes that sprite — an enemy dying while the cursor rests on
    it — the tooltip is still in the sprite group and still updating.
    """
    import play
    from play.io.screen import screen

    enemy = play.new_box(color="red", x=0, y=0, width=60, height=60)
    tooltip = play.new_tooltip(target=enemy, text="enemy")
    survived = []

    @play.when_program_starts
    async def driver():
        post_mouse_motion(*_screen_xy(screen, 0, 0))
        for _ in range(5):
            await play.animate()
        enemy.remove()
        for _ in range(20):
            await play.animate()
        # Reached only if every frame after the removal completed: an
        # exception in the tooltip's update would stop the loop before here.
        survived.append(True)
        play.stop_program()

    add_safety_timeout(max_frames)
    play.start_program()

    assert not enemy.alive()
    assert survived, "the game stopped running after the tooltip's target was removed"
    assert tooltip.alive(), "the tooltip should still be a live sprite"


# ---------------------------------------------------------------------------
# overlays, hiding, and dragging over a live playfield
# ---------------------------------------------------------------------------


def test_an_open_dropdown_menu_absorbs_clicks_meant_for_the_playfield():
    """An open menu covers the game; choosing an option must not also hit it."""
    import play
    from play.io.screen import screen

    sprite_clicks = []
    chosen = []

    field = play.new_box(color="green", x=0, y=0, width=400, height=400)
    field.when_clicked(lambda: sprite_clicks.append(1))

    menu = play.new_dropdown(options=["easy", "hard"], x=0, y=100, width=160)
    menu.when_changed(lambda value, index: chosen.append(value))

    # The open list is drawn below the closed box: option i occupies the band
    # starting one box-height down, so with height=40 at y=100 option 1 ("hard")
    # sits at play y=20. Option 0 is already selected, so picking it would not
    # fire when_changed and the assertion below would prove nothing.
    @play.when_program_starts
    async def driver():
        for _ in range(3):
            await play.animate()
        await _click(screen, 0, 100)  # open the menu
        await _click(screen, 0, 20)  # pick the second option
        play.stop_program()

    add_safety_timeout(max_frames)
    play.start_program()

    assert chosen == [
        "hard"
    ], f"the second option should have been picked, got {chosen}"
    assert menu.selected_value == "hard"
    assert (
        not sprite_clicks
    ), "the playfield under the menu should not have been clicked"


def test_hiding_a_widget_hands_the_playfield_back():
    """A dismissed overlay must stop intercepting clicks.

    A pause menu that keeps eating clicks after being hidden leaves the game
    looking alive and completely unresponsive.
    """
    import play
    from play.io.screen import screen

    sprite_clicks = []

    field = play.new_box(color="green", x=0, y=0, width=400, height=400)
    field.when_clicked(lambda: sprite_clicks.append(1))
    overlay = play.new_button(text="resume", x=0, y=0, width=200, height=80)

    @play.when_program_starts
    async def driver():
        for _ in range(3):
            await play.animate()
        overlay.hide()
        await play.animate()
        await _click(screen, 0, 0)
        play.stop_program()

    add_safety_timeout(max_frames)
    play.start_program()

    assert sprite_clicks, "with the overlay hidden the click should reach the playfield"


def test_a_slider_drag_survives_a_busy_physics_frame():
    """Dragging while the space is simulating.

    The drag is state carried across frames; the physics sub-steps run
    update() repeatedly in between. A drag that reset itself per sub-step
    would jump or stall exactly here and nowhere else.
    """
    import play
    from play.io.screen import screen

    for i in range(6):
        ball = play.new_circle(color="black", x=-200 + i * 40, y=-150, radius=8)
        ball.start_physics(
            obeys_gravity=False,
            x_speed=120,
            y_speed=60,
            friction=0,
            mass=10,
            bounciness=1.0,
        )

    slider = play.new_slider(min_value=0, max_value=100, value=0, x=0, y=150, width=200)

    @play.when_program_starts
    async def driver():
        for _ in range(5):
            await play.animate()

        start = _screen_xy(screen, -90, 150)
        post_mouse_motion(*start)
        await play.animate()
        post_mouse_down(*start)
        await play.animate()

        for x in (-40, 0, 40, 90):
            post_mouse_motion(*_screen_xy(screen, x, 150))
            await play.animate()

        post_mouse_up(*_screen_xy(screen, 90, 150))
        await play.animate()
        play.stop_program()

    add_safety_timeout(max_frames)
    play.start_program()

    assert slider.value == 100, (
        f"the drag should have reached max_value with sprites simulating, "
        f"got {slider.value}"
    )
    assert slider._dragging is False, "releasing the mouse should end the drag"
