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
    DROP_THROUGH_TIME,
)


class Player(Entity):
    def __init__(self, pos: tuple[float, float]):
        super().__init__(pos, (24, 32), COLOR_PLAYER)
        self.facing = 1  # 1=right, -1=left

        # Timers for input feel
        self.coyote_timer = 0.0  # time left to allow jump after leaving ground
        self.jump_buffer_timer = 0.0  # time left to consume buffered jump input
        self._prev_jump_down = False  # for detecting edge press
        self.drop_intent_timer = 0.0
        self.suppress_jump_timer = 0.0  # suppress buffered jump after drop-through

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

    def _clamp_to_max_speed(self, vx: float) -> float:
        return vx if abs(vx) <= MAX_SPEED else MAX_SPEED * self._sign(vx)

    def _next_velocity_x(self, vx: float, dt: float, input_dir: int, on_ground: bool):
        target_vx = input_dir * MAX_SPEED
        same_dir = self._sign(vx) == self._sign(target_vx) or target_vx == 0
        need_decel = not same_dir and abs(vx) > 1e-5

        if input_dir != 0:
            accel = ACCEL_GROUND if on_ground else ACCEL_AIR
            if need_decel:
                decel = DECEL_GROUND if on_ground else DECEL_AIR
                step = decel * dt
                vx = self._approach(vx, 0.0, step)
            step = accel * dt
            vx = self._approach(vx, target_vx, step)
        else:
            # No input: apply friction toward 0
            friction = FRICTION_GROUND if on_ground else FRICTION_AIR
            vx = self._approach(vx, 0.0, dt * friction)
        return vx

    def _set_direction(self, keys: pygame.key.ScancodeWrapper):
        self.input_dir = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.input_dir -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.input_dir += 1
        if self.input_dir:
            self.facing = 1 if self.input_dir > 0 else -1

    def _record_drop_intent(self):
        self.drop_intent_timer = DROP_THROUGH_TIME
        self.suppress_jump_timer = max(
            self.suppress_jump_timer, DROP_THROUGH_TIME * 0.5
        )
        self.jump_buffer_timer = 0.0
        self.coyote_timer = 0.0

    def _record_jump_intent(self):
        self.jump_buffer_timer = JUMP_BUFFER_TIME

    def _tick_timers(self, dt: float):
        if self.jump_buffer_timer > 0:
            self.jump_buffer_timer = max(0.0, self.jump_buffer_timer - dt)
        if self.suppress_jump_timer > 0:
            self.suppress_jump_timer = max(0.0, self.suppress_jump_timer - dt)
        if self.drop_intent_timer > 0:
            self.drop_intent_timer = max(0.0, self.drop_intent_timer - dt)

    # --- Input (pre-physics) ---
    def handle_input(self, dt: float):
        """Process input; acceleration-based horizontal; jump buffer; drop-through"""
        keys = pygame.key.get_pressed()

        # --- Horizontal input handling ---
        self._set_direction(keys)
        vx = self._next_velocity_x(self.vel.x, dt, self.input_dir, self.on_ground)
        self.vel.x = self._clamp_to_max_speed(vx)

        # --- Jump / drop-through input handling ---
        jump_down = keys[pygame.K_SPACE] or keys[pygame.K_UP]
        down_held = keys[pygame.K_DOWN] or keys[pygame.K_s]

        if down_held and jump_down and not self._prev_jump_down:
            self._record_drop_intent()
        elif jump_down and not self._prev_jump_down:
            self._record_jump_intent()
        self._prev_jump_down = jump_down

        # Tick timers
        self._tick_timers(dt)

    # --- Post-physics (after collisions) ---
    def after_physics(self, dt: float):
        """Coyote + buffered jump resolution after collisions."""
        # Refresh coyote when grounded; tick down when airborne
        if self.on_ground:
            self.coyote_timer = COYOTE_TIME
        else:
            if self.coyote_timer > 0:
                self.coyote_timer = max(0.0, self.coyote_timer - dt)

        # Consume drop-through intent when grounded: start ignoring one-way collisions
        if self.drop_intent_timer > 0.0 and self.on_ground:
            self.ignore_one_way_timer = DROP_THROUGH_TIME
            # Keep jump suppressed briefly so we don't immediately jump after dropping
            self.suppress_jump_timer = max(
                self.suppress_jump_timer, DROP_THROUGH_TIME * 0.5
            )
            self.drop_intent_timer = 0.0
            # Nudge downward to cleanly leave the platform
            if self.vel.y < 30:
                self.vel.y = 30
            return

        if self.suppress_jump_timer > 0.0:
            return

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
            run = [box((120, 210, 255)), box((80, 160, 240)), box((120, 210, 255))]
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
