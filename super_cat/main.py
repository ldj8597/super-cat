# main.py

import pygame

from core.camera import Camera
from core.utils import rects_from_level
from entities.player import Player
from entities.enemy import Enemy
from level_data import LEVEL
from settings import (
    WIDTH,
    HEIGHT,
    TILE,
    FPS,
    JUMP_SPEED,
    COLOR_BG,
    COLOR_TILE,
    COLOR_TEXT,
)


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Super Cat")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.Clock()
        self.font = pygame.font.SysFont(None, 18)

        # Build world from level
        self.tiles = rects_from_level(LEVEL)
        world_w = len(LEVEL[0]) * TILE
        world_h = len(LEVEL) * TILE

        # Entities
        self.player = Player((TILE * 3, TILE * 2))
        self.enemies = [Enemy((TILE * 7, TILE * 6), patrol_range=96)]

        # Camera
        self.camera = Camera(world_w, world_h)

        self.running = True

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            # --- Events ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # --- Input & AI ---
            self.player.handle_input(dt)
            for en in self.enemies:
                en.update_ai()

            # --- Physics & Collision ---
            self.player.move_and_collide(dt, self.tiles)
            for en in self.enemies:
                en.move_and_collide(dt, self.tiles)

            # --- Player-Enemy interaction ---
            for en in self.enemies[:]:
                if self.player.rect.colliderect(en.rect):
                    # Stomp check: player falling and above enemy center
                    if (
                        self.player.vel.y > 0
                        and self.player.rect.bottom <= en.rect.centery
                    ):
                        self.player.vel.y = -JUMP_SPEED * 0.55
                        self.enemies.remove(en)
                    else:
                        # Simple respawn
                        self.player.rect.topleft = (TILE * 3, TILE * 2)
                        self.player.vel = pygame.Vector2(0, 0)

            # --- Camera ---
            self.camera.follow(self.player.rect)

            # --- Animation update ---
            self.player.update_animation(dt)

            # --- Render ---
            self.screen.fill(COLOR_BG)

            # Draw tiles
            for t in self.tiles:
                pygame.draw.rect(self.screen, COLOR_TILE, self.camera.apply(t))

            # Draw entities
            self.player.draw(self.screen, self.camera)
            # self.player.debug_draw(self.screen, self.camera)
            for en in self.enemies:
                en.draw(self.screen, self.camera)

            # HUD
            fps_text = self.font.render(
                f"FPS {self.clock.get_fps():.0f}  pos=({self.player.rect.x:.1f},{self.player.rect.y:.1f})",
                True,
                COLOR_TEXT,
            )
            self.screen.blit(fps_text, (8, 8))

            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    Game().run()
