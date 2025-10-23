# player.py

import pygame

from .base import Entity
from settings import PLAYER_SPEED, JUMP_SPEED, COLOR_PLAYER


class Player(Entity):
    def __init__(self, pos: tuple[float, float]):
        super().__init__(pos, (24, 43), COLOR_PLAYER)

    def handle_input(self, dt: float):
        keys = pygame.key.get_pressed()
        move = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move += 1

        self.vel.x = move * PLAYER_SPEED

        if (keys[pygame.K_SPACE] or keys[pygame.K_UP]) and self.on_ground:
            self.vel.y = -JUMP_SPEED
            self.on_ground = False
