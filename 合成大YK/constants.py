"""Game constants at reference resolution 600×900. All values scaled via s()."""

import math
import os
import sys
from version import VERSION  # noqa: E402 — 版本号统一管理


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and PyInstaller builds."""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)

# ---- 自动更新 ----
# 远程版本信息 JSON 文件 URL。格式: {"version": "v0.3.2.0", "download_url": "..."}
# 设为空字符串 "" 禁用更新检查
UPDATE_URL = ""

# ---- Reference resolution (design target) ----
REF_WIDTH = 600
REF_HEIGHT = 900

# Default initial window size (bigger than reference for more room)
INIT_WIDTH = 720
INIT_HEIGHT = 1020

# ---- Scale factor (updated on window resize) ----
_SCALE = 1.0


def set_scale(scale: float):
    global _SCALE
    _SCALE = scale


def get_scale() -> float:
    return _SCALE


def s(value: float) -> float:
    """Scale a base value to current window size. Use for all positions, sizes, radii."""
    return value * _SCALE


def si(value: float) -> int:
    """s() rounded to int."""
    return int(value * _SCALE)


# ---- Base values (at reference resolution 600×900) ----

# Container
CONTAINER_LEFT = 45
CONTAINER_RIGHT = 555
CONTAINER_TOP = 70
CONTAINER_BOTTOM = 700
CONTAINER_WIDTH = CONTAINER_RIGHT - CONTAINER_LEFT
CONTAINER_HEIGHT = CONTAINER_BOTTOM - CONTAINER_TOP

# Spawn line for new items
DROP_LINE_Y = 50

# Overflow / Game Over line
OVERFLOW_LINE_Y = 130
OVERFLOW_TIME = 1.5  # seconds — NOT scaled

# Physics (at reference resolution; scaled via s() at runtime)
GRAVITY = 1400.0
DAMPING = 0.18
FRICTION = 0.997
MERGE_COOLDOWN = 0.25  # seconds — NOT scaled
# Drop delay = free-fall time from DROP_LINE_Y to CONTAINER_BOTTOM
# d = 0.5 * g * t²  →  t = sqrt(2*d/g)
_DROP_DISTANCE = CONTAINER_BOTTOM - DROP_LINE_Y  # 650 px at ref
DROP_DELAY = math.sqrt(2 * _DROP_DISTANCE / GRAVITY)  # ≈ 0.964s — NOT scaled

# Magnetic attraction for same-tier merging
ATTRACT_RANGE = 33.0   # px gap that triggers pull
ATTRACT_FORCE = 800.0    # acceleration strength

# ---- 大西瓜模式 (11-element lite) 物理覆写 ----
# 精确匹配 daxigua 参考比例（720×1280 → 600×900 等比例缩放）
# 有效重力 = 300 × gravityScale(3) = 900
LITE_GRAVITY = 900.0         # daxigua: 世界重力300, fruit gravityScale=3
LITE_DAMPING = 0.1           # daxigua: fruit restitution=0.1
LITE_FRICTION = 1.0          # daxigua: fruit friction=1.0
LITE_DROP_DELAY = 0.5        # daxigua: scheduleOnce(createFruit, 0.5)
LITE_INITIAL_VY = 800.0      # daxigua: linearVelocity (0, -800)
LITE_ATTRACT_FORCE = 0.0     # daxigua: 无磁力（纯碰撞合成）
LITE_ATTRACT_RANGE = 0.0     # 无磁力
# 容器比例：距顶 9.4% 掉落 / 17.2% 溢出 / 91.3% 底 → 900×比例
LITE_DROP_LINE_Y = 84        # 900×0.09375
LITE_CONTAINER_TOP = 60      # 略高于掉落线
LITE_CONTAINER_LEFT = 46     # 容器宽 507px，宽高比匹配 daxigua 720/948
LITE_CONTAINER_RIGHT = 553   # 46+507
LITE_CONTAINER_BOTTOM = 822  # 900×0.9125
LITE_OVERFLOW_Y = 155        # 900×0.1719
LITE_OVERFLOW_TIME = 3.0     # daxigua: checkEndTime > 3

# Collision resolution iterations per frame
COLLISION_PASSES = 5

# Colors
BG_COLOR = (20, 22, 35)
CONTAINER_BG = (32, 35, 52)
CONTAINER_BORDER = (80, 85, 115)
DANGER_LINE_COLOR = (210, 55, 55)
TEXT_COLOR = (240, 240, 245)
SCORE_COLOR = (255, 215, 90)
PREVIEW_ALPHA = 110
OVERLAY_COLOR = (0, 0, 0, 175)

FPS = 60

# ---- 按钮栏 ----
BUTTON_BAR_H = 24  # 按钮栏高度（基值）

# 按钮定义: (x_base, width_base, label, action)
BUTTONS = [
    (4,   50, "🔄重来",  "restart"),
    (56,  50, "🔲放大",  "maximize"),
    (108, 50, "⬜全屏",  "fullscreen"),
    (160, 50, "━最小",   "minimize"),
    (212, 54, "🐛调试",  "debug"),
    (270, 50, "❌退出",  "quit"),
]
