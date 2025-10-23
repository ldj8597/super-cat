# utils.py

import pygame

from settings import TILE


def rects_from_level(level) -> list[pygame.FRect]:
    tiles = []
    for y, line in enumerate(level):
        for x, ch in enumerate(line):
            if ch == "#":
                tiles.append(pygame.FRect(x * TILE, y * TILE, TILE, TILE))
    return tiles
