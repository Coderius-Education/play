"""This module contains the function that simulates the physics of the game"""

from play.core.sprites_loop import handle_new_contacts
from play.globals import globals_list
from play.physics import physics_space


async def simulate_physics():
    """
    Simulate the physics of the game
    """
    # more steps means more accurate simulation but more processing time
    for _ in range(globals_list.num_sim_steps):
        physics_space.step(1 / (globals_list.frame_rate * globals_list.num_sim_steps))
        await handle_new_contacts()
