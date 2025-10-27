# settings.py

# Screen/physics/speed constants
WIDTH, HEIGHT = 960, 540
TILE = 32
FPS = 60

# Vertical physics
JUMP_SPEED = 640  # px/s
GRAVITY = 1800
TERMINAL_V = 1400

# Horizontal movement (acceleration-based)
# Horizontal movement (acceleration-based)
MAX_SPEED = 260  # px/s (horizontal top speed)
ACCEL_GROUND = 2800  # px/s^2 when holding left/right on ground
DECEL_GROUND = 3200  # px/s^2 when changing direction on ground
ACCEL_AIR = 900  # px/s^2 when holding left/right in air
DECEL_AIR = 1600  # px/s^2 when changing direction in air
FRICTION_GROUND = 1000  # px/s^2 when no input on ground
FRICTION_AIR = 300  # px/s^2 when no input in air (tiny drift damp)


# Input feel
COYOTE_TIME = 0.20  # seconds you can still jump after leaving ground
JUMP_BUFFER_TIME = 0.24  # seconds jump input is buffered before landing

# Colors
COLOR_BG = (20, 20, 20)
COLOR_TILE = (90, 90, 95)
COLOR_PLAYER = (40, 160, 255)
COLOR_ENEMY = (220, 60, 60)
COLOR_TEXT = (230, 230, 230)

# Animation
ANIM_DEFAULT_FPS = 10
USE_PLACEHOLDER_GFX = False

# One-way platforms
DROP_THROUGH_TIME = 0.15  # seconds to ignore one-way when pressing Down+Jump
DROP_SUPPRESS_JUMP = 0.08  # grace period to suppress buffered jump after drop-through
