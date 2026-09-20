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

DELETE_ME = 1

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
    PIP is a counter for how many stones the player has each turn
    TILE is a tile sprite used for snapping stones
    BOARD is the game board, UI features are measured against its rect
    STONE is a draggable game piece
    """

    UI = auto()
    PIP = auto()
    TILE = auto()
    BOARD = auto()
    STONE = auto()


class Player(Enum):
    """
    Used for telling whose turn it is, or none if not playing a match
    """

    WHITE = auto()
    BLACK = auto()
    NONE = auto()


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
    Mutable sprite data
    """

    def __init__(
        self,
        sprite_type: SpriteType,
        sprite: Path,
        rect: pygame.Rect,
        *groups: pygame.sprite.AbstractGroup,
    ):
        assert not groups, (
            "Add sprites via spawn() ONLY. Using this constructor directly "
            "will cause some nasty dup issues."
        )
        super().__init__(*groups)
        self.type = sprite_type
        self.sprite = sprite
        self.rect = rect


def spawn(
    state: GameState, sprite_type: SpriteType, sprite: Path, rect: pygame.Rect
) -> SpriteID:
    """
    Use this to make new sprites, no other constructor
    :param state:
    :param sprite_type:
    :param sprite:
    :param rect:
    :return:
    """
    sprite_id = SpriteID(next(NEXT_ID))
    info = SpriteInfo(sprite_type, sprite, rect)
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


@dataclass
class Render:
    """
    Format to queue up
    """

    surface: pygame.Surface
    rect: pygame.Rect


RenderQueue = list[Render]


@dataclass
class RenderingParams:
    """
    Pass to helper functions to keep track of PyGame's window
    """

    canvas: pygame.Surface
    clock: pygame.time.Clock
    display_target: pygame.Rect
    render_queue: RenderQueue
    window: pygame.Surface


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
    WHITE_CAP = "WhiteCap"
    WHITE_FLAT = "WhiteFlat"
    WHITE_PIP = "WhitePip"
    WHITE_SIDE_CAP = "WhiteSideCap"
    WHITE_SIDE_FLAT = "WhiteSideFlat"
    WHITE_SIDE_STANDING = "WhiteSideStanding"
    WHITE_STANDING = "WhiteStanding"


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

BLACK = (0, 0, 0)

WINDOW_W = 1920
WINDOW_H = 1080

BOARD_SIZE = 980
TILE_SPACER = 20
UI_SPACER = 40

PIP_SCALE = 20
PIP_SPACER = 18
PIP_GAP = 8
PIP_CLUSTER = 5
PIP_LINE = 15

COUNTER_UI_SCALE_RATIO = 2.5

STONE_COVERAGE = 0.9  # As a percentage of tile size

NEXT_ID: Iterator[int] = count(0)


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
    board_choice: Dimension = 6
    stones = BOARD_DIMS[board_choice].stones
    capstones = BOARD_DIMS[board_choice].capstones
    stone_count: StoneCount = StoneCount(
        black=Stones(stones, capstones),
        white=Stones(stones, capstones),
    )
    board_state: BoardState = {}
    sprites: Sprites = {}
    sprites_by_type: SpritesByType = defaultdict(pygame.sprite.Group)
    render_queue: RenderQueue = RenderQueue()
    render_params: RenderingParams = RenderingParams(
        window=window,
        canvas=canvas,
        display_target=display_target,
        clock=clock,
        render_queue=render_queue,
    )
    game_state: GameState = GameState(
        sprites=sprites,
        sprites_by_type=sprites_by_type,
        board=board_state,
        dimension=board_choice,
        stone_count=stone_count,
    )

    #####################
    # Load single images
    textures: dict[Texture, pygame.Surface] = {
        Texture("Bg"): pygame.image.load(SINGLES_DIR / "Bg.png").convert_alpha(),
        Texture("Board"): pygame.image.load(SINGLES_DIR / "Board.png").convert_alpha(),
        Texture("Tile"): pygame.image.load(SINGLES_DIR / "Tile.png").convert_alpha(),
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

    game_loop(game_state, render_params, textures)


def show_stone_count(
    state: GameState,
    rendering: RenderingParams,
    textures: dict[Texture, pygame.Surface],
) -> None:
    """
    :param state:
    :param rendering:
    :param textures:
    """
    board_size = textures[
        Texture.BOARD
    ].get_width()  # square board, only one dim needed
    board_bounds = textures[Texture.BOARD].get_rect()
    board_bounds.center = rendering.canvas.get_rect().center

    counter_scale = board_size / COUNTER_UI_SCALE_RATIO
    pip_offset: tuple[int, int] = (48, -55)

    scaled_counter: pygame.Surface = square_scale(
        textures[Texture.STONE_COUNTER], counter_scale
    )
    black_counter_rect: pygame.Rect = scaled_counter.get_rect(
        bottomright=board_bounds.move(-UI_SPACER, 0).midleft
    )
    rendering.render_queue.append(
        Render(surface=scaled_counter, rect=black_counter_rect)
    )

    right_counter_rect: pygame.Rect = scaled_counter.get_rect(
        bottomleft=board_bounds.move(UI_SPACER, 0).midright
    )
    rendering.render_queue.append(Render(scaled_counter, right_counter_rect))

    scaled_white_pip: pygame.Surface = square_scale(
        textures[Texture.WHITE_PIP], PIP_SCALE
    )
    white_pip_rect: pygame.Rect = scaled_white_pip.get_rect(
        bottomleft=black_counter_rect.move(pip_offset).bottomleft
    )

    scaled_black_pip = square_scale(textures[Texture.BLACK_PIP], PIP_SCALE)
    black_pip_rect = scaled_black_pip.get_rect(
        bottomleft=right_counter_rect.move(pip_offset).bottomleft
    )

    scaled_cap_pip = square_scale(textures[Texture.GOLD_PIP], PIP_SCALE)

    black_stones = state.stone_count.black.stones
    white_stones = state.stone_count.white.stones
    black_caps = state.stone_count.black.capstones
    white_caps = state.stone_count.white.capstones

    count_and_push_pips_to_render(
        black_stones,
        black_caps,
        rendering,
        StoneType.STONE,
        black_pip_rect,
        scaled_black_pip,
    )
    count_and_push_pips_to_render(
        white_stones,
        white_caps,
        rendering,
        StoneType.STONE,
        white_pip_rect,
        scaled_white_pip,
    )
    count_and_push_pips_to_render(
        black_stones,
        black_caps,
        rendering,
        StoneType.CAPSTONE,
        black_pip_rect,
        scaled_cap_pip,
    )
    count_and_push_pips_to_render(
        white_stones,
        white_caps,
        rendering,
        StoneType.CAPSTONE,
        white_pip_rect,
        scaled_cap_pip,
    )


def draw_board(
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
    #####################
    # The board and tiles are square, just need one side
    board_bounds = textures[Texture.BOARD].get_rect()
    board_bounds.center = renders.canvas.get_rect().center

    dimension = state.dimension
    tile = textures[Texture.TILE]
    board_size = board_bounds.w
    tile_size = (board_size - (dimension + 1) * TILE_SPACER) // dimension
    scaled_tile = pygame.transform.scale(tile, (tile_size, tile_size))
    for col in range(dimension):
        for row in range(dimension):
            renders.render_queue.append(
                Render(
                    scaled_tile,
                    (
                        board_bounds.move(
                            TILE_SPACER + (tile_size + TILE_SPACER) * col,
                            TILE_SPACER + (tile_size + TILE_SPACER) * row,
                        )
                    ),
                )
            )


def square_scale(surface: pygame.Surface, new_size: float) -> pygame.Surface:
    """
    Scale a sprite to a square
    :param surface:
    :param new_size:
    :return:
    """
    return pygame.transform.scale(surface, (new_size, new_size))


def count_and_push_pips_to_render(
    stones: int,
    capstones: int,
    renders: RenderingParams,
    stone_type: StoneType,
    pip_rect: pygame.Rect,
    scaled_pip: pygame.Surface,
) -> None:
    """
    do a little loop to neatly align pip stone counters in a grid
    :param stones:
    :param capstones:
    :param renders:
    :param stone_type: if we're doing capstones we need to know to offset by total pips
    :param pip_rect:
    :param scaled_pip:
    :return:
    """

    for pips in range(stones if stone_type == StoneType.STONE else capstones):
        stone_count: int = pips + stones if stone_type == StoneType.CAPSTONE else pips

        y_movement = PIP_SPACER * (stone_count // PIP_LINE)
        pip_base_move = (stone_count % PIP_LINE) * PIP_SPACER
        pip_gap_move = ((stone_count % PIP_LINE) // PIP_CLUSTER) * PIP_GAP
        x_movement = pip_base_move + pip_gap_move

        pip_translation = pip_rect.move(x_movement, -y_movement)
        renders.render_queue.append(Render(scaled_pip, pip_translation))


def set_up_game(
    renders: RenderingParams,
    textures: dict[Texture, pygame.Surface],
) -> None:
    """
    Edit this to only spawn initial sprites
    :param renders:
    :param textures:
    :return:
    """

    board_bounds = textures[Texture.BOARD].get_rect()
    board_size = board_bounds.w
    board_bounds.center = renders.canvas.get_rect().center

    bag_scale = board_size / 4
    stone_scale = bag_scale / 2
    stone_spacer = bag_scale / 4

    scaled_bag = square_scale(textures[Texture.STONE_BAG], bag_scale)

    left_bag_rect = scaled_bag.get_rect(
        topright=board_bounds.move(-UI_SPACER, 0).topleft
    )
    renders.render_queue.append(Render(scaled_bag, left_bag_rect))

    right_bag_rect = scaled_bag.get_rect(
        topleft=board_bounds.move(UI_SPACER, 0).topright
    )
    renders.render_queue.append(Render(scaled_bag, right_bag_rect))

    scaled_black_stone = square_scale(textures[Texture.BLACK_FLAT], stone_scale)
    black_stone_rect = scaled_black_stone.get_rect(
        center=right_bag_rect.move(0, -stone_spacer).center
    )
    renders.render_queue.append(Render(scaled_black_stone, black_stone_rect))

    scaled_white_stone = square_scale(textures[Texture.WHITE_FLAT], stone_scale)
    white_stone_rect = scaled_white_stone.get_rect(
        center=left_bag_rect.move(0, -stone_spacer).center
    )
    renders.render_queue.append(Render(scaled_white_stone, white_stone_rect))


def game_loop(
    state: GameState,
    rendering: RenderingParams,
    textures: dict[Texture, pygame.Surface],
) -> None:
    """
    main game loop silly
    :param state:
    :param rendering:
    :param textures:
    :return:
    """
    while True:

        raw_mouse_pos = pygame.mouse.get_pos()
        rendering.window.fill(BLACK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.WINDOWRESIZED:
                window_w = event.x
                window_h = event.y

                scale = min(window_w / WINDOW_W, window_h / WINDOW_H)
                scaled_canvas_w = int(WINDOW_W * scale)
                scaled_canvas_h = int(WINDOW_H * scale)

                rendering.display_target = pygame.Rect(
                    0, 0, scaled_canvas_w, scaled_canvas_h
                )
                rendering.display_target.center = (window_w // 2, window_h // 2)
        canvas_mouse = (
            (raw_mouse_pos[0] - rendering.display_target.x)
            * (WINDOW_W / rendering.display_target.width),
            (raw_mouse_pos[1] - rendering.display_target.y)
            * (WINDOW_H / rendering.display_target.height),
        )
        global DELETE_ME
        if DELETE_ME == 1:
            print(canvas_mouse)
            DELETE_ME = 0
        background_bounds = textures[Texture.BG].get_rect()
        rendering.canvas.blit(textures[Texture.BG])

        board_bounds = textures[Texture.BOARD].get_rect()
        board_bounds.center = background_bounds.center
        rendering.canvas.blit(textures[Texture.BOARD], board_bounds)

        draw_board(
            state, rendering, textures
        )
        set_up_game(rendering, textures)
        show_stone_count(state, rendering, textures)
        blit_render_queue(rendering)
        scaled_canvas = pygame.transform.scale(
            rendering.canvas,
            (rendering.display_target.width, rendering.display_target.height),
        )
        rendering.window.blit(scaled_canvas, rendering.display_target)
        pygame.display.flip()

        rendering.clock.tick(60)


def blit_render_queue(rendering: RenderingParams) -> None:
    """
    Run through the render queue, consume and blit it
    :param rendering:
    :return:
    """
    for each in rendering.render_queue:
        rendering.canvas.blit(each.surface, each.rect)
    rendering.render_queue.clear()


if __name__ == "__main__":
    main()
