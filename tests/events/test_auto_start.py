"""Tests for auto-starting when user forgets to call play.start_program()."""

from unittest.mock import patch


def test_auto_start_flag_set_by_callback():
    """Test that adding a callback sets _should_auto_start."""
    from play.api import utils
    from play.callback import callback_manager, CallbackType

    utils._program_started = False
    utils._should_auto_start = False
    callback_manager.on_first_callback = utils._schedule_auto_start

    async def dummy():
        pass

    callback_manager.add_callback(CallbackType.WHEN_PROGRAM_START, dummy)
    assert utils._should_auto_start is True
    assert callback_manager.on_first_callback is None

    callback_manager.remove_callbacks(CallbackType.WHEN_PROGRAM_START)
    callback_manager.on_first_callback = utils._schedule_auto_start
    utils._should_auto_start = False
    utils._program_started = False


def test_auto_start_flag_set_by_sprite():
    """Test that creating a real Sprite subclass sets _should_auto_start."""
    from play.api import utils
    from play.globals import globals_list
    import play

    utils._program_started = False
    utils._should_auto_start = False
    globals_list.on_first_sprite = utils._schedule_auto_start

    box = play.new_box()

    assert utils._should_auto_start is True
    assert globals_list.on_first_sprite is None

    box.remove()
    globals_list.on_first_sprite = utils._schedule_auto_start
    utils._should_auto_start = False
    utils._program_started = False


def test_on_main_return_calls_start_program():
    """Test that _on_main_return calls start_program when flag is set."""
    from play.api import utils

    utils._program_started = False
    utils._should_auto_start = True

    with patch.object(utils, "start_program") as mock_start:
        utils._on_main_return(None, "return", None)  # noqa: E501
        mock_start.assert_called_once()

    utils._should_auto_start = False
    utils._program_started = False


def test_on_main_return_skipped_when_already_started():
    """Test that _on_main_return does nothing if already started."""
    from play.api import utils

    utils._program_started = True
    utils._should_auto_start = True

    with patch.object(utils, "start_program") as mock_start:
        utils._on_main_return(None, "return", None)  # noqa: E501
        mock_start.assert_not_called()

    utils._should_auto_start = False
    utils._program_started = False


def test_on_main_return_skipped_when_flag_not_set():
    """Test that _on_main_return does nothing if no callbacks/sprites were registered."""
    from play.api import utils

    utils._program_started = False
    utils._should_auto_start = False

    with patch.object(utils, "start_program") as mock_start:
        utils._on_main_return(None, "return", None)  # noqa: E501
        mock_start.assert_not_called()

    utils._program_started = False


def test_on_main_return_ignores_non_return_events():
    """Test that _on_main_return only triggers on 'return' events."""
    from play.api import utils

    utils._program_started = False
    utils._should_auto_start = True

    with patch.object(utils, "start_program") as mock_start:
        utils._on_main_return(None, "call", None)  # noqa: E501
        utils._on_main_return(None, "line", None)  # noqa: E501
        mock_start.assert_not_called()

    utils._should_auto_start = False
    utils._program_started = False


def test_start_program_clears_auto_start_flag():
    """Test that start_program() clears _should_auto_start."""
    from play.api import utils

    utils._program_started = False
    utils._should_auto_start = True

    with patch.object(utils, "_get_loop"):
        utils.start_program()

    assert utils._should_auto_start is False

    utils._program_started = False
