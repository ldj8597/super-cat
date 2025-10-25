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
        self.rect = pygame.FRect(pos, size)
        self.vel = pygame.Vector2(0, 0)
        self.on_ground = False
        self.color = color
        # Timer to ignore one-way collisions (for drop-through)
        self.ignore_one_way_timer = 0.0

    def move_and_collide(
        self,
        dt: float,
        solids: list[pygame.FRect] | list[pygame.Rect],
        one_ways: list[pygame.FRect] | list[pygame.Rect] | None = None,
    ):
        """
        Integrate velocity, collide against solids;
        For one-way tiles, only collide when falling and coming from above.
        """
        if one_ways is None:
            one_ways = []

        # --- Horizontal movement ---
        self.rect.x += self.vel.x * dt
        # collide vs full solids only (one-way doesn't block horizontally)
        hits = [t for t in solids if self.rect.colliderect(t)]
        for t in hits:
            if self.vel.x > 0:
                self.rect.right = t.left
            elif self.vel.x < 0:
                self.rect.left = t.right

        # --- Vertical movement ---
        prev_bottom = self.rect.bottom  # remember previous bottom for one-way check
        self.vel.y = min(self.vel.y + GRAVITY * dt, TERMINAL_V)
        self.rect.y += self.vel.y * dt

        self.on_ground = False

        # 1) collide vs full solids(both up & down)
        hits = [t for t in solids if self.rect.colliderect(t)]
        for t in hits:
            if self.vel.y > 0:
                self.vel.y = 0
                self.rect.bottom = t.top
                self.on_ground = True
            elif self.vel.y < 0:
                self.vel.y = 0
                self.rect.top = t.bottom

        # 2) collide vs one-way platforms
        if self.ignore_one_way_timer > 0.0:
            self.ignore_one_way_timer = max(0.0, self.ignore_one_way_timer - dt)
        else:
            if self.vel.y >= 0:  # only when falling / moving down or resting
                hits = [
                    t
                    for t in one_ways
                    if self.rect.colliderect(t) and prev_bottom <= t.top
                ]
                for t in hits:
                    self.rect.bottom = t.top
                    self.vel.y = 0
                    self.on_ground = True

    def draw(self, surf: pygame.Surface, camera: Camera):
        pygame.draw.rect(surf, self.color, camera.apply(self.rect))
