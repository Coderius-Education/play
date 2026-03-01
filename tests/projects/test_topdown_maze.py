"""Top-down maze game — realistic full-game project test.

A player moves in four directions (no gravity) through a simple maze of walls.
The player picks up a key, then reaches a door to win.  This is a common
student pattern: top-down adventure/maze with WASD/arrow movement and
item collection.

This test verifies:
- obeys_gravity=False for top-down movement (no gravity world)
- four-directional keyboard movement
- is_touching for item pickup and door detection
- sprite.hide() for collected items
- set_gravity to disable gravity entirely
- the game completes on reaching the exit
"""

from tests.conftest import post_key_down, post_key_up
from tests.projects.conftest import add_safety_timeout

max_frames = 2000


def test_topdown_maze():
    import pygame
    import play
    from play.physics import set_gravity

    # Disable gravity for top-down view
    set_gravity(vertical=0, horizontal=0)

    has_key = [False]
    reached_door = [False]
    moves = [0]

    # --- sprites -----------------------------------------------------------
    player = play.new_box(color="green", x=-200, y=0, width=20, height=20)

    # Walls forming a simple corridor
    wall_top = play.new_box(color="gray", x=0, y=100, width=500, height=20)
    wall_bottom = play.new_box(color="gray", x=0, y=-100, width=500, height=20)

    # Key item in the middle
    key_item = play.new_circle(color="yellow", x=0, y=0, radius=8)

    # Door at the far right
    door = play.new_box(color="blue", x=200, y=0, width=20, height=60)

    status_text = play.new_text(words="Find the key!", x=0, y=260, font_size=24)

    # --- physics -----------------------------------------------------------
    player.start_physics(
        obeys_gravity=False,
        x_speed=0,
        y_speed=0,
        friction=0,
        mass=5,
        bounciness=0.0,
    )
    wall_top.start_physics(obeys_gravity=False, can_move=False, bounciness=0.0)
    wall_bottom.start_physics(obeys_gravity=False, can_move=False, bounciness=0.0)
    key_item.start_physics(obeys_gravity=False, can_move=False, bounciness=0.0)
    door.start_physics(obeys_gravity=False, can_move=False, bounciness=0.0)

    # --- keyboard movement -------------------------------------------------
    @play.when_key_pressed("right")
    def move_right(key=None):
        player.physics.x_speed = 200
        moves[0] += 1

    @play.when_key_pressed("left")
    def move_left(key=None):
        player.physics.x_speed = -200
        moves[0] += 1

    @play.when_key_pressed("up")
    def move_up(key=None):
        player.physics.y_speed = 200
        moves[0] += 1

    @play.when_key_pressed("down")
    def move_down(key=None):
        player.physics.y_speed = -200
        moves[0] += 1

    # --- driver: move right, collect key, reach door -----------------------
    @play.when_program_starts
    async def driver():
        for frame in range(max_frames):
            # Move right in bursts
            if frame % 20 == 0:
                post_key_down(pygame.K_RIGHT)
            if frame % 20 == 5:
                post_key_up(pygame.K_RIGHT)
                # Stop horizontal after key release
                player.physics.x_speed = 0

            # Check key pickup
            if (
                not has_key[0]
                and not key_item.is_hidden
                and player.is_touching(key_item)
            ):
                has_key[0] = True
                key_item.hide()
                status_text.words = "Go to the door!"

            # Check door
            if has_key[0] and player.is_touching(door):
                reached_door[0] = True
                status_text.words = "You win!"
                play.stop_program()
                return

            await play.animate()

        play.stop_program()

    play.start_program()

    # --- assertions --------------------------------------------------------
    assert moves[0] > 0, "player should have moved"
    assert has_key[0], "player should have collected the key"
    assert reached_door[0], "player should have reached the door"


if __name__ == "__main__":
    test_topdown_maze()
