# player.py

import pygame


from .base import Entity
from core.animation import (
    Animator,
    slice_grid,
    Animation,
    frames_from_row,
    scale_frames,
)
from core.camera import Camera
from core.utils import asset_path
from settings import (
    MAX_SPEED,
    ACCEL_GROUND,
    ACCEL_AIR,
    DECEL_GROUND,
    DECEL_AIR,
    FRICTION_GROUND,
    FRICTION_AIR,
    JUMP_SPEED,
    COLOR_PLAYER,
    USE_PLACEHOLDER_GFX,
    JUMP_BUFFER_TIME,
    COYOTE_TIME,
)


class Player(Entity):
    def __init__(self, pos: tuple[float, float]):
        super().__init__(pos, (24, 32), COLOR_PLAYER)
        self.facing = 1  # 1=right, -1=left

        # Timers for input feel
        self.coyote_timer = 0.0  # time left to allow jump after leaving ground
        self.jump_buffer_timer = 0.0  # time left to consume buffered jump input
        self._prev_jump_down = False  # for detecting edge press

        # Cached input state
        self.input_dir = 0  # -1, 0, +1

        # Load animations (fallback to placeholder if image missing)
        self._load_animations()

    # --- Helpers ---
    @staticmethod
    def _sign(x: float) -> int:
        return (x > 0) - (x < 0)

    @staticmethod
    def _approach(current: float, target: float, delta: float) -> float:
        """Move current toward target by at most delta (per call)."""
        if current < target:
            return min(current + delta, target)
        else:
            return max(current - delta, target)

    # --- Input (pre-physics) ---
    def handle_input(self, dt: float):
        """Process horizontal input and record jump intent (buffer).
        Acceleration-based horizontal movement.
        """
        keys = pygame.key.get_pressed()

        # Horizontal desired direction(-1, 0, 1)
        self.input_dir = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.input_dir -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.input_dir += 1
        if self.input_dir:
            self.facing = 1 if self.input_dir > 0 else -1

        # Compute target speed and choose accel/decles
        target_vx = self.input_dir * MAX_SPEED
        vx = self.vel.x
        same_dir = self._sign(vx) == self._sign(target_vx) or target_vx == 0

        if self.input_dir != 0:
            # Accelerate toward target speed (different on ground vs air)
            accel = ACCEL_GROUND if self.on_ground else ACCEL_AIR
            # if changing direction
            if not same_dir and abs(vx) > 1e-5:
                decel = DECEL_GROUND if self.on_ground else DECEL_AIR
                step = decel * dt
                vx = self._approach(vx, 0.0, step)
            # then accelerate toward target
            step = accel * dt
            vx = self._approach(vx, target_vx, step)
        else:
            # No input: apply friction toward 0
            friction = FRICTION_GROUND if self.on_ground else FRICTION_AIR
            vx = self._approach(vx, 0.0, dt * friction)

        # Clamp to max speed and assign
        if abs(vx) > MAX_SPEED:
            vx = MAX_SPEED * self._sign(vx)
        self.vel.x = vx

        # Record edge press for jump buffer (Space/Up)
        jump_down = keys[pygame.K_SPACE] or keys[pygame.K_UP]
        if jump_down and not self._prev_jump_down:
            # on the frame jump is pressed, (re)fill buffer
            self.jump_buffer_timer = JUMP_BUFFER_TIME
        self._prev_jump_down = jump_down

        # Decrease existing buffer slightly here; final handling in after_physics
        if self.jump_buffer_timer > 0:
            self.jump_buffer_timer = max(0.0, self.jump_buffer_timer - dt)

    # --- Post-physics (after collisions) ---
    def after_physics(self, dt: float):
        """Handle coyote time and buffered jump after collision resolution."""
        # Refresh coyote when grounded; tick down when airborne
        if self.on_ground:
            self.coyote_timer = COYOTE_TIME
        else:
            if self.coyote_timer > 0:
                self.coyote_timer = max(0.0, self.coyote_timer - dt)

        # If we have a buffered jump and are allowed to jump now, consume it
        can_jump_now = self.on_ground or self.coyote_timer > 0.0
        if self.jump_buffer_timer > 0.0 and can_jump_now:
            self.vel.y = -JUMP_SPEED
            self.on_ground = False
            self.coyote_timer = 0.0
            self.jump_buffer_timer = 0.0

    # --- Animation/state ---
    def _state_from_motion(self) -> str:
        # basic 4-state logic: idle/run/jump/fall
        if self.on_ground:
            return "run" if abs(self.vel.x) > 1e-3 else "idle"
        return "jump" if self.vel.y < 0 else "fall"

    def update_animation(self, dt: float):
        state = self._state_from_motion()
        self.anim.set_state(state)
        self.anim.update(dt)

    # --- Drawing ---
    def draw(self, surf: pygame.Surface, camera: Camera):
        frame = self.anim.frame()
        if frame is None:
            # Fallback to colored rect if no frames
            pygame.draw.rect(surf, self.color, camera.apply(self.rect))
        else:
            img = frame
            if self.facing < 0:
                img = pygame.transform.flip(img, True, False)
            dst = camera.apply(self.rect)
            # Align sprite's bottom-center to collision box's bottom-center
            ir = img.get_rect(midbottom=dst.midbottom)
            surf.blit(img, ir)

    # --- Assets ---
    def _load_animations(self):
        """
        Load spritesheet and build animations; fallback to colored rectangles.
        """
        sheet_path = asset_path("images", "player.png")
        clips = {}

        if not USE_PLACEHOLDER_GFX and sheet_path.exists():
            sheet = pygame.image.load(sheet_path).convert_alpha()

            # --- Configure sheet layout here ---
            FRAME_W, FRAME_H = 32, 32  # actual sprite frame size in the image
            PER_ROW = sheet.width // FRAME_W

            frames = slice_grid(sheet, FRAME_W, FRAME_H, margin=0, spacing=0)

            idle = frames_from_row(frames, row=0, columns=range(8), per_row=PER_ROW)
            run = frames_from_row(frames, row=1, columns=range(8), per_row=PER_ROW)
            jump = frames_from_row(frames, row=2, columns=range(4), per_row=PER_ROW)
            fall = frames_from_row(frames, row=2, columns=range(4, 8), per_row=PER_ROW)

            idle = scale_frames(idle, self.rect.size, pixel_art=True)
            run = scale_frames(run, self.rect.size, pixel_art=True)
            jump = scale_frames(jump, self.rect.size, pixel_art=True)
            fall = scale_frames(fall, self.rect.size, pixel_art=True)

            clips = {
                "idle": Animation(idle, fps=6, loop=True),
                "run": Animation(run, fps=12, loop=True),
                "jump": Animation(jump, fps=1, loop=False),
                "fall": Animation(fall, fps=1, loop=False),
            }
        else:
            # Placeholder frames (procedural surfaces)
            def box(color):
                surf = pygame.Surface((24, 32), pygame.SRCALPHA)
                surf.fill((0, 0, 0, 0))
                pygame.draw.rect(surf, color, pygame.Rect(0, 0, 24, 32), 2)
                pygame.draw.rect(surf, color, pygame.Rect(6, 8, 12, 16), 0)
                return surf

            idle = [box((90, 190, 255)), box((70, 170, 255))]
            run = [box((120, 210, 255)), box((80, 160, 240)), box((120, 210, 25))]
            jump = [box((180, 230, 255))]
            fall = [box((140, 200, 255))]
            clips = {
                "idle": Animation(idle, fps=2, loop=True),
                "run": Animation(run, fps=8, loop=True),
                "jump": Animation(jump, fps=1, loop=False),
                "fall": Animation(fall, fps=1, loop=False),
            }
        # Build animator
        self.anim = Animator(clips, initial="idle")
