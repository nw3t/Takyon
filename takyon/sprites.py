"""
Making and destroying sprites
"""

from .types import (
    AppContext,
    Interactable,
    Player,
    SpriteID,
    SpriteInfo,
    SpriteType,
)
from .const import NEXT_ID, Texture
import pygame


def spawn_from_surface(
    context: AppContext,
    sprite_type: SpriteType,
    surface: pygame.Surface,
    rect: pygame.Rect,
    z_order: int = 0,
    player: Player | None = None,
    interactable: Interactable | None = None,
    tooltip: str | None = None,
) -> SpriteID:
    """
    If the sprite has its own generated surface instead of a texture map
    :param context:
    :param sprite_type:
    :param surface:
    :param rect:
    :param z_order:
    :param player:
    :param interactable:
    :param tooltip:
    :return:
    """
    sprite_id = SpriteID(next(NEXT_ID))
    info = SpriteInfo(
        sprite_type,
        surface,
        rect,
        texture=None,
        z_order=z_order,
        player=player,
        interactable=interactable,
        tooltip=tooltip,
    )
    context.game.sprites[sprite_id] = info
    context.game.sprites_by_type[sprite_type].add(info)
    return sprite_id


def spawn(
    context: AppContext,
    sprite_type: SpriteType,
    texture: Texture,
    rect: pygame.Rect,
    z_order: int = 0,
    player: Player | None = None,
    interactable: Interactable | None = None,
    tooltip: str | None = None,
) -> SpriteID:
    """
    Use this to make new sprites, no other constructor
    :param context:
    :param sprite_type:
    :param texture:
    :param rect:
    :param z_order:
    :param player:
    :param interactable:
    :param tooltip:
    :return:
    """
    sprite_id: SpriteID = SpriteID(next(NEXT_ID))
    scaled_sprite = pygame.transform.scale(context.render.textures[texture], rect.size)
    info: SpriteInfo = SpriteInfo(
        sprite_type,
        scaled_sprite,
        rect,
        texture,
        z_order,
        player,
        interactable,
        tooltip,
    )
    context.game.sprites[sprite_id] = info
    context.game.sprites_by_type[sprite_type].add(info)
    return sprite_id


def despawn(context: AppContext, sprite_id: SpriteID) -> None:
    """
    Kill a sprite
    :param context:
    :param sprite_id:
    :return:
    """
    context.game.sprites[sprite_id].kill()
    del context.game.sprites[sprite_id]
