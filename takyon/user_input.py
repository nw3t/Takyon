"""
Track what the user is doing
"""

from .types import AppContext, SpriteID, RenderingParams, InteractionType, SpriteInfo
from .const import WINDOW_H, WINDOW_W, MOUSE_BINDINGS
from .interactions import (
    INTERACTION_CALLBACKS,
    Interactable,
    hover_enter_callbacks,
    hover_exit_callbacks,
)
import pygame


def get_top_sprite(context: AppContext, sprites: set[SpriteID]) -> SpriteID | None:
    """
    from our set of sprites, return the one with the highest render_count if any
    :param context:
    :param sprites:
    :return:
    """
    highest: SpriteID | None = None
    render_count: int | None = None
    for sprite_id in sprites:
        sprite = context.game.sprites[sprite_id]
        if sprite.render_count is None:
            continue
        if highest is None:
            highest = sprite_id
            render_count = sprite.render_count
        elif sprite.render_count > render_count:
            highest = sprite_id
            render_count = sprite.render_count
    return highest


def handle_pygame_events(context: AppContext) -> bool:
    """
    :param context:
    :return:
    """
    running = True
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONUP:
            sprites: set[SpriteID] = get_hovered_sprites(context)
            interaction: InteractionType | None = MOUSE_BINDINGS.get(event.button)
            if interaction is None:
                continue
            top_sprite: SpriteID | None = get_top_sprite(context, sprites)
            if top_sprite is None:
                continue
            click_match = top_sprite == context.game.input_state.clicked_down_sprite
            context.game.input_state.clicked_down_sprite = None
            if not click_match:
                continue
            interactable = context.game.sprites[top_sprite].interactable
            if interactable is None:
                continue
            callback = INTERACTION_CALLBACKS.get((interactable, interaction))
            if callback is not None:
                callback(context, top_sprite)

        if event.type == pygame.MOUSEBUTTONDOWN:
            sprites: set[SpriteID] = get_hovered_sprites(context)
            interaction: InteractionType | None = MOUSE_BINDINGS.get(event.button)
            if interaction is None:
                continue
            top_sprite: SpriteID | None = get_top_sprite(context, sprites)
            context.game.input_state.clicked_down_sprite = top_sprite

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

    return running


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


def user_inputs(context: AppContext) -> bool:
    """
    take user inputs and respond
    :param context:
    :return:
    """
    running = handle_pygame_events(context)
    hover_entered, hover_exited = update_hovered_sprites(context)
    hover_enter_callbacks(context, hover_entered)
    hover_exit_callbacks(context, hover_exited)
    return running


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
