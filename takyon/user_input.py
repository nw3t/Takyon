"""
Track what the user is doing
"""

from .takyon_types import AppContext, SpriteID, RenderingParams
from .takyon_const import WINDOW_H, WINDOW_W
from .interactions import hover_enter_callbacks, hover_exit_callbacks
import sys
import pygame


def handle_pygame_events(context: AppContext) -> None:
    """
    :param context:
    :return:
    """
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.WINDOWRESIZED:
            window_w: int = event.x
            window_h: int = event.y

            scale: int | float = min(window_w / WINDOW_W, window_h / WINDOW_H)
            scaled_canvas_w: int = int(WINDOW_W * scale)
            scaled_canvas_h: int = int(WINDOW_H * scale)

            context.render.display_target = pygame.Rect(
                0, 0, scaled_canvas_w, scaled_canvas_h
            )
            context.render.display_target.center = (window_w // 2, window_h // 2)


def update_hovered_sprites(context: AppContext) -> tuple[set[SpriteID], set[SpriteID]]:
    """
    fetch the lists of all hovered and unhovered sprites
    :param context:
    :return:
    """
    current_hovered = get_hovered_sprites(context)
    previous_hovered = context.game.input_state.hovered_sprites

    entered_sprites = current_hovered - previous_hovered
    exited_sprites = previous_hovered - current_hovered

    context.game.input_state.hovered_sprites = current_hovered

    return entered_sprites, exited_sprites


def user_inputs(context: AppContext) -> None:
    """
    take user inputs and respond
    :param context:
    :return:
    """
    handle_pygame_events(context)
    hover_entered, hover_exited = update_hovered_sprites(context)
    hover_enter_callbacks(context, hover_entered)
    hover_exit_callbacks(context, hover_exited)


def mouse_on_canvas(
    render: RenderingParams,
) -> tuple[int | float, int | float]:
    """
    convert the window mouse to a scaled canvas mouse
    :param render:
    :return:
    """
    raw_mouse_pos: tuple[int, int] = pygame.mouse.get_pos()
    canvas_mouse_x: int | float = (raw_mouse_pos[0] - render.display_target.x) * (
        WINDOW_W / render.display_target.width
    )
    canvas_mouse_y: int | float = (raw_mouse_pos[1] - render.display_target.y) * (
        WINDOW_H / render.display_target.height
    )
    return canvas_mouse_x, canvas_mouse_y


def get_hovered_sprites(context: AppContext) -> set[SpriteID]:
    """
    :param context:
    :return:
    """
    canvas_mouse: tuple[int | float, int | float] = mouse_on_canvas(context.render)
    current_hovered = set()
    for sprite_id, info in context.game.sprites.items():
        if info.interactable and info.rect.collidepoint(canvas_mouse):
            current_hovered.add(sprite_id)
    return current_hovered
