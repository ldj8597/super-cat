# base.py

import pygame

# from super_cat.core.camera import Camera
from core.camera import Camera
from settings import GRAVITY, TERMINAL_V


class Entity:
    def __init__(
        self,
        pos: tuple[float, float],
        size: tuple[float, float],
        color: pygame.typing.ColorLike,
    ):
        self.rect = pygame.FRect(pos[0], pos[1], size[0], size[1])
        self.vel = pygame.Vector2(0, 0)
        self.on_ground = False
        self.color = color

    def move_and_collide(self, dt: float, tiles: list[pygame.FRect]):
        # --- Horizontal movement and collision ---
        # Apply velocity with dt using float precision
        self.rect.x += self.vel.x * dt
        hits = [t for t in tiles if self.rect.colliderect(t)]
        for t in hits:
            if self.vel.x > 0:
                self.rect.right = t.left
            elif self.vel.x < 0:
                self.rect.left = t.right

        # --- Vertical movement and collision ---
        # Apply gravity with a terminal velocity cap
        self.vel.y = min(self.vel.y + GRAVITY * dt, TERMINAL_V)
        self.rect.y += self.vel.y * dt
        hits = [t for t in tiles if self.rect.colliderect(t)]
        self.on_ground = False
        for t in hits:
            if self.vel.y > 0:
                self.rect.bottom = t.top
                self.vel.y = 0
                self.on_ground = True
            elif self.vel.y < 0:
                self.rect.top = t.bottom
                self.vel.y = 0

    def draw(self, surf: pygame.Surface, camera: Camera):
        pygame.draw.rect(surf, self.color, camera.apply(self.rect))
