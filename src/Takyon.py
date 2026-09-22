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
import pygame
import sys

from dataclasses import dataclass
from collections.abc import Iterator
from enum import Enum, auto
from itertools import count
from pathlib import Path
from typing import Literal, NewType, Callable
from collections import defaultdict

Dimension = Literal[3, 4, 5, 6, 8]
SpriteID = NewType("SpriteID", int)


class SpriteType(Enum):
    """
    UI is a UI element, never changing but often clickable
    CLOCK is a UI element, but it needs to be updated frequently and conditionally
    PIP is a counter for how many stones the player has each turn
    TILE is a tile sprite used for snapping stones
    BOARD is the game board, UI features are measured against its rect
    STONE is a draggable game piece
    """

    UI = auto()
    CLOCK = auto()
    PIP = auto()
    TILE = auto()
    BOARD = auto()
    STONE = auto()


TYPE_Z_LAYERS = {
    SpriteType.BOARD: 0,
    SpriteType.UI: 1,
    SpriteType.CLOCK: 1,
    SpriteType.PIP: 2,
    SpriteType.TILE: 2,
    SpriteType.STONE: 3,
}


class Player(Enum):
    """
    Used for telling whose turn it is
    """

    WHITE = auto()
    BLACK = auto()


class StoneType(Enum):
    """
    Distinguish between the two major stone types
    """

    STONE = auto()
    CAPSTONE = auto()


@dataclass
class Stones:
    """
    Used to track how many stones are left in the game
    """

    stones: int
    capstones: int


@dataclass
class StoneCount:
    """
    Player's stones remaining
    """

    black: Stones
    white: Stones


class Interactable(Enum):
    """
    The types of things you can interact with
    """

    STONE_BAG = auto()
    TILE = auto()
    CLOCK = auto()
    STONE_COUNTER = auto()
    MENU_BUTTON = auto()
    MUSIC_BUTTON = auto()
    UNDO_BUTTON = auto()
    PLANNING_BUTTON = auto()


class InteractionType(Enum):
    """
    The types of things you can do with interactables
    """

    LEFT_CLICK = auto()
    RIGHT_CLICK = auto()
    LEFT_DRAG_START = auto()
    LEFT_DRAG_STOP = auto()
    RIGHT_DRAG_START = auto()
    RIGHT_DRAG_STOP = auto()
    HOVER_ENTER = auto()
    HOVER_EXIT = auto()


class SpriteInfo(pygame.sprite.Sprite):
    """
    Mutable sprite data. Each sprit contains a .type, .sprite and .rect
    """

    type: SpriteType
    sprite: pygame.Surface
    rect: pygame.Rect
    texture: Texture | None
    z_order: int
    player: Player | None
    interactable: Interactable | None
    tooltip: str | None

    def __init__(
        self,
        sprite_type: SpriteType,
        sprite: pygame.Surface,
        rect: pygame.Rect,
        texture: Texture | None,
        z_order: int,
        player: Player | None,
        interactable: Interactable | None,
        tooltip: str | None,
        *groups: pygame.sprite.AbstractGroup,
    ):
        assert not groups, (
            "Add sprites via spawn() ONLY. Using this constructor directly "
            "will cause some nasty dup issues."
        )
        super().__init__(*groups)
        self.type: SpriteType = sprite_type
        self.sprite: pygame.Surface = sprite
        self.rect: pygame.Rect = rect
        self.texture: Texture | None = texture
        self.player: Player | None = player
        self.interactable: Interactable | None = interactable
        self.tooltip: str | None = tooltip
        self.z_order: int = z_order


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


def despawn(state: GameState, sprite_id: SpriteID) -> None:
    """
    Kill a sprite
    :param state:
    :param sprite_id:
    :return:
    """
    state.sprites[sprite_id].kill()
    del state.sprites[sprite_id]


TimeRemaining = float
Timer = dict[Player, TimeRemaining]


@dataclass
class GameState:
    """
    Our god object for sprites and positioning
    """

    sprites: Sprites
    sprites_by_type: SpritesByType
    board: BoardState
    dimension: Dimension
    stone_count: StoneCount
    active_player: Player
    timer: Timer
    input_state: InputState


@dataclass
class RenderingParams:
    """
    Pass to helper functions to keep track of PyGame's window
    """

    canvas: pygame.Surface
    clock: pygame.time.Clock
    clock_tick: int
    display_target: pygame.Rect
    window: pygame.Surface
    textures: dict[Texture, pygame.Surface]
    ui_info: UIInfo


class Texture(Enum):
    """
    Edit this every time a new texture is added to the atlas
    """

    BG = "Bg"
    BOARD = "Board"
    GOLD_PIP = "GoldPip"
    STONE_BAG = "StoneBag"
    STONE_COUNTER = "StoneCounter"
    TILE = "Tile"
    BLACK_CAP = "BlackCap"
    BLACK_FLAT = "BlackFlat"
    BLACK_PIP = "BlackPip"
    BLACK_SIDE_CAP = "BlackSideCap"
    BLACK_SIDE_FLAT = "BlackSideFlat"
    BLACK_SIDE_STANDING = "BlackSideStanding"
    BLACK_STANDING = "BlackStanding"
    BLACK_CLOCK = "BlackClock"
    WHITE_CAP = "WhiteCap"
    WHITE_FLAT = "WhiteFlat"
    WHITE_PIP = "WhitePip"
    WHITE_SIDE_CAP = "WhiteSideCap"
    WHITE_SIDE_FLAT = "WhiteSideFlat"
    WHITE_SIDE_STANDING = "WhiteSideStanding"
    WHITE_STANDING = "WhiteStanding"
    WHITE_CLOCK = "WhiteClock"


SEE_THROUGH_TEXTURES: tuple[Texture, Texture] = (
    Texture.WHITE_STANDING,
    Texture.BLACK_STANDING,
)


@dataclass
class AppContext:
    """Source of truth for the state of the app"""

    game: GameState
    render: RenderingParams


@dataclass
class InputState:
    """
    Trackables required for input
    """

    hovered_sprites: set[SpriteID]
    dragged_sprite: SpriteID | None
    last_click_time: int
    last_clicked_sprite: SpriteID | None
    active_tooltip_sprite: SpriteID | None
    active_tooltip: pygame.Surface | None
    pending_tooltip_sprite: SpriteID | None
    hover_start_time: int | None


BoardSetup = dict[Dimension, Stones]
Sprites = dict[SpriteID, SpriteInfo]
SpritesByType = dict[SpriteType, pygame.sprite.Group]
BoardState = dict[tuple[int, int], list[SpriteInfo]]
InteractionCallback = Callable[[AppContext, SpriteID], None]

BOARD_DIMS: BoardSetup = {
    3: Stones(stones=10, capstones=0),
    4: Stones(stones=15, capstones=0),
    5: Stones(stones=21, capstones=1),
    6: Stones(stones=30, capstones=1),
    8: Stones(stones=50, capstones=2),
}

IS_COMPILED = 0 if "__compiled__" in globals() else 1
ROOT_DIR = Path(__file__).resolve().parents[IS_COMPILED]
ATLAS_DIR = ROOT_DIR / "assets" / "SpriteAtlas"
SINGLES_DIR = ROOT_DIR / "assets" / "Singles"

BLACK: pygame.Color = pygame.Color(0, 0, 0)
CREAM: pygame.Color = pygame.Color(251, 239, 218)
CHARCOAL: pygame.Color = pygame.Color(33, 32, 28)
CHARCOAL_ALPHA: pygame.Color = pygame.Color(33, 32, 28, 230)
SHADOW: pygame.Color = pygame.Color(30, 30, 30)
RED: pygame.Color = pygame.Color(220, 20, 20)

WINDOW_W: int = 1920
WINDOW_H: int = 1080

BOARD_SIZE: int = 980

TILE_SPACER: int = 20
UI_SPACER: int = 40

PIP_SCALE: int = 20
PIP_SPACER: int = 18
PIP_GAP: int = 8
PIP_CLUSTER: int = 5
PIP_LINE: int = 15
PIP_OFFSET: tuple[int, int] = (48, -55)
CLOCK_OFFSET: int = -64
SHADOW_OFFSET: int = 3

COUNTER_UI_SCALE_RATIO: float = 2.5

STONE_COVERAGE: float = 0.9  # As a percentage of tile size

NEXT_ID: Iterator[int] = count(0)

TIMER_START_SECONDS = 900.0
TOOLTIP_DELAY = 1000.0
TOOLTIP_PADDING = 8
TOOLTIP_OFFSET_X = 14
TOOLTIP_OFFSET_Y = 13
TOOLTIP_CLAMP_MARGIN = 6


@dataclass
class UIInfo:
    """
    Used for UI rendering
    """

    ui_font: pygame.font.Font
    tooltip_font: pygame.font.Font
    clock_font: pygame.font.Font


BAG_TOOLTIP = "Left Click: pick up stone\nRight Click: pick up capstone"


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


def update_hovered_sprites(context: AppContext) -> tuple[set[SpriteID],set[SpriteID]]:
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
            callback = INTERACTION_CALLBACKS.get((interactable, InteractionType.HOVER_ENTER))
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
            callback = INTERACTION_CALLBACKS.get((interactable, InteractionType.HOVER_EXIT))
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
