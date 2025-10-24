# animation.py

from collections.abc import Iterable
import pygame

from settings import ANIM_DEFAULT_FPS


def slice_grid(
    surface: pygame.Surface, fw: int, fh: int, margin: int = 0, spacing: int = 0
) -> list[pygame.Surface]:
    """
    Slice a spritesheet into a flat list of frames using a fixed grid.

    Frames are extracted row by row
    """
    frames = []
    w, h = surface.size
    y = margin
    while y + fh <= h:
        x = margin
        while x + fw <= w:
            rect = pygame.Rect(x, y, fw, fh)
            frame = surface.subsurface(rect).copy()
            frames.append(frame)
            x += fw + spacing
        y += fh + spacing
    return frames


def frames_from_row(
    frames: list[pygame.Surface], row: int, columns: Iterable[int], per_row: int
):
    """Pick frames from a specific row by column indices."""
    return [frames[row * per_row + c] for c in columns]


def scale_frames(
    frames: list[pygame.Surface], size: tuple[float, float], pixel_art=True
):
    """Scale frames to a target (w, h) and return a new list."""
    w, h = size
    out = []
    for f in frames:
        if pixel_art:
            out.append(pygame.transform.scale(f, (w, h)))
        else:
            out.append(pygame.transform.smoothscale(f, (w, h)))
    return out


class Animation:
    def __init__(
        self,
        frames: list[pygame.Surface],
        fps: int = ANIM_DEFAULT_FPS,
        loop: bool = True,
    ):
        self.frames = frames
        self.fps = fps
        self.loop = loop
        self.time = 0.0
        self.index = 0

    def reset(self):
        self.time = 0.0
        self.index = 0

    def update(self, dt: float):
        if not self.frames:
            return
        self.time += dt
        step = 1.0 / max(1, self.fps)  # interval between frames in seconds.
        # Skip frames to pick correct frame
        while self.time >= step:
            self.time -= step
            self.index += 1
            if self.loop:
                self.index %= len(self.frames)
            else:
                self.index = min(self.index, len(self.frames) - 1)

    def current(self) -> pygame.Surface | None:
        return self.frames[self.index] if self.frames else None


class Animator:
    """
    State-based animation controller.

    Example:
        animator = Animator({'idle': idle_anim, 'run': 'run_anim})
        animator.set_state('run')
        animator.update(dt)
        frame = animator.frame()
    """

    def __init__(self, clips: dict[str, Animation], initial: str) -> None:
        self.clips = clips
        self.state = initial

    def set_state(self, state: str):
        if state == self.state:
            return
        self.state = state
        clip = self.clips.get(state)
        if clip:
            clip.reset()

    def update(self, dt: float):
        clip = self.clips.get(self.state)
        if clip:
            clip.update(dt)

    def frame(self) -> pygame.Surface | None:
        clip = self.clips.get(self.state)
        return clip.current() if clip else None
