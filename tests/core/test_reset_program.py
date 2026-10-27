"""play.reset_program(): back to the state of a fresh import, for a playground or a test suite."""

import asyncio
import gc
import logging
import weakref

import pygame
import pytest

import play
from play.callback.collision_callbacks import collision_registry
from play.core.controller_loop import controller_state
from play.globals import ProgramState, globals_list
from play.io import controllers as controllers_module
from play.io.controllers import controllers
from play.io.keypress import keyboard_state
from play.physics import physics_space, set_gravity
from tests.events.frames import button_down, mouse_down, mouse_move, play_frames


def _stop_on_the_first_frame(heard, name):
    """A repeat_forever callback that notes *name* in *heard* and stops the program."""

    def tick():
        heard.append(name)
        play.stop_program()

    return tick


def test_a_second_program_runs_after_a_reset_without_the_first_programs_callbacks():
    heard = []
    play.repeat_forever(_stop_on_the_first_frame(heard, "first"))
    play.start_program()

    play.reset_program()
    play.repeat_forever(_stop_on_the_first_frame(heard, "second"))
    play.start_program()

    assert heard == ["first", "second"]


def test_a_reset_puts_back_the_screen_physics_backdrop_and_event_queue():
    play.new_box(color="red", width=200, height=200)
    play.screen.width, play.screen.height = 300, 200
    play.screen.caption = "My game"
    play.screen.resizable = True
    set_gravity(vertical=-500, horizontal=20)
    play.set_backdrop("blue")
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_a}))

    play.reset_program()
    assert not pygame.event.peek(pygame.KEYDOWN)
    play.repeat_forever(play.stop_program)
    play.start_program()

    assert play.screen.size == (800, 600)
    assert play.screen.caption == "coderius-play"
    assert play.screen.resizable is False
    assert tuple(physics_space.gravity) == (0, -100)
    assert globals_list.display.get_at((400, 300))[:3] == (255, 255, 255)
    assert len(globals_list.walls) == 4


def test_a_reset_forgets_the_mouse_keys_and_buttons_of_the_last_program():
    play.mouse.x, play.mouse.y = 120, -80
    play.mouse._is_clicked = True
    keyboard_state.pressed.add("a")
    play_frames([button_down(4)], then=0)

    play.reset_program()
    assert not controller_state.any()
    assert not controller_state.buttons_pressed_this_frame
    held = []
    controllers.while_button_pressed(0, 4)(held.append)
    play.repeat_forever(play.stop_program)
    play.start_program()

    assert (play.mouse.x, play.mouse.y) == (0, 0)
    assert not play.mouse.is_clicked
    assert not play.key_is_pressed("a")
    assert held == []


def test_a_reset_lets_go_of_the_last_programs_sprites_and_widgets():
    box = play.new_box(x=-200, width=50, height=50)
    box.when_touching(play.new_circle(x=200, radius=10))(lambda: None)
    field = play.new_text_input(x=0, y=200)
    menu = play.new_dropdown(options=["a", "b"], x=0, y=-100)
    button = play.new_button(x=200, y=-200)
    play_frames(
        [mouse_move(-200, 0)],
        [mouse_down(-200, 0)],
        [mouse_move(0, 200)],
        [mouse_down(0, 200)],
        [mouse_move(200, -200)],
        [mouse_down(200, -200)],
        [mouse_move(0, -100)],
        [mouse_down(0, -100)],
        then=0,
    )
    left_behind = [weakref.ref(thing) for thing in (box, field, menu, button)]
    del box, field, menu, button

    play.reset_program()
    play.repeat_forever(play.stop_program)
    play.start_program()
    gc.collect()

    assert [ref() for ref in left_behind] == [None] * 4


def test_a_reset_stops_videos_and_sounds(video_file, monkeypatch):
    stopped = []
    monkeypatch.setattr(pygame.mixer, "get_init", lambda: (22050, -16, 2))
    monkeypatch.setattr(pygame.mixer, "stop", lambda: stopped.append(True))
    video = play.new_video(video_file)
    video.play()
    assert video.playing

    play.reset_program()

    assert not video.playing
    assert stopped == [True]


def test_a_reset_lets_go_of_a_focused_text_field(monkeypatch):
    calls = []
    monkeypatch.setattr(pygame.key, "start_text_input", lambda: calls.append("on"))
    monkeypatch.setattr(pygame.key, "stop_text_input", lambda: calls.append("off"))
    play.new_text_input(x=0, y=0)
    play_frames([mouse_move(0, 0)], [mouse_down(0, 0)], then=0)
    assert calls == ["on"]

    play.reset_program()

    assert calls == ["on", "off"]
    assert globals_list.focused_text_input is None


def test_a_reset_finds_the_controllers_that_are_plugged_in_now(monkeypatch):
    class _Joystick:
        """A plugged-in controller that tells which device it is."""

        def __init__(self, device_index):
            self.device_index = device_index

        def init(self):
            pass

        def get_instance_id(self):
            return 10 + self.device_index

    monkeypatch.setattr(controllers_module, "_Controller", _Joystick)
    monkeypatch.setattr(controllers_module, "_get_controller_count", lambda: 2)
    monkeypatch.setattr(controllers, "_controllers", [])

    play.reset_program()

    assert controllers.get_count() == 2


def test_a_reset_empties_the_physics_space_of_constraints_too():
    import pymunk

    a, b = pymunk.Body(), pymunk.Body()
    physics_space.add(pymunk.PinJoint(a, b))

    play.reset_program()

    assert not physics_space.constraints


def test_a_reset_puts_the_asyncio_logger_back():
    play.repeat_forever(play.stop_program)
    play.start_program()
    assert logging.getLogger("asyncio").level == logging.CRITICAL

    play.reset_program()

    assert logging.getLogger("asyncio").level == logging.NOTSET


def test_a_reset_gives_the_asyncio_logger_back_the_level_the_host_gave_it():
    logger = logging.getLogger("asyncio")
    logger.setLevel(logging.ERROR)
    try:
        play.repeat_forever(play.stop_program)
        play.start_program()
        play.reset_program()

        assert logger.level == logging.ERROR
    finally:
        logger.setLevel(logging.NOTSET)


def test_a_reset_forgets_the_last_programs_collision_callbacks():
    a = play.new_box(x=0)
    b = play.new_box(x=200)
    a.when_touching(b)(lambda: None)
    a.when_stopped_touching(b)(lambda: None)

    play.reset_program()

    assert collision_registry.callbacks == {True: {}, False: {}}


def test_resets_one_after_another_keep_only_the_four_new_walls():
    for _ in range(3):
        play.reset_program()

    assert len(globals_list.walls[0].body.shapes) == 4


def test_a_reset_on_the_desktop_leaves_no_closed_event_loop_behind():
    play.repeat_forever(play.stop_program)
    play.start_program()

    play.reset_program()

    try:
        current = asyncio.get_event_loop()
    except RuntimeError:
        current = None
    assert current is None or not current.is_closed()


def test_a_reset_inside_a_running_event_loop_on_the_desktop_is_refused_and_changes_nothing():
    heard = []
    play.repeat_forever(_stop_on_the_first_frame(heard, "first"))
    play.start_program()

    async def host():
        play.reset_program()

    with pytest.raises(RuntimeError, match="inside a running event loop"):
        asyncio.run(host())
    assert globals_list.program_state is ProgramState.STOPPED

    play.reset_program()
    play.repeat_forever(_stop_on_the_first_frame(heard, "second"))
    play.start_program()

    assert heard == ["first", "second"]


def test_a_stop_in_one_finally_does_not_cut_another_finally_short_during_a_reset():
    ended = []

    @play.when_program_starts
    async def walk():
        try:
            while True:
                await play.animate()
        finally:
            ended.append("finally starts")
            for _ in range(5):
                await play.animate()
            ended.append("finally ends")

    @play.when_program_starts
    async def quitter():
        try:
            while True:
                await play.animate()
        finally:
            await play.animate()
            play.stop_program()

    play.repeat_forever(play.stop_program)
    play.start_program()

    play.reset_program()

    assert ended == ["finally starts", "finally ends"]


@pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
def test_a_task_of_its_own_that_will_not_end_is_closed_quietly_and_the_next_program_runs(
    monkeypatch, caplog
):
    monkeypatch.setattr(play.loop, "_SECONDS_TO_END", 0.05)
    heard = []

    async def stubborn():
        while True:
            try:
                await play.animate()
            except BaseException:
                pass

    play.when_program_starts(lambda: asyncio.ensure_future(stubborn()))
    play.repeat_forever(play.stop_program)
    play.start_program()

    with caplog.at_level(logging.INFO, logger="play"):
        play.reset_program()
        gc.collect()
    play.repeat_forever(_stop_on_the_first_frame(heard, "next"))
    play.start_program()

    assert heard == ["next"]
    assert not [r for r in caplog.records if r.levelno >= logging.INFO]


@pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
def test_a_closed_task_that_fails_later_does_not_stop_the_next_program(
    monkeypatch, caplog
):
    monkeypatch.setattr(play.loop, "_SECONDS_TO_END", 0.05)
    frames = []

    @play.when_program_starts
    async def stubborn():
        try:
            while True:
                try:
                    await play.timer(0.01)
                except asyncio.CancelledError:
                    pass
        finally:
            raise ValueError("a mistake in the cleanup")

    play.repeat_forever(play.stop_program)
    play.start_program()

    with caplog.at_level(logging.INFO, logger="play"):
        play.reset_program()
        gc.collect()
        play.repeat_forever(_stop_on_the_first_frame(frames, "next"))
        play.start_program()

    assert frames == ["next"]
    assert not [r for r in caplog.records if r.levelno >= logging.INFO]


def test_a_task_whose_finally_raises_does_not_keep_the_next_program_from_starting():
    heard = []

    async def helper():
        try:
            while True:
                await play.animate()
        finally:
            raise ValueError("a mistake in the cleanup")

    play.when_program_starts(lambda: asyncio.ensure_future(helper()))
    play.repeat_forever(play.stop_program)
    play.start_program()

    play.reset_program()
    gc.collect()
    play.repeat_forever(_stop_on_the_first_frame(heard, "next"))
    play.start_program()

    assert heard == ["next"]


def test_a_callback_ends_its_finally_block_also_after_an_await_before_the_reset_returns(
    caplog,
):
    log = []

    @play.when_program_starts
    async def walk():
        try:
            while True:
                await play.animate()
        finally:
            log.append("finally starts")
            await play.animate()
            log.append("finally ends")

    play.repeat_forever(play.stop_program)
    play.start_program()

    with caplog.at_level(logging.INFO, logger="play"):
        play.reset_program()

    assert log == ["finally starts", "finally ends"]
    assert not [r for r in caplog.records if r.levelno >= logging.INFO]


def test_a_reset_while_the_program_runs_is_refused_and_changes_nothing():
    refused = []
    frames = []
    box = play.new_box(color="red", width=100, height=100)

    @play.repeat_forever
    def try_to_reset():
        frames.append(1)
        if len(frames) == 1:
            with pytest.raises(RuntimeError, match="inside a running play program"):
                play.reset_program()
            refused.append(globals_list.program_state)
        if len(frames) == 3:
            play.stop_program()

    play.start_program()

    assert refused == [ProgramState.RUNNING]
    assert frames == [1, 1, 1]
    assert globals_list.display.get_at((400, 300))[:3] == (255, 0, 0)
    assert box in globals_list.sprites_group


def test_a_script_that_never_started_does_not_keep_the_next_one_from_starting(
    run_script,
):
    printed = run_script(
        "try:\n"
        "    play.new_circle()\n"
        "    play.when_program_starts(lambda: print('old'))\n"
        "    raise NameError('a typo after new_circle')\n"
        "except NameError:\n"
        "    play.reset_program()\n"
        "\n"
        "@play.when_program_starts\n"
        "def started():\n"
        "    print('started')\n"
        "    os._exit(0)\n"
    )

    assert printed == ["started"]


def test_programs_run_one_after_another_in_a_real_script_without_a_word_logged(
    run_script,
):
    printed = run_script(
        "import gc, logging\n"
        "class Show(logging.Handler):\n"
        "    def emit(self, record):\n"
        "        print('logged:', record.getMessage().replace(' ', '_'))\n"
        "logging.getLogger('play').addHandler(Show())\n"
        "\n"
        "def program(name):\n"
        "    play.new_text(words=name)\n"
        "    @play.when_program_starts\n"
        "    async def walk():\n"
        "        try:\n"
        "            while True:\n"
        "                await play.animate()\n"
        "        finally:\n"
        "            await play.animate()\n"
        "            print(name + '-finally')\n"
        "    @play.repeat_forever\n"
        "    def tick():\n"
        "        print(name)\n"
        "        play.stop_program()\n"
        "    play.start_program()\n"
        "\n"
        "for name in ['first', 'second', 'third']:\n"
        "    program(name)\n"
        "    play.reset_program()\n"
        "    gc.collect()\n"
        "os._exit(0)\n"
    )

    assert printed == [
        "first",
        "first-finally",
        "second",
        "second-finally",
        "third",
        "third-finally",
    ]


@pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
def test_a_task_that_will_not_end_is_closed_quietly_and_the_next_program_runs(
    monkeypatch, caplog
):
    monkeypatch.setattr(play.loop, "_SECONDS_TO_END", 0.05)
    frames = []

    @play.when_program_starts
    async def stubborn():
        while True:
            try:
                await play.animate()
            except BaseException:
                pass

    play.repeat_forever(play.stop_program)
    play.start_program()

    with caplog.at_level(logging.INFO, logger="play"):
        play.reset_program()
    play.repeat_forever(_stop_on_the_first_frame(frames, "next"))
    play.start_program()

    assert frames == ["next"]
    assert not [r for r in caplog.records if r.levelno >= logging.INFO]


def test_a_task_that_waits_on_a_timer_inside_a_bare_except_does_not_hang_the_reset(
    run_script,
):
    printed = run_script(
        "import play.loop\n"
        "play.loop._SECONDS_TO_END = 0.05\n"
        "\n"
        "@play.when_program_starts\n"
        "async def blink():\n"
        "    while True:\n"
        "        try:\n"
        "            await play.timer(0.5)\n"
        "        except:\n"
        "            pass\n"
        "\n"
        "play.repeat_forever(play.stop_program)\n"
        "play.start_program()\n"
        "play.reset_program()\n"
        "print('reset')\n"
        "os._exit(0)\n"
    )

    assert printed == ["reset"]


def test_a_reset_gives_a_debugger_back_its_trace_of_the_script(run_script):
    printed = run_script(
        "import sys\n"
        "lines = []\n"
        "def local(frame, event, arg):\n"
        "    if event == 'line':\n"
        "        lines.append(frame.f_lineno)\n"
        "    return local\n"
        "sys.settrace(lambda frame, event, arg: None)\n"
        "sys._getframe().f_trace = local\n"
        "play.when_program_starts(lambda: None)\n"
        "play.reset_program()\n"
        "before = len(lines)\n"
        "after = len(lines)\n"
        "sys.settrace(None)\n"
        "print(after > before)\n"
        "os._exit(0)\n"
    )

    assert printed == ["True"]


def test_a_reset_turns_off_the_tracing_that_auto_start_turned_on(run_script):
    printed = run_script(
        "import sys\n"
        "play.when_program_starts(lambda: None)\n"
        "print(sys.gettrace() is not None)\n"
        "play.reset_program()\n"
        "print(sys.gettrace() is not None)\n"
        "os._exit(0)\n"
    )

    assert printed == ["True", "False"]


def test_a_click_left_in_the_last_frame_does_not_reach_the_next_programs_widgets():
    play.new_box(x=0, y=0, width=50, height=50)
    play_frames([mouse_move(0, 0)], [mouse_down(0, 0)], then=0)

    play.reset_program()
    box = play.new_checkbox(x=0, y=0, size_px=40)
    box.update()

    assert box.checked is False
