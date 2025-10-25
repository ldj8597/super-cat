# tilemap.py

# CSV-based tilemap loader and renderer
# - Map CSV values: -1 = empty, 0..N = tile index
# - Tilset is a grid spritesheet sliced to frames

import csv
from pathlib import Path

import pygame

from .camera import Camera
from .tileprops import TilesetProps
from settings import TILE

type Grid = list[list[int]]


def load_csv_grid(csv_file: Path) -> Grid:
    """Load a CSV file into a 2D grid fo ints."""
    grid: Grid = []
    with open(csv_file, newline="") as file:
        reader = csv.reader(file)
        for row in reader:
            grid.append([int(x) for x in row])
    return grid


def build_rects_of_indices(
    grid: Grid, indices: set[int], tile_size: int = TILE
) -> list[pygame.Rect]:
    """Create axis-aligned solid rects from grid indices."""
    rects: list[pygame.Rect] = []
    for y, row in enumerate(grid):
        for x, idx in enumerate(row):
            if idx in indices:
                rects.append(
                    pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
                )
    return rects


def slice_tileset(
    image: pygame.Surface, tw: int, th: int, margin: int = 0, spacing: int = 0
) -> list[pygame.Surface]:
    frames: list[pygame.Surface] = []
    w, h = image.size
    y = margin
    while y + th <= h:
        x = margin
        while x + tw <= w:
            rect = pygame.Rect(x, y, tw, th)
            frames.append(image.subsurface(rect).copy())
            x += tw + spacing
        y += th + spacing
    return frames


class TileMap:
    """
    CSV tilemap with optional tileset rendering.

    Layers: currently one layer (grid). Extend as needed.
    """

    def __init__(
        self,
        csv_path: Path,
        tileset_path: Path | None = None,
        tile_w: int = TILE,
        tile_h: int = TILE,
        props: TilesetProps | None = None,
    ):
        self.grid = load_csv_grid(csv_path)
        self.h = len(self.grid)
        self.w = len(self.grid[0]) if self.h else 0
        self.tile_w = tile_w
        self.tile_h = tile_h
        self.props = props or TilesetProps()
        self.tileset_frames: list[pygame.Surface] | None = None
        if tileset_path and tileset_path.exists():
            image = pygame.image.load(tileset_path).convert_alpha()
            self.tileset_frames = slice_tileset(image, tile_w, tile_h)

    @property
    def world_size(self):
        return self.w * self.tile_w, self.h * self.tile_h

    def solid_rects(self, solid_indices: set[int] | None = None) -> list[pygame.Rect]:
        # if solid_indices not given, derive from props.solid_indices;
        # default to non-negative if props empty
        if solid_indices is None:
            solid_indices = self.props.solid_indices or {
                i for row in self.grid for i in row if i >= 0
            }
        return build_rects_of_indices(self.grid, solid_indices, self.tile_w)

    def one_way_rects(self) -> list[pygame.Rect]:
        one_way_indices = self.props.one_way_indices
        if not one_way_indices:
            return []
        return build_rects_of_indices(self.grid, one_way_indices, self.tile_w)

    def draw(self, target: pygame.Surface, camera: Camera, empty_value: int = -1):
        # Draw cell-by-cell. For larger maps batch/diff drawing would be better.
        for y, row in enumerate(self.grid):
            for x, idx in enumerate(row):
                if idx == empty_value:
                    continue
                dst = pygame.Rect(
                    x * self.tile_w, y * self.tile_h, self.tile_w, self.tile_h
                )
                dst = camera.apply(dst)
                if self.tileset_frames and 0 <= idx < len(self.tileset_frames):
                    target.blit(self.tileset_frames[idx], dst)
                else:
                    # Fallback: draw a simple tile rect
                    pygame.draw.rect(target, (110, 110, 115), dst)
