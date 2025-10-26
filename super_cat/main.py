# main.py

import pygame

from core.camera import Camera
from core.tilemap import TileMap
from core.tileprops import load_tileset_props
from core.utils import rects_from_level, asset_path
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

        # Try to load CSV tilemap; if missing, fall back to LEVEL string map
        csv_map = asset_path("maps", "level1.csv")
        tileset_img = asset_path("images", "tiles.png")
        tileset_json = asset_path("maps", "level1.tiles.json")

        if csv_map.exists():
            props = load_tileset_props(tileset_json)
            self.tilemap = TileMap(
                csv_map, tileset_img, tile_w=TILE, tile_h=TILE, props=props
            )
            world_w, world_h = self.tilemap.world_size
            # Build solids (treat all non-negative indices as solid by default)
            self.solid_tiles = self.tilemap.solid_rects()
            self.one_way_tiles = self.tilemap.one_way_rects()
        else:
            # Fallback: use built-in LEVEL string map
            self.tilemap = None
            self.solid_tiles = rects_from_level(LEVEL)
            self.one_way_tiles = []
            world_w = len(LEVEL[0]) * TILE
            world_h = len(LEVEL) * TILE

        # Entities
        self.player = Player((TILE * 3, TILE * 2))
        self.enemies = []
        # self.enemies = [Enemy((TILE * 14, TILE * 8), patrol_range=96)]

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

            # --- Input & AI (pre-physics) ---
            self.player.handle_input(dt)
            for en in self.enemies:
                en.update_ai()

            # --- Physics & Collision ---
            self.player.move_and_collide(dt, self.solid_tiles, self.one_way_tiles)
            for en in self.enemies:
                en.move_and_collide(dt, self.solid_tiles, self.one_way_tiles)

            # --- Post-physics (coyote + jump buffer resolution) ---
            self.player.after_physics(dt)

            # --- Update surface friction for the next frame ---
            if self.tilemap and self.player.on_ground:
                self.player.surface_friction = self.tilemap.friction_under(
                    self.player.rect
                )
            else:
                self.player.surface_friction = 1.0

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

            if self.tilemap:
                self.tilemap.draw(self.screen, self.camera)
            else:
                for t in self.solid_tiles:
                    pygame.draw.rect(self.screen, COLOR_TILE, self.camera.apply(t))

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
            # in Game.run() render section
            dbg = self.font.render(
                f"fric={self.player.surface_friction:.2f}", True, COLOR_TEXT
            )
            self.screen.blit(fps_text, (8, 8))
            self.screen.blit(dbg, (8, 24))

            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    Game().run()
