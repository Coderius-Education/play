"""A multiple-choice quiz — buttons, a question, and answer checking.

One of the most common things a class builds, and the first project test to
use the widget toolkit as a student would: two answer buttons, a question
that advances, and a score.
"""

from tests.conftest import post_mouse_motion, post_mouse_down, post_mouse_up
from tests.projects.conftest import add_safety_timeout

max_frames = 600

QUESTIONS = [
    ("2 + 2 = ?", "4", "5"),
    ("3 x 3 = ?", "9", "6"),
]


def test_quiz_game():
    import play
    from play.io.screen import screen

    score = [0]
    wrong = [0]
    index = [0]
    seen = {}

    question = play.new_text(words=QUESTIONS[0][0], x=0, y=150, font_size=40)
    right_button = play.new_button(
        QUESTIONS[0][1], x=-120, y=0, width=160, height=60
    )
    wrong_button = play.new_button(QUESTIONS[0][2], x=120, y=0, width=160, height=60)

    def next_question():
        index[0] += 1
        if index[0] >= len(QUESTIONS):
            question.words = "Done!"
            right_button.hide()
            wrong_button.hide()
            return
        text, right, wrong_text = QUESTIONS[index[0]]
        question.words = text
        right_button.text = right
        wrong_button.text = wrong_text

    @right_button.when_clicked
    def on_right():
        score[0] += 1
        next_question()

    @wrong_button.when_clicked
    def on_wrong():
        wrong[0] += 1

    @play.when_program_starts
    async def driver():
        async def click(x, y):
            pos = (int(screen.width / 2 + x), int(screen.height / 2 - y))
            post_mouse_motion(*pos)
            await play.animate()
            post_mouse_down(*pos)
            await play.animate()
            post_mouse_up(*pos)
            await play.animate()

        for _ in range(5):
            await play.animate()

        await click(120, 0)  # wrong answer: scores nothing, question stays
        seen["after_wrong"] = (score[0], wrong[0], question.words)

        await click(-120, 0)  # right answer: advances
        seen["after_right"] = (score[0], question.words, right_button.text)

        await click(-120, 0)  # right again: finishes the quiz
        seen["finished"] = (score[0], question.words, right_button.is_hidden)

        # The quiz is over; the hidden buttons must be inert.
        await click(-120, 0)
        seen["after_finish_click"] = score[0]
        play.stop_program()

    add_safety_timeout(max_frames)
    play.start_program()

    score_after_wrong, wrong_count, question_after_wrong = seen["after_wrong"]
    assert wrong_count == 1, "the wrong button should register a wrong answer"
    assert score_after_wrong == 0, "a wrong answer must not score"
    assert (
        question_after_wrong == QUESTIONS[0][0]
    ), "a wrong answer should leave the question up"

    score_after_right, question_2, right_label = seen["after_right"]
    assert score_after_right == 1
    assert question_2 == QUESTIONS[1][0], "a right answer should move to question two"
    assert right_label == QUESTIONS[1][1], "the buttons should relabel per question"

    final_score, final_question, buttons_hidden = seen["finished"]
    assert final_score == 2
    assert final_question == "Done!"
    assert buttons_hidden is True, "finishing the quiz should hide the answer buttons"
    assert (
        seen["after_finish_click"] == 2
    ), "clicking a hidden answer button must not score"
