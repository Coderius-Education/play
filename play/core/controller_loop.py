"""This module contains the controller loop, which handles controller events in the game loop."""

from collections import defaultdict
import pygame

from ..callback import callback_manager, CallbackType


class ControllerState:
    """Class to manage the state of the controller."""

    def __init__(self):
        self.buttons_pressed = defaultdict(set)
        self.buttons_released = defaultdict(set)
        self.axes_moved = defaultdict(list)

    def clear(self):
        """Clear the controller state for the next frame."""
        # on purpose: buttons pressed is not cleared to be able
        # to have event each time that button is held
        # self.buttons_pressed.clear()
        self.buttons_released.clear()
        self.axes_moved.clear()

    def any(self):
        """Check if any controller event has occurred."""
        return self.buttons_pressed or self.buttons_released or self.axes_moved


controller_state = ControllerState()


def handle_controller_events(event):
    """Handle controller events in the game loop.
    :param event: The event to handle."""
    if event.type == pygame.JOYAXISMOTION:  # pylint: disable=no-member
        controller_state.axes_moved[event.instance_id].append(
            {"axis": event.axis, "value": round(event.value)}
        )
    if event.type == pygame.JOYBUTTONDOWN:  # pylint: disable=no-member
        controller_state.buttons_pressed[event.instance_id].add(event.button)
    if event.type == pygame.JOYBUTTONUP:
        controller_state.buttons_released[event.instance_id].add(event.button)
        if event.button in controller_state.buttons_pressed:
            controller_state.buttons_pressed[event.instance_id].remove(event.button)


async def handle_controller():  # pylint: disable=too-many-branches
    """Handle controller events in the game loop."""
    ############################################################
    # @controller.when_button_pressed and @controller.when_any_button_pressed
    ############################################################
    if controller_state.buttons_pressed:
        for controller_id, buttons in controller_state.buttons_pressed.items():
            await callback_manager.run_callbacks_with_filter(
                callback_type=CallbackType.WHEN_CONTROLLER_BUTTON_PRESSED,
                activated_states=buttons,
                required_args=["button"],
                property_filter={"controller": controller_id},
            )

    ############################################################
    # @controller.when_button_released
    ############################################################
    if controller_state.buttons_released:
        for controller_id, buttons in controller_state.buttons_released.items():
            await callback_manager.run_callbacks_with_filter(
                callback_type=CallbackType.WHEN_CONTROLLER_BUTTON_RELEASED,
                activated_states=buttons,
                required_args=["button"],
                property_filter={"controller": controller_id},
            )
        controller_state.buttons_released.clear()

    ############################################################
    # @controller.when_axis_moved
    ############################################################
    if controller_state.axes_moved:
        for axes_events in controller_state.axes_moved.values():
            for axis_event in axes_events:
                await callback_manager.run_callbacks_with_filter(
                    CallbackType.WHEN_CONTROLLER_AXIS_MOVED,  # callback type
                    [axis_event["axis"]],  # activated states
                    axis_event["value"],  # value
                    required_args=["axis", "value"],
                    property_filter={"axis": axis_event["axis"]},
                )
        controller_state.axes_moved.clear()
