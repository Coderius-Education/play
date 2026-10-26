"""The callback manager keeps every event callback, sorted by type and key."""

import asyncio

import pytest

import play
from play.callback import CallbackManager, CallbackType


async def _noop():
    """A callback that does nothing."""


async def _other():
    """A second callback that does nothing, told apart from _noop."""


@pytest.fixture
def manager():
    """An empty callback manager of its own."""
    return CallbackManager()


def _run(coroutine):
    """Run *coroutine* to the end on a loop of its own."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coroutine)
    finally:
        loop.close()


def test_callbacks_are_kept_per_type_and_key(manager):
    manager.add_callback(CallbackType.PRESSED_KEYS, _noop, "space")
    manager.add_callback(CallbackType.PRESSED_KEYS, _other, "a")
    manager.add_callback(CallbackType.REPEAT_FOREVER, _other)

    assert manager.get_callback(CallbackType.PRESSED_KEYS, "space") == [_noop]
    assert manager.get_callback(CallbackType.PRESSED_KEYS, "b") is None
    assert manager.get_callback(CallbackType.REPEAT_FOREVER) == [_other]
    assert manager.get_callbacks(CallbackType.PRESSED_KEYS) == {
        "space": [_noop],
        "a": [_other],
    }
    assert manager.get_callbacks(CallbackType.WHEN_RESIZED) is None


def test_get_callback_of_several_types_lists_them_all_in_order(manager):
    manager.add_callback(CallbackType.WHEN_PROGRAM_START, _noop)
    manager.add_callback(CallbackType.REPEAT_FOREVER, _other)

    callbacks = manager.get_callback(
        [
            CallbackType.WHEN_PROGRAM_START,
            CallbackType.WHEN_RESIZED,
            CallbackType.REPEAT_FOREVER,
        ]
    )

    assert callbacks == [_noop, _other]


def test_a_callback_is_marked_with_its_type(manager):
    manager.add_callback(CallbackType.WHEN_CLICKED, _noop)

    assert _noop.type is CallbackType.WHEN_CLICKED


def test_the_first_callback_tells_the_manager_owner(manager):
    told = []
    manager.on_first_callback = lambda: told.append(True)

    manager.add_callback(CallbackType.REPEAT_FOREVER, _noop)

    assert told == [True]


def test_remove_callbacks_empties_one_key_and_leaves_the_others(manager):
    manager.add_callback(CallbackType.PRESSED_KEYS, _noop, "space")
    manager.add_callback(CallbackType.PRESSED_KEYS, _other, "a")

    manager.remove_callbacks(CallbackType.PRESSED_KEYS, "space")
    manager.remove_callbacks(CallbackType.WHEN_RESIZED)

    assert manager.get_callback(CallbackType.PRESSED_KEYS, "space") == []
    assert manager.get_callback(CallbackType.PRESSED_KEYS, "a") == [_other]


def test_take_callbacks_on_removes_only_those_aimed_at_the_target(manager):
    target, bystander = object(), object()
    manager.add_callback(CallbackType.WHEN_TOUCHING, (_noop, target), "key")
    manager.add_callback(CallbackType.WHEN_TOUCHING, (_other, bystander), "key")

    taken = manager.take_callbacks_on(CallbackType.WHEN_TOUCHING, "key", target)

    assert taken == [_noop]
    assert manager.get_callback(CallbackType.WHEN_TOUCHING, "key") == [
        (_other, bystander)
    ]


def test_run_callbacks_inline_runs_them_in_order_before_returning(manager):
    order = []

    async def first():
        order.append("first")

    async def second():
        order.append("second")

    manager.add_callback(CallbackType.REPEAT_FOREVER, first)
    manager.add_callback(CallbackType.REPEAT_FOREVER, second)
    manager.add_callback(CallbackType.WHEN_PROGRAM_START, second)

    _run(manager.run_callbacks_inline(CallbackType.REPEAT_FOREVER))

    assert order == ["first", "second"]


def test_run_callbacks_inline_of_a_type_without_callbacks_runs_nothing(manager):
    ran = []

    async def other_type():
        ran.append(True)

    manager.add_callback(CallbackType.REPEAT_FOREVER, other_type)

    _run(manager.run_callbacks_inline(CallbackType.WHEN_RESIZED))

    assert ran == []


def test_run_callbacks_inline_skips_a_callback_that_is_still_running(manager):
    ran = []

    async def busy():
        ran.append(True)

    busy.is_running = True
    manager.add_callback(CallbackType.REPEAT_FOREVER, busy)

    _run(manager.run_callbacks_inline(CallbackType.REPEAT_FOREVER))

    assert ran == []


def test_a_callback_added_while_the_game_runs_runs_in_the_next_frames():
    ran = []

    async def added_later():
        ran.append(True)

    @play.when_program_starts
    def setup():
        play.callback.callback_manager.add_callback(
            CallbackType.REPEAT_FOREVER, added_later
        )

    frames = []

    @play.repeat_forever
    def count():
        frames.append(1)
        if len(frames) == 5:
            play.stop_program()

    play.start_program()

    assert ran == [True] * 5


def test_run_callbacks_starts_each_callback_but_skips_one_still_running():
    ran = []

    async def listener():
        ran.append("listener")

    async def busy():
        ran.append("busy")

    busy.is_running = True
    manager = play.callback.callback_manager
    manager.add_callback(CallbackType.WHEN_RESIZED, listener)
    manager.add_callback(CallbackType.WHEN_RESIZED, busy)

    @play.when_program_starts
    async def fire():
        manager.run_callbacks(CallbackType.WHEN_RESIZED)
        await play.animate()
        play.stop_program()

    play.start_program()

    assert ran == ["listener"]
