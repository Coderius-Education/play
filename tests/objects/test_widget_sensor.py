"""UI widgets are physics sensors: hit-testable, but nothing bounces off them.

Every sprite has a physics body, and for widgets that body is the hit-test
behind hover and clicks. As a solid kinematic body it also stopped physics
sprites, so a ball in a game bounced off a "Pause" button. See #225.
"""

import pytest

import play
from play.core.sprites_loop import update_sprite_physics
from play.io.mouse import mouse
from play.objects.sprite import point_touching_sprite
from play.physics import physics_space


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


# Every UI factory, each built as a 120x40-ish element at the origin.
UI = {
    "button": lambda: play.new_button("Go", x=0, y=0, width=120, height=40),
    "checkbox": lambda: play.new_checkbox("Sound", x=0, y=0),
    "slider": lambda: play.new_slider(x=0, y=0),
    "dropdown": lambda: play.new_dropdown(options=["A", "B"], x=0, y=0),
    "radio_button": lambda: play.new_radio_button("A", value="a", x=0, y=0),
    "text_input": lambda: play.new_text_input(x=0, y=0),
    "progress_bar": lambda: play.new_progress_bar(x=0, y=0),
}
NAMES = sorted(UI)


def _drop_ball_through(frames=180):
    """Drop a ball from above the origin and return its lowest point."""
    ball = play.new_circle(x=0, y=150, radius=10)
    ball.start_physics(can_move=True, stable=False, obeys_gravity=True)
    lowest = ball.y
    for _ in range(frames):
        physics_space.step(1 / 60)
        update_sprite_physics(ball)
        lowest = min(lowest, ball.y)
    return lowest


@pytest.mark.parametrize("name", NAMES)
def test_a_ball_falls_through_every_ui_element(name):
    widget = UI[name]()
    assert widget.physics.sensor is True
    # Solid, the ball would come to rest on the widget's top edge, near y=30.
    # It falls at most 100 px/s, so three seconds take it below the widget.
    assert _drop_ball_through() < -100


def test_ordinary_sprites_are_still_solid():
    box = play.new_box(x=0, y=0, width=120, height=40)
    assert box.physics.sensor is False
    assert _drop_ball_through() == pytest.approx(30, abs=2)


def test_a_widget_can_opt_out_and_be_solid():
    button = UI["button"]()
    button.physics.sensor = False
    assert _drop_ball_through() == pytest.approx(30, abs=2)


def test_giving_a_widget_physics_makes_it_solid_again():
    # Only the automatic body is a sensor. A student who calls start_physics()
    # on a widget wants it to behave like physics, walls included, so it
    # lands on the floor instead of falling out of the screen.
    from play.io.screen import screen

    button = play.new_button("Go", x=0, y=0, width=120, height=40)
    button.start_physics(can_move=True, stable=False, obeys_gravity=True)
    assert button.physics.sensor is False

    for _ in range(600):
        physics_space.step(1 / 60)
        update_sprite_physics(button)

    assert button.y > screen.bottom


def test_stop_physics_makes_a_widget_a_sensor_again():
    button = UI["button"]()
    button.start_physics()
    assert button.physics.sensor is False
    button.stop_physics()
    assert button.physics.sensor is True
    button.start_physics(sensor=True)
    assert button.physics.sensor is True


@pytest.mark.parametrize("name", NAMES)
def test_the_mouse_still_hits_a_sensor_widget(name):
    widget = UI[name]()
    widget.update()
    assert point_touching_sprite((0, 0), widget)
    assert not point_touching_sprite((0, 300), widget)


def test_a_rotated_sensor_widget_is_hit_where_it_is_drawn():
    button = UI["button"]()
    button.angle = 90
    physics_space.step(1 / 60)  # the game loop steps every frame
    # Upright the button spans x -60..60, y -20..20; turned it is the reverse.
    assert point_touching_sprite((0, 50), button)
    assert not point_touching_sprite((50, 0), button)


def test_a_click_on_a_sensor_button_still_fires():
    button = UI["button"]()
    clicks = []

    @button.when_clicked
    def on_click():
        clicks.append(True)

    from tests.conftest import post_mouse_down, post_mouse_motion, post_mouse_up
    from play.io.screen import screen

    sx, sy = int(screen.width / 2), int(screen.height / 2)

    @play.when_program_starts
    async def driver():
        post_mouse_motion(sx, sy)
        await play.animate()
        post_mouse_down(sx, sy)
        await play.animate()
        post_mouse_up(sx, sy)
        await play.animate()
        play.stop_program()

    play.start_program()
    assert clicks == [True]


def test_when_touching_a_sensor_widget_still_fires():
    # pymunk still reports begin/separate for sensors, so a game can react to
    # a sprite reaching a widget even though it no longer bounces off it.
    button = UI["button"]()
    ball = play.new_circle(x=0, y=0, radius=10)
    ball.start_physics(can_move=True, stable=False, obeys_gravity=False)
    touched = []

    @ball.when_touching(button)
    def on_touch():
        touched.append(True)

    frames = [0]

    @play.repeat_forever
    def tick():
        frames[0] += 1
        if frames[0] == 5:
            play.stop_program()

    play.start_program()
    assert touched, "when_touching between a sprite and a sensor widget should fire"
