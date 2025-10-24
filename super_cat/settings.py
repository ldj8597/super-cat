# settings.py

# Screen/physics/speed constants
WIDTH, HEIGHT = 960, 540
TILE = 32
FPS = 60

PLAYER_SPEED = 240  # px/s
JUMP_SPEED = 540  # px/s
GRAVITY = 1800
TERMINAL_V = 1400

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
