# utils.py

from pathlib import Path

import pygame

from settings import TILE


def rects_from_level(level) -> list[pygame.FRect]:
    tiles = []
    for y, line in enumerate(level):
        for x, ch in enumerate(line):
            if ch == "#":
                tiles.append(pygame.FRect(x * TILE, y * TILE, TILE, TILE))
    return tiles


def asset_path(*parts) -> Path:
    """Return path under ./assets, creating folders if needed (for dev convenience)."""
    root = Path(__file__).resolve().parents[1]  # project root
    p = root / "assets"
    for part in parts:
        p = p / part
    return p
