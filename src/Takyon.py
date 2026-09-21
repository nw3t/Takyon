#!/usr/bin/env python
"""Takyon by Woland

Art creds
Arabesque Design on Dark Ground
Virgil Solis German
1534–1562

Dark Grey Leather Handbag By Saber Handbags - This file was contributed to
Wikimedia Commons by Missouri Historical Society as part of a cooperation project.
The donation was facilitated by the Digital Public Library of America.
Record in source catalogDPLA identifier: f676934219011ac2ae4eb524dad7cd15
Missouri Historical Society identifier: 2000-018-0089, No restrictions
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
from typing import Literal, NewType
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

    def __init__(
        self,
        sprite_type: SpriteType,
        sprite: pygame.Surface,
        rect: pygame.Rect,
        texture: Texture | None,
        z_order: int,
        player: Player | None,
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
        self.z_order: int = z_order


def spawn_from_surface(
    state: GameState,
    sprite_type: SpriteType,
    surface: pygame.Surface,
    rect: pygame.Rect,
    z_order: int = 0,
    player: Player | None = None,
) -> SpriteID:
    """
    If the sprite has its own generated surface instead of a texture map
    :param state:
    :param sprite_type:
    :param surface:
    :param rect:
    :param z_order:
    :param player:
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
    )
    state.sprites[sprite_id] = info
    state.sprites_by_type[sprite_type].add(info)
    return sprite_id


def spawn(
    state: GameState,
    textures: dict[Texture, pygame.Surface],
    sprite_type: SpriteType,
    texture: Texture,
    rect: pygame.Rect,
    z_order: int = 0,
    player: Player | None = None,
) -> SpriteID:
    """
    Use this to make new sprites, no other constructor
    :param state:
    :param textures:
    :param sprite_type:
    :param texture:
    :param rect:
    :param z_order:one = None,
    :param player:
    :return:
    """
    sprite_id: SpriteID = SpriteID(next(NEXT_ID))
    scaled_sprite = pygame.transform.scale(textures[texture], rect.size)
    info: SpriteInfo = SpriteInfo(
        sprite_type, scaled_sprite, rect, texture, z_order, player
    )
    state.sprites[sprite_id] = info
    state.sprites_by_type[sprite_type].add(info)
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
    clock_font: pygame.font.Font
    clock_time: int


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

BoardSetup = dict[Dimension, Stones]
Sprites = dict[SpriteID, SpriteInfo]
SpritesByType = dict[SpriteType, pygame.sprite.Group]
BoardState = dict[tuple[int, int], list[SpriteInfo]]

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

COUNTER_UI_SCALE_RATIO: float = 2.5

STONE_COVERAGE: float = 0.9  # As a percentage of tile size

NEXT_ID: Iterator[int] = count(0)

TIMER_START_SECONDS = 900.0


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
    clock_font = pygame.font.SysFont("courier new", 64)
    board_choice: Dimension = 6
    stones: int = BOARD_DIMS[board_choice].stones
    capstones: int = BOARD_DIMS[board_choice].capstones
    stone_count: StoneCount = StoneCount(
        black=Stones(stones, capstones),
        white=Stones(stones, capstones),
    )
    board_state: BoardState = {}
    sprites: Sprites = {}
    sprites_by_type: SpritesByType = defaultdict(pygame.sprite.Group)
    render_params: RenderingParams = RenderingParams(
        window=window,
        canvas=canvas,
        display_target=display_target,
        clock=clock,
        clock_font=clock_font,
        clock_tick=0,
        clock_time=0,
    )
    game_state: GameState = GameState(
        sprites=sprites,
        sprites_by_type=sprites_by_type,
        board=board_state,
        dimension=board_choice,
        stone_count=stone_count,
        active_player=Player.WHITE,
        timer=timer,
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

    # All static and non-moving elements
    spawn_board(game_state, render_params, textures)

    game_loop(game_state, render_params)


def spawn_stone_counters(
    state: GameState,
    renders: RenderingParams,
    textures: dict[Texture, pygame.Surface],
) -> None:
    """
    :param state:
    :param renders:
    :param textures:
    """
    board_bounds: pygame.Rect = textures[Texture.BOARD].get_rect()
    board_bounds.center = renders.canvas.get_rect().center

    counter_scale: int = round(BOARD_SIZE / COUNTER_UI_SCALE_RATIO)

    black_counter_rect: pygame.Rect = pygame.Rect(0, 0, counter_scale, counter_scale)
    white_counter_rect: pygame.Rect = pygame.Rect(0, 0, counter_scale, counter_scale)

    black_counter_rect.bottomleft = board_bounds.move(UI_SPACER, 0).midright
    white_counter_rect.bottomright = board_bounds.move(-UI_SPACER, 0).midleft

    spawn(state, textures, SpriteType.UI, Texture.STONE_COUNTER, white_counter_rect)
    spawn(state, textures, SpriteType.UI, Texture.STONE_COUNTER, black_counter_rect)

    pip_rect_black: pygame.Rect = pygame.Rect(0, 0, PIP_SCALE, PIP_SCALE)
    pip_rect_white: pygame.Rect = pygame.Rect(0, 0, PIP_SCALE, PIP_SCALE)
    pip_rect_black.bottomleft = black_counter_rect.move(PIP_OFFSET).bottomleft
    pip_rect_white.bottomleft = white_counter_rect.move(PIP_OFFSET).bottomleft

    count_and_spawn_pips(state, textures, pip_rect_black, pip_rect_white)


def count_and_spawn_pips(
    state: GameState,
    textures: dict[Texture, pygame.Surface],
    pip_rect_black: pygame.Rect,
    pip_rect_white: pygame.Rect,
) -> None:
    """
    spawn all pips aligned on the grid at game start
    :param state:
    :param textures:
    :param pip_rect_black:
    :param pip_rect_white:
    :return:
    """

    players = (
        (
            state.stone_count.black.stones,
            state.stone_count.black.capstones,
            Texture.BLACK_PIP,
            pip_rect_black,
        ),
        (
            state.stone_count.white.stones,
            state.stone_count.white.capstones,
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
            spawn(state, textures, SpriteType.PIP, pip_texture, pip_translation)


def spawn_board(
    state: GameState,
    renders: RenderingParams,
    textures: dict[Texture, pygame.Surface],
) -> None:
    """
    Edit this to only spawn the UI
    :param state:
    :param renders:
    :param textures:
    :return:
    """

    spawn_timers(state, renders, textures)

    board_bounds: pygame.Rect = textures[Texture.BOARD].get_rect()
    board_bounds.center = renders.canvas.get_rect().center

    bg_bounds: pygame.Rect = textures[Texture.BG].get_rect()
    spawn(state, textures, SpriteType.BOARD, Texture.BG, bg_bounds)
    spawn(state, textures, SpriteType.BOARD, Texture.BOARD, board_bounds, 1)

    spawn_stone_counters(state, renders, textures)

    bag_scale: int = BOARD_SIZE // 4
    stone_scale: int = bag_scale // 2
    stone_spacer: int = bag_scale // 4

    right_bag_rect: pygame.Rect = pygame.Rect(0, 0, bag_scale, bag_scale)
    left_bag_rect: pygame.Rect = pygame.Rect(0, 0, bag_scale, bag_scale)
    black_ui_stone: pygame.Rect = pygame.Rect(0, 0, stone_scale, stone_scale)
    white_ui_stone: pygame.Rect = pygame.Rect(0, 0, stone_scale, stone_scale)

    left_bag_rect.topright = board_bounds.move(-UI_SPACER, 0).topleft
    right_bag_rect.topleft = board_bounds.move(UI_SPACER, 0).topright
    spawn(state, textures, SpriteType.UI, Texture.STONE_BAG, left_bag_rect)
    spawn(state, textures, SpriteType.UI, Texture.STONE_BAG, right_bag_rect)

    black_ui_stone.center = right_bag_rect.move(0, -stone_spacer).center
    white_ui_stone.center = left_bag_rect.move(0, -stone_spacer).center
    spawn(state, textures, SpriteType.UI, Texture.BLACK_FLAT, black_ui_stone)
    spawn(state, textures, SpriteType.UI, Texture.WHITE_FLAT, white_ui_stone)

    dimension = state.dimension

    # Probably a mistake, I wanna spawn the tiles as full sprites so I can snap to them
    tile_size = (BOARD_SIZE - (dimension + 2) * TILE_SPACER) // dimension
    tile_rect: pygame.Rect = pygame.Rect(0, 0, tile_size, tile_size)
    tile_rect.topleft = board_bounds.topleft
    for col in range(dimension):
        for row in range(dimension):
            spawn(
                state,
                textures,
                SpriteType.TILE,
                Texture.TILE,
                tile_rect.move(
                    TILE_SPACER + (tile_size + TILE_SPACER) * col,
                    TILE_SPACER + (tile_size + TILE_SPACER) * row,
                ),
            )


def spawn_timers(
    state: GameState, renders: RenderingParams, textures: dict[Texture, pygame.Surface]
) -> None:
    """

    :param state:
    :param renders:
    :param textures:
    :return:
    """
    board_bounds: pygame.Rect = textures[Texture.BOARD].get_rect()
    board_bounds.center = renders.canvas.get_rect().center

    clock_scale: int = round(BOARD_SIZE / COUNTER_UI_SCALE_RATIO)

    black_clock_rect: pygame.Rect = pygame.Rect(0, 0, clock_scale, clock_scale)
    white_clock_rect: pygame.Rect = pygame.Rect(0, 0, clock_scale, clock_scale)

    black_clock_rect.topleft = board_bounds.move(UI_SPACER, 0).midright
    white_clock_rect.topright = board_bounds.move(-UI_SPACER, 0).midleft

    spawn(state, textures, SpriteType.UI, Texture.BLACK_CLOCK, black_clock_rect)
    spawn(state, textures, SpriteType.UI, Texture.WHITE_CLOCK, white_clock_rect)

    minutes, seconds = divmod(TIMER_START_SECONDS, 60.0)
    text = f"{int(minutes):02d}:{int(seconds):02d}"
    white_clock_text: pygame.Surface = renders.clock_font.render(text, True, CHARCOAL)
    black_clock_text: pygame.Surface = renders.clock_font.render(text, True, CREAM)

    black_text_rect = black_clock_text.get_rect()
    white_text_rect = white_clock_text.get_rect()
    black_text_rect.midbottom = black_clock_rect.move(0, CLOCK_OFFSET).midbottom
    white_text_rect.midbottom = white_clock_rect.move(0, CLOCK_OFFSET).midbottom

    spawn_from_surface(
        state,
        SpriteType.CLOCK,
        black_clock_text,
        black_text_rect,
        player=Player.BLACK,
    )
    spawn_from_surface(
        state,
        SpriteType.CLOCK,
        white_clock_text,
        white_text_rect,
        player=Player.WHITE,
    )


def update_clocks(state: GameState, renders: RenderingParams) -> None:
    """

    :param state:
    :param renders:
    :return:
    """
    prev_time = state.timer[state.active_player]
    next_time = state.timer[state.active_player] - (renders.clock_tick / 1000.0)
    state.timer[state.active_player] = next_time

    if int(prev_time) != int(next_time):
        for clock in state.sprites_by_type[SpriteType.CLOCK]:
            if clock.player == state.active_player:
                minutes, seconds = divmod(state.timer[state.active_player], 60.0)
                text = f"{int(minutes):02d}:{int(seconds):02d}"
                match clock.player:
                    case Player.BLACK:
                        old_center = clock.rect.center
                        clock.sprite = renders.clock_font.render(text, True, CREAM)
                        clock.rect.center = old_center

                    case Player.WHITE:
                        old_center = clock.rect.center
                        clock.sprite = renders.clock_font.render(text, True, CHARCOAL)
                        clock.rect.center = old_center


def user_inputs(
    renders: RenderingParams,
):
    """
    take user inputs and respond
    :param renders:
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

            renders.display_target = pygame.Rect(0, 0, scaled_canvas_w, scaled_canvas_h)
            renders.display_target.center = (window_w // 2, window_h // 2)


def mouse_on_canvas(
    renders: RenderingParams,
) -> tuple[int, int]:
    """
    convert the window mouse to a scaled canvas mouse
    :param renders:
    :return:
    """
    raw_mouse_pos: tuple[int, int] = pygame.mouse.get_pos()
    canvas_mouse_x: int = (raw_mouse_pos[0] - renders.display_target.x) * (
        WINDOW_W // renders.display_target.width
    )
    canvas_mouse_y: int = (raw_mouse_pos[1] - renders.display_target.y) * (
        WINDOW_H // renders.display_target.height
    )
    return canvas_mouse_x, canvas_mouse_y


def game_loop(
    state: GameState,
    renders: RenderingParams,
) -> None:
    """
    main game loop silly
    :param state:
    :param renders:
    :return:
    """
    while True:

        update_clocks(state, renders)
        # This can resize the window and close the game, so it comes first
        user_inputs(renders)

        # canvas_mouse = mouse_on_canvas(renders)

        render_sprites(state, renders)


def render_sprites(state: GameState, renders: RenderingParams) -> None:
    """
    Run through the sprites in the game and blit them
    :param state:
    :param renders:
    :return:
    """
    renders.window.fill(BLACK)

    non_stones = (s for s in state.sprites.values() if s.type != SpriteType.STONE)

    for sprite_info in sorted(
        non_stones, key=lambda s: (TYPE_Z_LAYERS[s.type], s.z_order)
    ):
        rect: pygame.Rect = sprite_info.rect
        sprite: pygame.Surface = sprite_info.sprite
        renders.canvas.blit(sprite, rect)

    for sprite_list in state.board.values():
        if not sprite_list:
            continue
        top = sprite_list[-1]
        second = sprite_list[-2] if len(sprite_list) >= 2 else None

        if second and top.texture in SEE_THROUGH_TEXTURES:
            renders.canvas.blit(second.sprite, second.rect)
        renders.canvas.blit(top.sprite, top.rect)

    scaled_canvas: pygame.Surface = pygame.transform.scale(
        renders.canvas,
        (renders.display_target.width, renders.display_target.height),
    )

    renders.window.blit(scaled_canvas, renders.display_target)
    pygame.display.flip()
    renders.clock_tick = renders.clock.tick(60)
    renders.clock_time += renders.clock_tick


if __name__ == "__main__":
    main()
