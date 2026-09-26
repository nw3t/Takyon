"""
For all our mouse magic
"""

from .types import (
    AppContext,
    Interactable,
    InteractionCallback,
    InteractionType,
    SpriteID,
)
import pygame


def hover_enter_callbacks(
    context: AppContext,
    entered_sprites: set[SpriteID],
) -> None:
    """
    Go through all the sprites hovered this frame and call their callbacks
    :param context:
    :param entered_sprites:
    :return:
    """
    for sprite_id in entered_sprites:
        interactable = context.game.sprites[sprite_id].interactable
        if interactable:
            callback = INTERACTION_CALLBACKS.get(
                (interactable, InteractionType.HOVER_ENTER)
            )
            if callback:
                callback(context, sprite_id)


def hover_exit_callbacks(
    context: AppContext,
    exited_sprites: set[SpriteID],
) -> None:
    """
    Go through all the sprites exited this frame and call their callbacks
    :param context:
    :param exited_sprites:
    :return:
    """
    for sprite_id in exited_sprites:
        interactable = context.game.sprites[sprite_id].interactable
        if interactable:
            callback = INTERACTION_CALLBACKS.get(
                (interactable, InteractionType.HOVER_EXIT)
            )
            if callback:
                callback(context, sprite_id)


def queue_pending_tooltip(context: AppContext, sprite_id: SpriteID) -> None:
    """
    push a tooltip into the queue to render after a timer has elapsed
    :return:
    """
    context.game.input_state.pending_tooltip_sprite = sprite_id
    context.game.input_state.hover_start_time = pygame.time.get_ticks()
    context.game.input_state.active_tooltip_sprite = None
    context.game.input_state.active_tooltip = None


def clear_pending_tooltips(context: AppContext, sprite_id: SpriteID) -> None:
    """
    reset the queue on hover exit
    :return:
    """
    if context.game.input_state.pending_tooltip_sprite == sprite_id:
        context.game.input_state.pending_tooltip_sprite = None
    if context.game.input_state.active_tooltip_sprite == sprite_id:
        context.game.input_state.active_tooltip_sprite = None
        context.game.input_state.active_tooltip = None


def spawn_stone_at_mouse(_context: AppContext, _sprite_id: SpriteID) -> None:
    """
    Passed as a callback to put a white or black stone in your hand, if one's already in your hand, put it back
    :return:
    """
    print("I got triggered!")


def spawn_capstone_at_mouse(_context: AppContext, _sprite_id: SpriteID) -> None:
    """
    Passed as a callback to put a white or black stone in your hand, if one's already in your hand, put it back
    :return:
    """


def show_tile_stack(_context: AppContext, _sprite_id: SpriteID) -> None:
    """
    Passed as a callback to show the tile's side view
    :return:
    """


def hide_tile_stack(_context: AppContext, _sprite_id: SpriteID) -> None:
    """
    Passed as a callback to hide the tile's sideview
    :return:
    """


def drop_tiles_along_drag(_context: AppContext, _sprite_id: SpriteID) -> None:
    """
    Passed as a callback to drop one tile at a time in a straight line
    :return:
    """


def drop_all_tiles(_context: AppContext, _sprite_id: SpriteID) -> None:
    """
    Passed as a callback to drop everything in your hand
    :return:
    """


def flatten_tiles_along_drag(_context: AppContext, _sprite_id: SpriteID) -> None:
    """
    Passed as a callback to super drag - intentionally flatten with your capstones if possible
    :return:
    """


def drop_and_flatten_all_tiles(_context: AppContext, _sprite_id: SpriteID) -> None:
    """
    Passed as a callback to super drop - intentionally flatten with your capstones if possible
    :return:
    """


#####################
# Big map of all the types to their callbacks
INTERACTION_CALLBACKS: dict[
    tuple[Interactable, InteractionType], InteractionCallback
] = {
    (Interactable.STONE_BAG, InteractionType.LEFT_CLICK): spawn_stone_at_mouse,
    (Interactable.STONE_BAG, InteractionType.RIGHT_CLICK): spawn_capstone_at_mouse,
    (Interactable.STONE_BAG, InteractionType.HOVER_ENTER): queue_pending_tooltip,
    (Interactable.STONE_BAG, InteractionType.HOVER_EXIT): clear_pending_tooltips,
    (Interactable.STONE_COUNTER, InteractionType.HOVER_ENTER): queue_pending_tooltip,
    (Interactable.STONE_COUNTER, InteractionType.HOVER_EXIT): clear_pending_tooltips,
    (Interactable.CLOCK, InteractionType.HOVER_ENTER): queue_pending_tooltip,
    (Interactable.CLOCK, InteractionType.HOVER_EXIT): clear_pending_tooltips,
    (Interactable.TILE, InteractionType.HOVER_ENTER): show_tile_stack,
    (Interactable.TILE, InteractionType.HOVER_EXIT): hide_tile_stack,
    (Interactable.TILE, InteractionType.LEFT_DRAG_START): drop_tiles_along_drag,
    (Interactable.TILE, InteractionType.LEFT_DRAG_STOP): drop_all_tiles,
    (Interactable.TILE, InteractionType.RIGHT_DRAG_START): flatten_tiles_along_drag,
    (Interactable.TILE, InteractionType.RIGHT_DRAG_STOP): drop_and_flatten_all_tiles,
}
