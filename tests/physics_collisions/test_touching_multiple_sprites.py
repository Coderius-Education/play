"""A sprite touching two other sprites at once must keep both callbacks live.

Every collision record used to be filed under ``shape.collision_id``, which is
always ``CollisionType.SPRITE`` -- one shared slot for every sprite-sprite
pair.  So a sprite with two ``when_touching`` callbacks could only ever have
one of them running, and separating from either sprite deleted the record for
the other one as well.  That is the shape of a platformer: the player rests on
the ground while walking through coins, and the moment it leaves a coin the
ground callback goes quiet for the rest of the game.

The zones here are sensors so the ball passes through instead of bouncing off,
which keeps the overlap long and the timing easy to reason about.
"""

MAX_FRAMES = 400


def test_touching_two_sprites_at_once():
    import play

    counts = {"wide": 0, "narrow": 0}
    seen = {}

    ball = play.new_circle(color="black", x=-300, y=0, radius=10)
    # The narrow zone sits inside the wide one, so the ball is in both at once.
    wide = play.new_box(color="blue", x=0, y=0, width=400, height=60)
    narrow = play.new_box(color="red", x=0, y=0, width=40, height=60)

    ball.start_physics(
        obeys_gravity=False, x_speed=200, friction=0, mass=10, bounciness=1.0
    )
    wide.start_physics(obeys_gravity=False, can_move=False, sensor=True)
    narrow.start_physics(obeys_gravity=False, can_move=False, sensor=True)

    @ball.when_touching(wide)
    def touching_wide():
        counts["wide"] += 1

    @ball.when_touching(narrow)
    def touching_narrow():
        counts["narrow"] += 1
        seen.setdefault("wide_when_narrow_began", counts["wide"])

    @ball.when_stopped_touching(narrow)
    def left_narrow():
        seen.setdefault("wide_when_narrow_ended", counts["wide"])

    @play.when_program_starts
    async def driver():
        for _ in range(MAX_FRAMES):
            await play.animate()
            # Keep going a good while past the narrow zone, but stop before the
            # ball leaves the wide one at x = 200.
            if "wide_when_narrow_ended" in seen and ball.x > 150:
                break
        seen["wide_at_end"] = counts["wide"]
        seen["final_x"] = ball.x
        play.stop_program()

    play.start_program()

    assert counts["narrow"] > 0, "the ball should have passed through the narrow zone"
    assert (
        "wide_when_narrow_ended" in seen
    ), "the ball should have left the narrow zone before the test ended"

    # Both callbacks live at the same time.
    began = seen["wide_when_narrow_began"]
    ended = seen["wide_when_narrow_ended"]
    assert ended > began, (
        "the wide-zone callback should keep running while the ball is also in "
        f"the narrow zone (count stuck at {began})"
    )

    # Leaving one zone must not cancel the other.
    assert seen["final_x"] < 200, "the ball should still be inside the wide zone"
    assert seen["wide_at_end"] > ended, (
        "leaving the narrow zone silently cancelled the wide-zone callback: "
        f"it stopped at {ended} while the ball was still inside the wide zone"
    )


def test_when_touching_fires_while_resting_on_a_platform():
    """The platformer case: falling onto a static platform and staying there.

    Nothing else in the suite covers a gravity-driven landing -- the existing
    when_touching tests all use sprites moving under their own speed with
    gravity off -- and it is the first thing a student builds after pong.
    """
    import play

    landings = [0]
    seen = {}

    ground = play.new_box(color="brown", x=0, y=-230, width=700, height=20)
    player = play.new_box(color="green", x=0, y=-150, width=30, height=30)

    player.start_physics(obeys_gravity=True, friction=0, mass=5, bounciness=0.0)
    ground.start_physics(obeys_gravity=False, can_move=False, bounciness=0.0)

    @player.when_touching(ground)
    def on_ground():
        landings[0] += 1

    @play.when_program_starts
    async def driver():
        # A 55px drop under gravity of -100 takes about a second; 200 frames is
        # comfortably more than that.
        for _ in range(200):
            await play.animate()
            if landings[0] > 0:
                break
        seen["landings"] = landings[0]
        seen["player_y"] = player.y
        play.stop_program()

    play.start_program()

    assert seen["landings"] > 0, (
        "a sprite that falls onto a static platform should trigger "
        f"when_touching; the player ended at y={seen['player_y']} with the "
        f"platform top at {ground.y + 10}"
    )


if __name__ == "__main__":
    test_touching_two_sprites_at_once()
    test_when_touching_fires_while_resting_on_a_platform()
