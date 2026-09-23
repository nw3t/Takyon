"""
Set up all runtime vars
"""

from .takyon_types import (
    AppContext,
    Timer,
    Player,
    Dimension,
    InputState,
    StoneCount,
    Stones,
    Sprites,
    SpritesByType,
    BoardState,
    GameState,
    UIInfo,
    RenderingParams,
)
from .takyon_const import (
    ATLAS_DIR,
    BOARD_DIMS,
    CLOCK_FONT,
    CLOCK_START_SECONDS,
    SINGLES_DIR,
    TOOLTIP_FONT,
    Texture,
    UI_FONT,
    WINDOW_H,
    WINDOW_W,
)
from collections import defaultdict
import json
import pygame


def initialize_takyon_context() -> AppContext:
    """
    This needs pygame.init() to run first, I have it in main just cause that's where I like to see it
    :return:
    """

    window: pygame.Surface = pygame.display.set_mode(
        (WINDOW_W, WINDOW_H), pygame.RESIZABLE
    )
    pygame.display.set_caption("Takyon")

    canvas: pygame.Surface = pygame.Surface((WINDOW_W, WINDOW_H))
    display_target: pygame.Rect = pygame.Rect(0, 0, WINDOW_W, WINDOW_H)

    clock: pygame.time.Clock = pygame.time.Clock()
    timer: Timer = {
        Player.BLACK: CLOCK_START_SECONDS,
        Player.WHITE: CLOCK_START_SECONDS,
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
        ui_font=pygame.font.SysFont(UI_FONT, 48),
        tooltip_font=pygame.font.SysFont(TOOLTIP_FONT, 24),
        clock_font=pygame.font.SysFont(CLOCK_FONT, 64),
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
    return app_context
