"""Edge cases — realistic scenarios where students make mistakes.

These are common beginner mistakes that should not crash the engine:
- Creating sprites at exact screen edges
- Registering empty callbacks (do-nothing handlers)
- Setting speed to 0 mid-game
- Hiding a sprite that is already hidden
- Showing a sprite that is already shown
- Removing a sprite during gameplay

This test verifies:
- sprites at screen edges don't cause physics glitches
- empty/no-op callbacks don't crash the event system
- rapid hide/show toggling is safe
- sprite removal mid-game doesn't crash
"""

from tests.projects.conftest import add_safety_timeout

max_frames = 200


def test_edge_sprites_at_boundaries():
    """Sprites created at exact screen edges should not glitch or crash."""
    import play

    # Create sprites at all four edges
    top = play.new_box(color="red", x=0, y=300, width=20, height=20)
    bottom = play.new_box(color="blue", x=0, y=-300, width=20, height=20)
    left = play.new_box(color="green", x=-400, y=0, width=20, height=20)
    right = play.new_box(color="yellow", x=400, y=0, width=20, height=20)

    # Give them physics — they should bounce off the walls
    for sprite in [top, bottom, left, right]:
        sprite.start_physics(
            obeys_gravity=False,
            x_speed=50,
            y_speed=50,
            bounciness=1.0,
            mass=1,
        )

    frames_run = [0]

    @play.repeat_forever
    def tick():
        frames_run[0] += 1
        if frames_run[0] >= max_frames:
            play.stop_program()

    play.start_program()

    assert frames_run[0] >= max_frames, "simulation should have completed all frames"


def test_edge_empty_callbacks():
    """Empty/no-op callbacks should not crash the event system."""
    import play

    ball = play.new_circle(color="black", x=0, y=0, radius=10)
    wall = play.new_box(color="gray", x=200, y=0, width=10, height=600)

    ball.start_physics(obeys_gravity=False, x_speed=300, bounciness=1.0)
    wall.start_physics(obeys_gravity=False, can_move=False, bounciness=1.0)

    # Register empty callbacks — students often do this as placeholders
    @ball.when_stopped_touching(wall)
    def nothing():
        pass

    @ball.when_touching_wall
    def also_nothing():
        pass

    @play.when_any_key_pressed
    def key_noop(key):
        pass

    add_safety_timeout(max_frames)

    play.start_program()
    # If we get here without crashing, the test passes


def test_edge_rapid_hide_show():
    """Rapidly toggling hide/show should not crash or corrupt state."""
    import play

    box = play.new_box(color="red", x=0, y=0, width=50, height=50)
    box.start_physics(obeys_gravity=False, x_speed=100, bounciness=1.0)

    toggles = [0]

    @play.repeat_forever
    def toggle():
        if toggles[0] % 2 == 0:
            box.hide()
            # Hiding again while already hidden
            box.hide()
        else:
            box.show()
            # Showing again while already shown
            box.show()
        toggles[0] += 1
        if toggles[0] >= 60:
            play.stop_program()

    play.start_program()

    assert toggles[0] >= 60, "should have toggled hide/show 60 times"
    # Final iteration: toggles was 59 (odd) → show() was called last
    assert box.is_shown


def test_edge_remove_mid_game():
    """Removing a sprite mid-game should not crash the physics or rendering."""
    import play

    sprites = [
        play.new_circle(color="red", x=-100 + i * 50, y=0, radius=10) for i in range(5)
    ]
    for s in sprites:
        s.start_physics(obeys_gravity=False, x_speed=50, bounciness=1.0)

    removed = [0]

    @play.repeat_forever
    def remove_one():
        # Remove one sprite per frame until all are gone
        if removed[0] < len(sprites):
            sprites[removed[0]].remove()
            removed[0] += 1
        else:
            play.stop_program()

    play.start_program()

    assert removed[0] == len(sprites), "all sprites should have been removed"


def test_edge_zero_speed_midgame():
    """Setting speed to 0 mid-game should freeze the sprite."""
    import play

    ball = play.new_circle(color="black", x=0, y=0, radius=10)
    ball.start_physics(obeys_gravity=False, x_speed=200, y_speed=100, bounciness=1.0)

    frozen_stable = [True]

    @play.when_program_starts
    async def driver():
        # Let ball move for a bit
        for _ in range(20):
            await play.animate()

        # Freeze the ball
        ball.physics.x_speed = 0
        ball.physics.y_speed = 0

        frozen_x = ball.x
        frozen_y = ball.y

        # Verify it stays still
        for _ in range(20):
            await play.animate()

        if abs(ball.x - frozen_x) > 1 or abs(ball.y - frozen_y) > 1:
            frozen_stable[0] = False

        play.stop_program()

    play.start_program()

    assert frozen_stable[0], "ball should not move after setting speed to 0"


if __name__ == "__main__":
    test_edge_sprites_at_boundaries()
    test_edge_empty_callbacks()
    test_edge_rapid_hide_show()
    test_edge_remove_mid_game()
    test_edge_zero_speed_midgame()
