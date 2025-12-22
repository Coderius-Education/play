"""Test coverage for all physics collision scenarios."""
import play

# Test results tracking
results = {
    "both_physics_touching": False,
    "both_physics_stopped": False,
    "neither_physics_touching": False,
    "neither_physics_stopped": False,
    "mixed_a_physics_touching": False,
    "mixed_a_physics_stopped": False,
    "mixed_b_physics_touching": False,
    "mixed_b_physics_stopped": False,
}

# ============================================================
# Case 1: Both sprites have physics
# ============================================================
ball1 = play.new_circle(color="blue", radius=30, x=-200, y=200)
ball1.start_physics(obeys_gravity=False, x_speed=100)

target1 = play.new_box(color="red", x=0, y=200, width=50, height=50)
target1.start_physics(can_move=False, obeys_gravity=False)

@ball1.when_touching(target1)
def both_physics_touch():
    results["both_physics_touching"] = True
    print("✓ Case 1a: Both physics - when_touching")

@ball1.when_stopped_touching(target1)
def both_physics_stopped():
    results["both_physics_stopped"] = True
    print("✓ Case 1b: Both physics - when_stopped_touching")


# ============================================================
# Case 2: Neither sprite has physics
# ============================================================
box1 = play.new_box(color="green", x=-200, y=100, width=40, height=40)
box2 = play.new_box(color="yellow", x=-200, y=100, width=40, height=40)

@box1.when_touching(box2)
def neither_physics_touch():
    results["neither_physics_touching"] = True
    print("✓ Case 2a: Neither physics - when_touching")

@box1.when_stopped_touching(box2)
def neither_physics_stopped():
    results["neither_physics_stopped"] = True
    print("✓ Case 2b: Neither physics - when_stopped_touching")

# Move box2 away to trigger stopped touching
@play.repeat_forever
async def move_box2():
    await play.timer(seconds=0.5)
    box2.x = 0
    await play.timer(seconds=0.5)
    box2.x = -200


# ============================================================
# Case 3: Mixed - First sprite has physics, second doesn't
# ============================================================
ball2 = play.new_circle(color="purple", radius=30, x=-200, y=0)
ball2.start_physics(obeys_gravity=False, x_speed=100)

target2 = play.new_box(color="orange", x=0, y=0, width=50, height=50)
# target2 has NO physics

@ball2.when_touching(target2)
def mixed_a_physics_touch():
    results["mixed_a_physics_touching"] = True
    print("✓ Case 3a: Mixed (A has physics) - when_touching")

@ball2.when_stopped_touching(target2)
def mixed_a_physics_stopped():
    results["mixed_a_physics_stopped"] = True
    print("✓ Case 3b: Mixed (A has physics) - when_stopped_touching")


# ============================================================
# Case 4: Mixed - First sprite has no physics, second does
# ============================================================
box3 = play.new_box(color="cyan", x=-200, y=-100, width=40, height=40)
# box3 has NO physics

ball3 = play.new_circle(color="pink", radius=30, x=0, y=-100)
ball3.start_physics(obeys_gravity=False, x_speed=100)

@box3.when_touching(ball3)
def mixed_b_physics_touch():
    results["mixed_b_physics_touching"] = True
    print("✓ Case 4a: Mixed (B has physics) - when_touching")

@box3.when_stopped_touching(ball3)
def mixed_b_physics_stopped():
    results["mixed_b_physics_stopped"] = True
    print("✓ Case 4b: Mixed (B has physics) - when_stopped_touching")


# ============================================================
# Test results display
# ============================================================
status_text = play.new_text(
    words="Running tests...",
    x=0,
    y=-200,
    font_size=20,
)

@play.repeat_forever
async def check_results():
    await play.timer(seconds=3)
    passed = sum(results.values())
    total = len(results)

    status_text.words = f"Tests: {passed}/{total} passed"

    if passed == total:
        status_text.words += " ✓ ALL TESTS PASSED!"
        print("\n" + "="*50)
        print("ALL TESTS PASSED!")
        print("="*50)
        for test_name, result in results.items():
            print(f"  {'✓' if result else '✗'} {test_name}")
    else:
        print(f"\nTests in progress: {passed}/{total}")


play.start_program()