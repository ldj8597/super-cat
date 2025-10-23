# camera.py

import pygame

from settings import WIDTH, HEIGHT


class Camera:
    def __init__(self, world_width, world_height):
        self.rect = pygame.FRect(0, 0, WIDTH, HEIGHT)
        self.world_w = world_width
        self.world_h = world_height

    @property
    def offset(self):
        return pygame.Vector2(self.rect.topleft)

    def follow(self, target_rect: pygame.FRect):
        self.rect.center = target_rect.center
        self._clamp_to_world()

    def _clamp_to_world(self):
        """keep the camera viewport within the world bounds."""
        if self.rect.w >= self.world_w:
            self.rect.x = (self.world_w - self.rect.w) / 2
        else:
            if self.rect.left < 0:
                self.rect.left = 0
            if self.rect.right > self.world_w:
                self.rect.right = self.world_w

        if self.rect.h >= self.world_h:
            self.rect.y = (self.world_h - self.rect.h) / 2
        else:
            if self.rect.top < 0:
                self.rect.top = 0
            if self.rect.bottom > self.world_h:
                self.rect.bottom = self.world_h

    def apply(self, rect):
        """Round to nearest pixel (recommended for smoothness)."""
        sx = round(rect.x - self.rect.x)
        sy = round(rect.y - self.rect.y)
        sw = round(rect.w)
        sh = round(rect.h)
        return pygame.Rect(sx, sy, sw, sh)
