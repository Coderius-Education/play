"""This module contains the controller loop, which handles controller events in the game loop."""

import pygame

from ..callback import callback_manager, CallbackType
from ..io.controllers import (
    controllers,
)


class ControllerState:
    """Class to manage the state of the controller."""

    axis_moved = False
    button_pressed = False
    button_released = False

    def clear(self):
        """Clear the controller state for the next frame."""
        self.axis_moved = False
        self.button_pressed = False
        self.button_released = False

    def any(self):
        """Check if any controller event has occurred."""
        return self.axis_moved or self.button_pressed or self.button_released


controller_state = ControllerState()


def handle_controller_events(event):
    """Handle controller events in the game loop.
    :param event: The event to handle."""
    if event.type == pygame.JOYAXISMOTION:  # pylint: disable=no-member
        controller_state.axis_moved = True
    if event.type == pygame.JOYBUTTONDOWN:  # pylint: disable=no-member
        controller_state.button_pressed = True
    if event.type == pygame.JOYBUTTONUP:
        controller_state.button_released = True


async def handle_controller():  # pylint: disable=too-many-branches
    """Handle controller events in the game loop."""
    ############################################################
    # @controller.when_button_pressed and @controller.when_any_button_pressed
    ############################################################
    if controller_state.button_pressed:
        for controller in controllers.get_controllers():
            controller_buttons_pressed = controllers.get_controller(
                controller
            ).get_buttons_pressed()
            callback_manager.run_callbacks_with_filter(
                CallbackType.WHEN_CONTROLLER_BUTTON_PRESSED,
                controller_buttons_pressed,
                ["button_number"],
                [],
                {"controller": controller},
            )
        controller_state.button_pressed = False

    ############################################################
    # @controller.when_button_released
    ############################################################
    if controller_state.button_released:
        for controller in controllers.get_controllers():
            controller_buttons_released = controllers.get_controller(
                controller
            ).get_buttons_released()
            callback_manager.run_callbacks_with_filter(
                CallbackType.WHEN_CONTROLLER_BUTTON_RELEASED,
                controller_buttons_released,
                ["button_number"],
                [],
                {"controller": controller},
            )
        controller_state.button_released = False
    ############################################################
    # @controller.when_axis_moved
    ############################################################
    if controller_state.axis_moved:
        for controller in controllers.get_controllers():
            controller_axis_moved = controllers.get_controller(
                controller
            ).get_axis_moved()
            callback_manager.run_callbacks_with_filter(
                CallbackType.WHEN_CONTROLLER_AXIS_MOVED,
                controller_axis_moved,
                ["axis_number", "value"],
                [],
                {"controller": controller},
            )
        controller_state.axis_moved = False
