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

from __future__ import annotations  # the ability to order freely
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from .takyon_types import *
from .global_const import *

from collections import defaultdict


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


#####################
# ENTRY POINT HERE BAYBEEEEE
#####################
def main():
    """
    Let's play Tak
    """
    pygame.init()

    window: pygame.Surface = pygame.display.set_mode(
        (WINDOW_W, WINDOW_H), pygame.RESIZABLE
    )
    pygame.display.set_caption("Takyon")

    canvas: pygame.Surface = pygame.Surface((WINDOW_W, WINDOW_H))
    display_target: pygame.Rect = pygame.Rect(0, 0, WINDOW_W, WINDOW_H)

    clock: pygame.time.Clock = pygame.time.Clock()
    timer: Timer = {
        Player.BLACK: TIMER_START_SECONDS,
        Player.WHITE: TIMER_START_SECONDS,
    }
    board_choice: Dimension = 6
    input_state: InputState = InputState(set(), None, 0, None, None, None, None, None)
    stones: int = BOARD_DIMS[board_choice].stones
    capstones: int = BOARD_DIMS[board_choice].capstones
    stone_count: StoneCount = StoneCount(
        black=Stones(stones, capstones),
        white=Stones(stones, capstones),
    )
    board_state: BoardState = {}
    sprites: Sprites = {}
    sprites_by_type: SpritesByType = defaultdict(pygame.sprite.Group)
    game_state: GameState = GameState(
        sprites=sprites,
        sprites_by_type=sprites_by_type,
        board=board_state,
        dimension=board_choice,
        stone_count=stone_count,
        active_player=Player.BLACK,
        timer=timer,
        input_state=input_state,
    )

    #####################
    # Load single images
    textures: dict[Texture, pygame.Surface] = {
        Texture("Bg"): pygame.image.load(SINGLES_DIR / "Bg.png").convert_alpha(),
        Texture("Board"): pygame.image.load(SINGLES_DIR / "Board.png").convert_alpha(),
        Texture("Tile"): pygame.image.load(SINGLES_DIR / "Tile.png").convert_alpha(),
        Texture("BlackClock"): pygame.image.load(
            SINGLES_DIR / "BlackClock.png"
        ).convert_alpha(),
        Texture("WhiteClock"): pygame.image.load(
            SINGLES_DIR / "WhiteClock.png"
        ).convert_alpha(),
    }

    #####################
    # Load sprites
    atlas = pygame.image.load(ATLAS_DIR / "atlas.png").convert_alpha()
    with open(ATLAS_DIR / "atlas.json") as file:
        atlas_map = json.load(file)

    for sprite in atlas_map["sprites"]:
        name = Texture(sprite["nameId"])
        x = sprite["position"]["x"]
        y = sprite["position"]["y"]
        h = sprite["sourceSize"]["height"]
        w = sprite["sourceSize"]["width"]

        rect = pygame.Rect(x, y, w, h)
        textures[name] = atlas.subsurface(rect)
    ui_info: UIInfo = UIInfo(
        ui_font=pygame.font.SysFont("courier new", 48),
        tooltip_font=pygame.font.SysFont("courier new", 24),
        clock_font=pygame.font.SysFont("courier new", 64),
    )

    render_params: RenderingParams = RenderingParams(
        window=window,
        canvas=canvas,
        display_target=display_target,
        clock=clock,
        clock_tick=0,
        textures=textures,
        ui_info=ui_info,
    )
    app_context: AppContext = AppContext(
        game=game_state,
        render=render_params,
    )
    # All static and non-moving elements
    spawn_board(app_context)

    game_loop(app_context)


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

    minutes, seconds = divmod(TIMER_START_SECONDS, 60.0)
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


def hover_enter_callbacks(
    context: AppContext,
    entered_sprites: set[SpriteID],
) -> None:
    """

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
        # This can resize the window and close the game, so it comes first
        user_inputs(context)
        update_tooltips(context)

        render_sprites(context)


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


def render_sprites(context: AppContext) -> None:
    """
    Run through the sprites in the game and blit them
    :param context:
    :return:
    """
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
        context.render.canvas.blit(sprite, rect)

    # stones fetched from the board will be in lists of 1-8 members and only the top two will ever be blitted
    for sprite_list in context.game.board.values():
        if not sprite_list:
            continue
        top = sprite_list[-1]
        second = sprite_list[-2] if len(sprite_list) >= 2 else None

        if second and top.texture in SEE_THROUGH_TEXTURES:
            context.render.canvas.blit(second.sprite, second.rect)
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


def spawn_stone_at_mouse(context: AppContext, sprite_id: SpriteID) -> None:
    """
    Passed as a callback to put a white or black stone in your hand, if one's already in your hand, put it back
    :return:
    """
    print(context, sprite_id)


def spawn_capstone_at_mouse(context: AppContext, sprite_id: SpriteID) -> None:
    """
    Passed as a callback to put a white or black stone in your hand, if one's already in your hand, put it back
    :return:
    """
    print(context, sprite_id)


def show_tile_stack(context: AppContext, sprite_id: SpriteID) -> None:
    """
    Passed as a callback to show the tile's side view
    :return:
    """
    print(context, sprite_id)


def hide_tile_stack(context: AppContext, sprite_id: SpriteID) -> None:
    """
    Passed as a callback to hide the tile's sideview
    :return:
    """
    print(context, sprite_id)


def drop_tiles_along_drag(context: AppContext, sprite_id: SpriteID) -> None:
    """
    Passed as a callback to drop one tile at a time in a straight line
    :return:
    """
    print(context, sprite_id)


def drop_all_tiles(context: AppContext, sprite_id: SpriteID) -> None:
    """
    Passed as a callback to drop everything in your hand
    :return:
    """
    print(context, sprite_id)


def flatten_tiles_along_drag(context: AppContext, sprite_id: SpriteID) -> None:
    """
    Passed as a callback to super drag - intentionally flatten with your capstones if possible
    :return:
    """
    print(context, sprite_id)


def drop_and_flatten_all_tiles(context: AppContext, sprite_id: SpriteID) -> None:
    """
    Passed as a callback to super drop - intentionally flatten with your capstones if possible
    :return:
    """
    print(context, sprite_id)


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
if __name__ == "__main__":
    main()