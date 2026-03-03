"""Typing game — realistic full-game project test.

Letters appear on screen and the player must type them. Pressing the correct
key scores a point. Releasing a key updates a status display.

This test verifies:
- @play.when_any_key_pressed as an actual game mechanic
- @play.when_any_key_released (completely untested until now)
- @play.when_key_released for specific key
- text.words dynamic updates
- text.color setter
"""

from tests.conftest import post_key_down, post_key_up

MAX_FRAMES = 150
TARGET_SCORE = 3


def test_typing_game():
    import pygame
    import play
    from play.io.screen import screen

    score = [0]
    keys_released = [0]
    specific_released = [0]
    frames_run = [0]
    current_letter = ["a"]
    last_pressed_key = [None]

    # --- sprites ---
    letter_display = play.new_text(words="a", x=0, y=0, font_size=80, color="black")
    score_text = play.new_text(words="Score: 0", x=0, y=screen.top - 30, font_size=25)
    status_text = play.new_text(
        words="Type!", x=0, y=screen.bottom + 40, font_size=20, color="gray"
    )

    # Map of letters to pygame keys
    letter_keys = {"a": pygame.K_a, "b": pygame.K_b, "c": pygame.K_c}
    letters = list(letter_keys.keys())

    # --- key pressed handler ---
    @play.when_any_key_pressed
    def on_key(key):
        if key == current_letter[0]:
            score[0] += 1
            score_text.words = f"Score: {score[0]}"
            score_text.color = "green"
            # Next letter
            current_letter[0] = letters[score[0] % len(letters)]
            letter_display.words = current_letter[0]
        else:
            score_text.color = "red"

    # --- key released handler ---
    @play.when_any_key_released
    def on_release(key):
        keys_released[0] += 1
        status_text.words = f"Released: {key}"

    # --- specific key released ---
    @play.when_key_released("a")
    def on_a_released(key):
        specific_released[0] += 1

    # --- game loop ---
    @play.when_program_starts
    async def game_loop():
        for frame in range(MAX_FRAMES):
            await play.animate()
            frames_run[0] += 1

            if score[0] >= TARGET_SCORE:
                play.stop_program()
                return

            # Press the correct letter every 10 frames, release 5 frames later
            # This gives the event loop time to process each event
            if frame % 10 == 0:
                key_const = letter_keys.get(current_letter[0], pygame.K_a)
                last_pressed_key[0] = key_const
                post_key_down(key_const)
            if frame % 10 == 5 and last_pressed_key[0] is not None:
                post_key_up(last_pressed_key[0])
                last_pressed_key[0] = None

        play.stop_program()

    play.start_program()

    # --- assertions ---
    assert frames_run[0] >= 1, "Game loop never ran"
    assert score[0] >= TARGET_SCORE, f"Expected score >= {TARGET_SCORE}, got {score[0]}"
    assert keys_released[0] >= 1, "when_any_key_released never fired"
    assert specific_released[0] >= 1, "when_key_released('a') never fired"
    assert score_text.color in (
        "green",
        "red",
    ), f"text.color was never set, got {score_text.color}"


if __name__ == "__main__":
    test_typing_game()
