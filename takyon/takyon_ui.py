"""
Do shenanigans here that draw and interact with UI buttons on the screen
This will often mix game state and rendering I understand...
I guess we deal with it. This module sets up the board and spawns game pieces
"""

from .takyon_types import AppContext, Interactable, Player, SpriteID, SpriteType
from .takyon_const import (
    BAG_TOOLTIP,
    BOARD_SIZE,
    CHARCOAL,
    CHARCOAL_ALPHA,
    CLOCK_OFFSET,
    CLOCK_START_SECONDS,
    COUNTER_UI_SCALE_RATIO,
    CREAM,
    PIP_CLUSTER,
    PIP_GAP,
    PIP_LINE,
    PIP_OFFSET,
    PIP_SCALE,
    PIP_SPACER,
    SHADOW,
    TILE_SPACER,
    TOOLTIP_DELAY,
    TOOLTIP_PADDING,
    UI_SPACER,
    Texture,
)
from .takyon_render import render_text_with_shadow
from .takyon_sprites import spawn, spawn_from_surface
import pygame


def spawn_stone_counters(
    context: AppContext,
) -> None:
    """
    :param context:
    """
    board_bounds: pygame.Rect = context.render.textures[Texture.BOARD].get_rect()
    board_bounds.center = context.render.canvas.get_rect().center

    counter_scale: int = round(BOARD_SIZE / COUNTER_UI_SCALE_RATIO)

    black_counter_rect: pygame.Rect = pygame.Rect(0, 0, counter_scale, counter_scale)
    white_counter_rect: pygame.Rect = pygame.Rect(0, 0, counter_scale, counter_scale)

    black_counter_rect.bottomleft = board_bounds.move(UI_SPACER, 2 * UI_SPACER).midright
    white_counter_rect.bottomright = board_bounds.move(
        -UI_SPACER, 2 * UI_SPACER
    ).midleft

    spawn(
        context,
        SpriteType.UI,
        Texture.STONE_COUNTER,
        white_counter_rect,
        interactable=Interactable.STONE_COUNTER,
    )
    spawn(
        context,
        SpriteType.UI,
        Texture.STONE_COUNTER,
        black_counter_rect,
        interactable=Interactable.STONE_COUNTER,
    )

    pip_rect_black: pygame.Rect = pygame.Rect(0, 0, PIP_SCALE, PIP_SCALE)
    pip_rect_white: pygame.Rect = pygame.Rect(0, 0, PIP_SCALE, PIP_SCALE)
    pip_rect_black.bottomleft = black_counter_rect.move(PIP_OFFSET).bottomleft
    pip_rect_white.bottomleft = white_counter_rect.move(PIP_OFFSET).bottomleft

    count_and_spawn_pips(context, pip_rect_black, pip_rect_white)


def count_and_spawn_pips(
    context: AppContext,
    pip_rect_black: pygame.Rect,
    pip_rect_white: pygame.Rect,
) -> None:
    """
    spawn all pips aligned on the grid at game start
    :param context:
    :param pip_rect_black:
    :param pip_rect_white:
    :return:
    """

    players = (
        (
            context.game.stone_count.black.stones,
            context.game.stone_count.black.capstones,
            Texture.BLACK_PIP,
            pip_rect_black,
        ),
        (
            context.game.stone_count.white.stones,
            context.game.stone_count.white.capstones,
            Texture.WHITE_PIP,
            pip_rect_white,
        ),
    )

    for stones, capstones, texture, pip_rect in players:
        for pips in range(stones + capstones):

            row: int = pips // PIP_LINE
            col: int = pips % PIP_LINE
            y_movement: int = row * PIP_SPACER
            pip_base_move: int = col * PIP_SPACER
            pip_gap_move: int = (col // PIP_CLUSTER) * PIP_GAP
            x_movement: int = pip_base_move + pip_gap_move

            pip_texture: Texture = texture if pips < stones else Texture.GOLD_PIP

            pip_translation: pygame.Rect = pip_rect.move(x_movement, -y_movement)
            spawn(context, SpriteType.PIP, pip_texture, pip_translation)


def spawn_board(
    context: AppContext,
) -> None:
    """
    Edit this to only spawn the UI
    :param context:
    :return:
    """

    spawn_timers(context)

    board_bounds: pygame.Rect = context.render.textures[Texture.BOARD].get_rect()
    board_bounds.center = context.render.canvas.get_rect().center

    bg_bounds: pygame.Rect = context.render.textures[Texture.BG].get_rect()
    spawn(context, SpriteType.BOARD, Texture.BG, bg_bounds)
    spawn(context, SpriteType.BOARD, Texture.BOARD, board_bounds)

    spawn_stone_counters(context)

    bag_scale: int = BOARD_SIZE // 4
    stone_scale: int = bag_scale // 2
    stone_spacer: int = bag_scale // 4

    right_bag_rect: pygame.Rect = pygame.Rect(0, 0, bag_scale, bag_scale)
    left_bag_rect: pygame.Rect = pygame.Rect(0, 0, bag_scale, bag_scale)
    black_ui_stone: pygame.Rect = pygame.Rect(0, 0, stone_scale, stone_scale)
    white_ui_stone: pygame.Rect = pygame.Rect(0, 0, stone_scale, stone_scale)

    left_bag_rect.topright = board_bounds.move(-UI_SPACER, 0).topleft
    right_bag_rect.topleft = board_bounds.move(UI_SPACER, 0).topright
    spawn(
        context,
        SpriteType.UI,
        Texture.STONE_BAG,
        left_bag_rect,
        interactable=Interactable.STONE_BAG,
        tooltip=BAG_TOOLTIP,
    )
    spawn(
        context,
        SpriteType.UI,
        Texture.STONE_BAG,
        right_bag_rect,
        interactable=Interactable.STONE_BAG,
        tooltip=BAG_TOOLTIP,
    )

    black_ui_stone.center = right_bag_rect.move(0, -stone_spacer).center
    white_ui_stone.center = left_bag_rect.move(0, -stone_spacer).center
    spawn(
        context,
        SpriteType.UI,
        Texture.BLACK_FLAT,
        black_ui_stone,
    )
    spawn(
        context,
        SpriteType.UI,
        Texture.WHITE_FLAT,
        white_ui_stone,
    )

    dimension = context.game.dimension

    tile_size = (BOARD_SIZE - (dimension + 2) * TILE_SPACER) // dimension
    tile_rect: pygame.Rect = pygame.Rect(0, 0, tile_size, tile_size)
    tile_rect.topleft = board_bounds.topleft
    for col in range(dimension):
        for row in range(dimension):
            spawn(
                context,
                SpriteType.TILE,
                Texture.TILE,
                tile_rect.move(
                    TILE_SPACER + (tile_size + TILE_SPACER) * col,
                    TILE_SPACER + (tile_size + TILE_SPACER) * row,
                ),
                interactable=Interactable.TILE,
            )


def spawn_timers(context: AppContext) -> None:
    """
    :param context:
    :return:
    """
    board_bounds: pygame.Rect = context.render.textures[Texture.BOARD].get_rect()
    board_bounds.center = context.render.canvas.get_rect().center

    clock_scale: int = round(BOARD_SIZE / COUNTER_UI_SCALE_RATIO)

    black_clock_rect: pygame.Rect = pygame.Rect(0, 0, clock_scale, clock_scale)
    white_clock_rect: pygame.Rect = pygame.Rect(0, 0, clock_scale, clock_scale)

    black_clock_rect.topleft = board_bounds.move(UI_SPACER, 0).midright
    white_clock_rect.topright = board_bounds.move(-UI_SPACER, 0).midleft

    spawn(
        context,
        SpriteType.UI,
        Texture.BLACK_CLOCK,
        black_clock_rect,
        interactable=Interactable.CLOCK,
    )
    spawn(
        context,
        SpriteType.UI,
        Texture.WHITE_CLOCK,
        white_clock_rect,
        interactable=Interactable.CLOCK,
    )

    minutes, seconds = divmod(CLOCK_START_SECONDS, 60.0)
    text = f"{int(minutes):02d}:{int(seconds):02d}"
    white_clock_text: pygame.Surface = render_text_with_shadow(
        context.render.ui_info.clock_font, text, CHARCOAL, SHADOW
    )
    black_clock_text: pygame.Surface = render_text_with_shadow(
        context.render.ui_info.clock_font, text, CREAM, SHADOW
    )

    black_text_rect = black_clock_text.get_rect()
    white_text_rect = white_clock_text.get_rect()
    black_text_rect.midbottom = black_clock_rect.move(0, CLOCK_OFFSET).midbottom
    white_text_rect.midbottom = white_clock_rect.move(0, CLOCK_OFFSET).midbottom

    spawn_from_surface(
        context,
        SpriteType.CLOCK,
        black_clock_text,
        black_text_rect,
        player=Player.BLACK,
    )
    spawn_from_surface(
        context,
        SpriteType.CLOCK,
        white_clock_text,
        white_text_rect,
        player=Player.WHITE,
    )


def create_tooltip_surface(text: str, font: pygame.font.Font) -> pygame.Surface:
    """Padded grey tooltips - this needs a refactor to remove magic numbers and clean up"""
    padding = TOOLTIP_PADDING
    text_surf = font.render(text, True, CREAM)

    box_w = text_surf.get_width() + (padding * 2)
    box_h = text_surf.get_height() + (padding * 2)

    tooltip_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    tooltip_surf.fill(CHARCOAL_ALPHA)

    pygame.draw.rect(tooltip_surf, CREAM, tooltip_surf.get_rect(), width=1)
    tooltip_surf.blit(text_surf, (padding, padding))

    return tooltip_surf


def show_tooltip(context: AppContext, sprite_id: SpriteID) -> None:
    """Triggered on HOVER_ENTER: builds and stores tooltip surface."""
    info = context.game.sprites.get(sprite_id)
    if not info or not getattr(info, "tooltip", None):
        return
    context.game.input_state.active_tooltip_sprite = sprite_id
    context.game.input_state.pending_tooltip_sprite = None

    if isinstance(info.tooltip, pygame.Surface):
        context.game.input_state.active_tooltip = info.tooltip
    else:
        context.game.input_state.active_tooltip = (
            create_tooltip_surface(info.tooltip, context.render.ui_info.tooltip_font)
            if info.tooltip
            else None
        )


def update_tooltips(context: AppContext) -> None:
    """
    If the tooltip timer has counted a second, then show tooltips
    :param context:
    :return:
    """
    if context.game.input_state.pending_tooltip_sprite is not None:
        if context.game.input_state.active_tooltip is None:
            time_diff = (
                pygame.time.get_ticks() - context.game.input_state.hover_start_time
            )
            if time_diff > TOOLTIP_DELAY:
                show_tooltip(context, context.game.input_state.pending_tooltip_sprite)


def update_clocks(context: AppContext) -> None:
    """

    :param context:
    :return:
    """
    prev_time = context.game.timer[context.game.active_player]
    next_time = context.game.timer[context.game.active_player] - (
        context.render.clock_tick / 1000.0
    )
    context.game.timer[context.game.active_player] = next_time

    if int(prev_time) != int(next_time):
        for clock in context.game.sprites_by_type[SpriteType.CLOCK]:
            if clock.player == context.game.active_player:
                minutes, seconds = divmod(
                    context.game.timer[context.game.active_player], 60.0
                )
                text = f"{int(minutes):02d}:{int(seconds):02d}"
                match clock.player:
                    case Player.BLACK:
                        old_center = clock.rect.center
                        clock.sprite = render_text_with_shadow(
                            context.render.ui_info.clock_font, text, CREAM, SHADOW
                        )
                        clock.rect.center = old_center

                    case Player.WHITE:
                        old_center = clock.rect.center
                        clock.sprite = render_text_with_shadow(
                            context.render.ui_info.clock_font, text, CHARCOAL, SHADOW
                        )
                        clock.rect.center = old_center
