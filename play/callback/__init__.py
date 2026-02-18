"""
This module contains the CallbackManager class and CallbackType enum.
"""

from enum import Enum

from play.callback.callback_helpers import run_callback, run_async_callback


class CallbackType(Enum):
    REPEAT_FOREVER = 0
    WHEN_PROGRAM_START = 1
    PRESSED_KEYS = 2
    RELEASED_KEYS = 3
    WHEN_CLICKED = 4
    WHEN_CLICK_RELEASED = 5
    WHEN_CLICKED_SPRITE = 6
    WHEN_TOUCHING = 7
    WHEN_STOPPED_TOUCHING = 8
    WHEN_TOUCHING_WALL = 9
    WHEN_STOPPED_TOUCHING_WALL = 10
    WHEN_CONTROLLER_BUTTON_PRESSED = 11
    WHEN_CONTROLLER_BUTTON_RELEASED = 12
    WHEN_CONTROLLER_AXIS_MOVED = 13
    WHEN_RESIZED = 14
    WHEN_CLICK_RELEASED_SPRITE = 15


class CallbackManager:
    def __init__(self):
        """
        A class to manage callbacks.
        """
        self.callbacks = {}

    def add_callback(
        self, callback_type, callback, callback_discriminator=None
    ) -> None:
        """
        Add a callback to the callback manager.
        :param callback_type: The type of callback.
        :param callback: The callback function.
        :param callback_discriminator: The discriminator for the callback.
        :return: None
        """
        if not isinstance(callback, tuple):
            callback.type = callback_type
        elif isinstance(callback, tuple):
            callback[0].type = callback_type

        if callback_type not in self.callbacks:
            if callback_discriminator is None:
                self.callbacks[callback_type] = []
            else:
                self.callbacks[callback_type] = {}

        if callback_discriminator is None:
            self.callbacks[callback_type].append(callback)
        else:
            if callback_discriminator not in self.callbacks[callback_type]:
                self.callbacks[callback_type][callback_discriminator] = []
            self.callbacks[callback_type][callback_discriminator].append(callback)

    def remove_callbacks(self, callback_type, callback_discriminator=None) -> None:
        """
        Remove all callbacks of a certain type.
        :param callback_type: The type of callback.
        :param callback_discriminator: The discriminator for the callback.
        :return: None
        """
        if callback_type not in self.callbacks:
            return
        if callback_discriminator is None:
            existing = self.callbacks[callback_type]
            self.callbacks[callback_type] = [] if isinstance(existing, list) else {}
        elif (
            isinstance(self.callbacks[callback_type], dict)
            and callback_discriminator in self.callbacks[callback_type]
        ):
            self.callbacks[callback_type][callback_discriminator] = []

    def get_callbacks(self, callback_type) -> dict:
        """
        Get the callbacks of a certain type.
        :param callback_type: The type of callback.
        :return: The callbacks of the specified type.
        """
        return self.callbacks.get(callback_type, None)

    def get_callback(self, callback_type, callback_discriminator=None) -> callable:
        """
        Get a callback of a certain type.
        :param callback_type: The type of callback.
        :param callback_discriminator: The discriminator for the callback.
        :return: The callback(s) of the specified type.
        """
        if isinstance(callback_type, list):
            callbacks = []
            for ctype in callback_type:
                if ctype in self.callbacks:
                    if callback_discriminator is None:
                        callbacks.extend(self.callbacks[ctype])
                    else:
                        callbacks.extend(
                            self.callbacks[ctype].get(callback_discriminator, [])
                        )
            return callbacks
        if callback_discriminator is None:
            return self.callbacks.get(callback_type, None)
        return self.callbacks.get(callback_type, {}).get(callback_discriminator, None)

    def run_callbacks(
        self,
        callback_type,
        *args,
        callback_discriminator=None,
        **kwargs,
    ):
        """
        Run all callbacks of a certain type with the given arguments.
        :param callback_type: The type of callback.
        :param callback_discriminator: The discriminator for the callback.
        :param args: Positional arguments to pass to the callbacks.
        :param kwargs: Keyword arguments to pass to the callbacks.
        :return: None
        """
        if callback_type not in self.callbacks:
            return

        def is_valid_callback(cb):
            if not callable(cb):
                return False
            if hasattr(cb, "is_running") and cb.is_running:
                return False
            return True

        if callback_discriminator is not None:
            if callback_discriminator not in self.callbacks[callback_type]:
                return

            for callback in self.callbacks[callback_type][callback_discriminator]:
                if is_valid_callback(callback):
                    run_callback(callback, [], [], *args, **kwargs)
        else:
            for callback in self.callbacks[callback_type]:
                if is_valid_callback(callback):
                    run_callback(callback, [], [], *args, **kwargs)

    async def run_callbacks_with_filter(
        self,
        callback_type,
        activated_states,
        *args,
        required_args=None,
        optional_args=None,
        property_filter=None,
    ):
        """
        Run callbacks of a certain type with a specific discriminator.
        :param callback_type: The type of callback.
        :param activated_states: The states to filter by.
        :param required_args: The required arguments for the callback.
        :param optional_args: The optional arguments for the callback.
        :param property_filter: A dictionary of properties to filter the callbacks. For example, {'controller': 0}.
        :return: None
        """
        if required_args is None:
            required_args = []
        if optional_args is None:
            optional_args = []
        if property_filter is None:
            property_filter = {}

        def is_valid_callback(cb):
            if not callable(cb):
                return False
            if hasattr(cb, "is_running") and cb.is_running:
                return False

            if property_filter:
                for key, value in property_filter.items():
                    if value != "any" and getattr(cb, key, None) != value:
                        return False

            return True

        if not activated_states or not self.get_callbacks(callback_type):
            return

        subscriptions = self.get_callbacks(callback_type)
        for state in activated_states:
            for callback in subscriptions.get(state, []):
                if is_valid_callback(callback):
                    await run_async_callback(
                        callback, required_args, optional_args, state, *args
                    )
            for callback in subscriptions.get("any", []):
                if is_valid_callback(callback):
                    await run_async_callback(
                        callback, required_args, optional_args, state, *args
                    )
        all_hash = hash(frozenset(activated_states))
        for callback in subscriptions.get(all_hash, []):
            if is_valid_callback(callback):
                await run_async_callback(
                    callback,
                    required_args,
                    optional_args,
                    activated_states,
                    *args,
                )


callback_manager = CallbackManager()
