#!/usr/bin/env python
"""**Takyon by Woland**

Rules of Tak go here eventually <

**Art creds:**

**Arabesque Design on Dark Ground**
Virgil Solis German
*1534–1562*

**Dark Grey Leather Handbag By Saber Handbags**
This file was contributed to Wikimedia Commons by Missouri Historical
Society as part of a cooperation project. The donation was facilitated by the
Digital Public Library of America. Record in source
*catalogDPLA identifier: f676934219011ac2ae4eb524dad7cd15
Missouri Historical Society identifier: 2000-018-0089, No restrictions*
"""

from .takyon_init import initialize_takyon_context
from .takyon_render import render_sprites
from .takyon_types import AppContext
from .takyon_ui import spawn_board
from .takyon_ui import update_clocks, update_tooltips
from .user_input import user_inputs
import pygame


#####################
# ENTRY POINT HERE BAYBEEEEE
#####################
def main():
    """
    Let's play Tak
    """
    pygame.init()
    app_context = initialize_takyon_context()
    spawn_board(app_context)
    game_loop(app_context)


def game_loop(
    context: AppContext,
) -> None:
    """
    main game loop silly
    :param context:
    :return:
    """
    while True:
        update_clocks(context)
        user_inputs(context)
        update_tooltips(context)
        render_sprites(context)


if __name__ == "__main__":
    main()
