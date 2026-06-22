"""Game constants at reference resolution 600×900. All values scaled via s()."""

import math
import os
import sys
from version import VERSION  # noqa: E402 — 版本号统一管理


# ---- v2.2.0.2: 外部数据文件夹 ----
_DATA_DIR_NAME = "合成大YK_Data"


def _get_exe_dir() -> str:
    """EXE 或脚本所在目录（frozen 时用 sys.executable，否则用 __file__）。"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource.

    v2.2.0.2: 优先查找外部数据文件夹 合成大YK_Data/（EXE 同目录），
    找不到再回退 _MEIPASS 或脚本目录。
    """
    # 1) 外部数据文件夹（EXE 旁边）
    external = os.path.join(_get_exe_dir(), _DATA_DIR_NAME, relative_path)
    if os.path.exists(external):
        return external

    # 2) PyInstaller _MEIPASS 或 脚本目录
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


def get_user_data_dir() -> str:
    """v2.3.0.0: 返回用户数据目录（%APPDATA%/Trash Panda Q Opal/Big Alloy Merge）。
    确保目录存在，用于存放所有可写文件（存档、配置、最高分等）。
    这样安装到 Program Files 后不需要管理员权限。
    """
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    path = os.path.join(appdata, "Trash Panda Q Opal", "Big Alloy Merge")
    os.makedirs(path, exist_ok=True)
    return path


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
FRICTION = 0.20
MERGE_COOLDOWN = 0.25  # seconds — NOT scaled
# Drop delay = free-fall time from DROP_LINE_Y to CONTAINER_BOTTOM
# d = 0.5 * g * t²  →  t = sqrt(2*d/g)
_DROP_DISTANCE = CONTAINER_BOTTOM - DROP_LINE_Y  # 650 px at ref
DROP_DELAY = math.sqrt(2 * _DROP_DISTANCE / GRAVITY)  # ≈ 0.964s — NOT scaled

# Magnetic attraction for same-tier merging
ATTRACT_RANGE = 33.0   # px gap that triggers pull
ATTRACT_FORCE = 800.0    # acceleration strength

# ---- JaneFlyThought1 (daxigua replica) ----
# 精确匹配 daxigua 参考比例（720×1280 → 600×900 等比例缩放）
# 有效重力 = 300 × gravityScale(3) = 900
JFT1_GRAVITY = 900.0         # daxigua: 世界重力300, fruit gravityScale=3
JFT1_DAMPING = 0.1           # daxigua: fruit restitution=0.1
JFT1_FRICTION = 1.0          # daxigua: fruit friction=1.0
JFT1_DROP_DELAY = 0.5        # daxigua: scheduleOnce(createFruit, 0.5)
JFT1_INITIAL_VY = 800.0      # daxigua: linearVelocity (0, -800)
JFT1_ATTRACT_FORCE = 0.0     # daxigua: 无磁力（纯碰撞合成）
JFT1_ATTRACT_RANGE = 0.0     # 无磁力
# 容器比例：距顶 9.4% 掉落 / 17.2% 溢出 / 91.3% 底 → 900×比例
JFT1_DROP_LINE_Y = 84        # 900×0.09375
JFT1_CONTAINER_TOP = 60      # 略高于掉落线
JFT1_CONTAINER_LEFT = 46     # 容器宽 507px，宽高比匹配 daxigua 720/948
JFT1_CONTAINER_RIGHT = 553   # 46+507
JFT1_CONTAINER_BOTTOM = 822  # 900×0.9125
JFT1_OVERFLOW_Y = 155        # 900×0.1719
JFT1_OVERFLOW_TIME = 3.0     # daxigua: checkEndTime > 3

# 兼容别名：旧代码引用 LITE_* 仍可用（指向 JFT1）
LITE_GRAVITY = JFT1_GRAVITY
LITE_DAMPING = JFT1_DAMPING
LITE_FRICTION = JFT1_FRICTION
LITE_DROP_DELAY = JFT1_DROP_DELAY
LITE_INITIAL_VY = JFT1_INITIAL_VY
LITE_ATTRACT_FORCE = JFT1_ATTRACT_FORCE
LITE_ATTRACT_RANGE = JFT1_ATTRACT_RANGE
LITE_DROP_LINE_Y = JFT1_DROP_LINE_Y
LITE_CONTAINER_TOP = JFT1_CONTAINER_TOP
LITE_CONTAINER_LEFT = JFT1_CONTAINER_LEFT
LITE_CONTAINER_RIGHT = JFT1_CONTAINER_RIGHT
LITE_CONTAINER_BOTTOM = JFT1_CONTAINER_BOTTOM
LITE_OVERFLOW_Y = JFT1_OVERFLOW_Y
LITE_OVERFLOW_TIME = JFT1_OVERFLOW_TIME

# ---- JaneFlyThought2 (当前默认) ----
# 高重力+高初速+摩擦+刚性(无弹性)+轻质球
JFT2_GRAVITY = 1800.0        # 重力加速度↓（JFT1=900 → 2倍）
JFT2_DAMPING = 0.0           # 刚性：无弹性碰撞（JFT1=0.1）
JFT2_FRICTION = 0.20         # 球间接触摩擦系数（v2.2.2.3: 从0.95降，不粘）
JFT2_DROP_DELAY = 0.25       # 更短冷却（JFT1=0.5s → 减半）
JFT2_INITIAL_VY = 1600.0     # 高初速↓（JFT1=800 → 2倍）
JFT2_ATTRACT_FORCE = 0.0     # 无磁力
JFT2_ATTRACT_RANGE = 0.0     # 无磁力
# 容器参数与 JFT1 相同（球半径/容器比例不变）
JFT2_DROP_LINE_Y = 84
JFT2_CONTAINER_TOP = 60
JFT2_CONTAINER_LEFT = 46
JFT2_CONTAINER_RIGHT = 553
JFT2_CONTAINER_BOTTOM = 822
JFT2_OVERFLOW_Y = 155
JFT2_OVERFLOW_TIME = 3.0

# 合成终极球庆祝特效时长（秒）
CELEBRATION_DURATION = 10.0

# Collision resolution iterations per frame
COLLISION_PASSES = 4

# 即时合成容错间距（v2.2.2.4）：两球距离 ≤ 半径和+3px 即合成
MERGE_TOLERANCE = 3.0

# 低速休眠阈值（px/帧）：低于此速度归零，消除微抖动
SLEEP_VELOCITY = 2.0
# 球稳定后持续静止超过此秒数 → 完全休眠（跳过碰撞检测）
SLEEP_SETTLE_TIME = 0.3

# 容器壁摩擦系数（v2.0.0.0 → v2.2.2.3 降：不再粘壁）
FRICTION_WALL = 0.08
# 旋转物理开关（v2.0.0.0）：球可旋转（碰撞切向冲量 → 扭矩）
ROTATION_ENABLED = True
# 旋转角速度每秒保留系数（v2.0.1.0 → v2.3.0.0: 0.92 更快衰减）
ANGULAR_DAMPING = 0.92
# 壁面旋转摩擦系数（v2.0.1.0 → v2.2.2.3: 大幅降低，触壁不杀旋转）
WALL_ROTATIONAL_FRICTION = 0.03
# 壁面线速度→旋转扭矩耦合系数（v2.0.1.0 → v2.3.0.0: 0.015 减半）
WALL_TORQUE_COUPLING = 0.015

# Colors (v2.2.0.0: 主题色系 — 浅亮紫/浅亮橙/浅亮青)
BG_COLOR = (20, 22, 35)
CONTAINER_BG = (32, 35, 52)
CONTAINER_BORDER = (80, 85, 115)
DANGER_LINE_COLOR = (210, 55, 55)
TEXT_COLOR = (200, 160, 255)      # 浅亮紫 — 主要文本
SCORE_COLOR = (255, 200, 140)     # 浅亮橙 — 强调/分数
TEXT_CYAN = (140, 230, 255)       # 浅亮青 — 标签/版本信息
PREVIEW_ALPHA = 110
OVERLAY_COLOR = (0, 0, 0, 175)

FPS = 480

# ---- v2.3.0.0 动态掉落参数（仅 full/full_debug 模式生效） ----
DYNAMIC_DROP_ENABLED = True        # 是否启用动态掉落
DYNAMIC_DROP_UNLOCK_OFFSET = 2     # 合成 N 级 → 解锁掉落 N-2 级
DYNAMIC_DROP_RATE_LIMIT = 5        # N-3 级：每 K 个球最多掉 1 次
DYNAMIC_DROP_RATE_LIMIT_TIGHT = 8  # N-2 级：更严格限频

# ---- 按钮栏 ----
BUTTON_BAR_H = 24  # 按钮栏高度（基值）

# 按钮定义: (x_base, width_base, label, action)
BUTTONS = [
    (4,   50, "🔄重来",  "restart"),
    (56,  50, "🔲放大",  "maximize"),
    (108, 50, "⬜全屏",  "fullscreen"),
    (160, 50, "━最小",   "minimize"),
    (212, 54, "🐛调试",  "debug"),
    (270, 50, "🏠菜单",  "menu"),
    (324, 50, "❌退出",  "quit"),
]
