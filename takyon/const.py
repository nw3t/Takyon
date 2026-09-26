"""
all the constants all the time
"""

from .types import Texture, SpriteType, BoardSetup, Stones, InteractionType
from pathlib import Path
import pygame

IS_COMPILED = 0 if "__compiled__" in globals() else 1
ROOT_DIR = Path(__file__).resolve().parents[IS_COMPILED]
ATLAS_DIR = ROOT_DIR / "assets" / "SpriteAtlas"
SINGLES_DIR = ROOT_DIR / "assets" / "Singles"

TYPE_Z_LAYERS = {
    SpriteType.BOARD: 0,
    SpriteType.UI: 1,
    SpriteType.CLOCK: 1,
    SpriteType.PIP: 2,
    SpriteType.TILE: 2,
    SpriteType.STONE: 3,
}

SEE_THROUGH_TEXTURES: tuple[Texture, ...] = (
    Texture.BLACK_STANDING,
    Texture.WHITE_STANDING,
)

BOARD_DIMS: BoardSetup = {
    3: Stones(stones=10, capstones=0),
    4: Stones(stones=15, capstones=0),
    5: Stones(stones=21, capstones=1),
    6: Stones(stones=30, capstones=1),
    8: Stones(stones=50, capstones=2),
}

BLACK: pygame.Color = pygame.Color(0, 0, 0)
CHARCOAL: pygame.Color = pygame.Color(33, 32, 28)
CHARCOAL_ALPHA: pygame.Color = pygame.Color(33, 32, 28, 230)
CREAM: pygame.Color = pygame.Color(251, 239, 218)
RED: pygame.Color = pygame.Color(220, 20, 20)
SHADOW: pygame.Color = pygame.Color(30, 30, 30)

UI_FONT = "courier new"
TOOLTIP_FONT = "courier new"
CLOCK_FONT = "courier new"

BOARD_SIZE: int = 980
WINDOW_W: int = 1920
WINDOW_H: int = 1080

TILE_SPACER: int = 20
UI_SPACER: int = 40

PIP_CLUSTER: int = 5
PIP_GAP: int = 8
PIP_LINE: int = 15
PIP_OFFSET: tuple[int, int] = (48, -55)
PIP_SCALE: int = 20
PIP_SPACER: int = 18

CLOCK_START_SECONDS = 900.0
CLOCK_OFFSET: int = -64
SHADOW_OFFSET: int = 3

#####################
# Kill this thing and make proper counter sprites that don't need it
COUNTER_UI_SCALE_RATIO: float = 2.5

BAG_TOOLTIP = "Left Click: pick up stone\nRight Click: pick up capstone"
STONE_COVERAGE: float = 0.9  # As a percentage of tile size
TOOLTIP_CLAMP_MARGIN = 6
TOOLTIP_DELAY = 1000.0
TOOLTIP_OFFSET_X = 14
TOOLTIP_OFFSET_Y = 13
TOOLTIP_PADDING = 8

MOUSE_BINDINGS: dict[int, InteractionType] = {
    1: InteractionType.LEFT_CLICK,
    2: InteractionType.MIDDLE_CLICK,
    3: InteractionType.RIGHT_CLICK,
    4: InteractionType.SCROLL_UP,
    5: InteractionType.SCROLL_DOWN,
    6: InteractionType.FORWARD,
    7: InteractionType.BACK,
}