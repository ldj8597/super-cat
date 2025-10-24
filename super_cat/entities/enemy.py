# enemy.py

from .base import Entity
from settings import COLOR_ENEMY


class Enemy(Entity):
    def __init__(self, pos: tuple[float, float], patrol_range=160, speed=80):
        super().__init__(pos, (24, 28), COLOR_ENEMY)
        self.base_x = pos[0]
        self.patrol_range = patrol_range
        self.speed = speed
        self.direction = 1

    def update_ai(self):
        left = self.base_x - self.patrol_range
        right = self.base_x + self.patrol_range
        if self.rect.x <= left:
            self.direction = 1
        elif self.rect.x >= right:
            self.direction = -1
        self.vel.x = self.direction * self.speed
