"""
Draw to the screen
"""

from .const import SHADOW_OFFSET, BLACK, TYPE_Z_LAYERS, SEE_THROUGH_TEXTURES, TOOLTIP_OFFSET_X, TOOLTIP_OFFSET_Y, TOOLTIP_CLAMP_MARGIN
from .types import AppContext, SpriteType
from .user_input import mouse_on_canvas
from itertools import count
import pygame


def draw_active_tooltip(context: AppContext) -> None:
    """
    :param context:
    :return:
    """
    tooltip = context.game.input_state.active_tooltip
    if tooltip is None:
        return

    canvas_mouse = mouse_on_canvas(context.render)
    mouse_x, mouse_y = canvas_mouse

    rect = tooltip.get_rect(
        topleft=(mouse_x + TOOLTIP_OFFSET_X, mouse_y + TOOLTIP_OFFSET_Y)
    )

    # flipflop left and right to avoid going off the screen
    canvas_rect = context.render.canvas.get_rect()
    if rect.right > canvas_rect.right:
        rect.right = mouse_x - TOOLTIP_CLAMP_MARGIN
    if rect.bottom > canvas_rect.bottom:
        rect.bottom = mouse_y - TOOLTIP_CLAMP_MARGIN

    context.render.canvas.blit(tooltip, rect)
def render_text_with_shadow(
    font: pygame.font.Font, text: str, fg: pygame.Color, shadow: pygame.Color
) -> pygame.Surface:
    """
    Helper function for making drop shadow text
    :param font:
    :param text:
    :param fg:
    :param shadow:
    :return:
    """
    shadow_surf = font.render(text, True, shadow)
    shadow_surf = pygame.transform.gaussian_blur(shadow_surf, SHADOW_OFFSET)
    main_surf = font.render(text, True, fg)

    composite = pygame.Surface(
        (main_surf.get_width() + SHADOW_OFFSET, main_surf.get_height() + SHADOW_OFFSET),
        pygame.SRCALPHA,
    )
    composite.blit(shadow_surf, (SHADOW_OFFSET, SHADOW_OFFSET))
    composite.blit(main_surf, (0, 0))
    return composite


def render_sprites(context: AppContext) -> None:
    """
    Run through the sprites in the game and blit them
    :param context:
    :return:
    """
    for sprite_info in context.game.sprites.values():
        sprite_info.render_count = None
    render_count: count = count(0)

    context.render.window.fill(BLACK)
    # everything that's not a stone gets blitted in order of the TYPE_Z_LAYERS dict
    non_stones = (
        s for s in context.game.sprites.values() if s.type != SpriteType.STONE
    )

    for sprite_info in sorted(
        non_stones, key=lambda s: (TYPE_Z_LAYERS[s.type], s.z_order)
    ):
        rect: pygame.Rect = sprite_info.rect
        sprite: pygame.Surface = sprite_info.sprite
        sprite_info.render_count = next(render_count)
        context.render.canvas.blit(sprite, rect)

    # stones fetched from the board will be in lists of 1-8 members and only the top two will ever be blitted
    for sprite_list in context.game.board.values():
        if not sprite_list:
            continue
        top = sprite_list[-1]
        second = sprite_list[-2] if len(sprite_list) >= 2 else None

        if second and top.texture in SEE_THROUGH_TEXTURES:
            second.render_count = next(render_count)
            context.render.canvas.blit(second.sprite, second.rect)
        top.render_count = next(render_count)
        context.render.canvas.blit(top.sprite, top.rect)

    draw_active_tooltip(context)

    # virtual canvas scaling, maybe i wanna move all three sections of this into their own functions?
    scaled_canvas: pygame.Surface = pygame.transform.scale(
        context.render.canvas,
        (context.render.display_target.width, context.render.display_target.height),
    )

    context.render.window.blit(scaled_canvas, context.render.display_target)
    pygame.display.flip()
    context.render.clock_tick = context.render.clock.tick(60)
