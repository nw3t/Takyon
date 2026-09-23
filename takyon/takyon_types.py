"""
all the types go here, silly
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Literal, NewType, Callable
import pygame

Dimension = Literal[3, 4, 5, 6, 8]
TimeRemaining = float
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


@dataclass
class UIInfo:
    """
    Used for UI rendering
    """

    ui_font: pygame.font.Font
    tooltip_font: pygame.font.Font
    clock_font: pygame.font.Font


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


Sprites = dict[SpriteID, SpriteInfo]
SpritesByType = dict[SpriteType, pygame.sprite.Group]
Timer = dict[Player, TimeRemaining]
BoardSetup = dict[Dimension, Stones]
BoardState = dict[tuple[int, int], list[SpriteInfo]]
InteractionCallback = Callable[[AppContext, SpriteID], None]
