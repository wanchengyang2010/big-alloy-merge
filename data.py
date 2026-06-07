"""Item tier definitions. Base radii at reference resolution 600×900.

Two modes:
  full — 17 elements (2222模式), 0-5 drop randomly
  lite — 11 elements (大西瓜模式), 0-4 drop randomly

set_active_mode(mode) switches the active TIERS list in-place.
All modules see changes because TIERS is the same list object.
"""

import random

# ---- 17 元素（2222 模式）----
TIERS_FULL = [
    #  Tier  Name      Radius  Color            Image        Points
    {"name": "嘟嘟 ☢️",  "radius": 9,   "color": (220, 60, 60),   "image": "0.png",  "points": 1},
    {"name": "张骞 🎦",  "radius": 12,  "color": (220, 100, 50),  "image": "1.png",  "points": 3},
    {"name": "党项 🔠",  "radius": 16,  "color": (220, 140, 50),  "image": "2.png",  "points": 6},
    {"name": "蟑螂 🪳",  "radius": 20,  "color": (200, 180, 50),  "image": "3.png",  "points": 10},
    {"name": "仓鼠 🐹",  "radius": 24,  "color": (140, 200, 60),  "image": "4.png",  "points": 15},
    {"name": "灰鼠 🐁",  "radius": 29,  "color": (60, 200, 80),   "image": "5.png",  "points": 21},
    {"name": "家畜 🐱",  "radius": 33,  "color": (50, 190, 160),  "image": "6.png",  "points": 28},
    {"name": "猴子 🐒",  "radius": 38,  "color": (50, 160, 210),  "image": "7.png",  "points": 36},
    {"name": "考拉 🐨",  "radius": 43,  "color": (60, 120, 220),  "image": "8.png",  "points": 45},
    {"name": "疯狗 🐕",  "radius": 48,  "color": (90, 80, 220),   "image": "9.png",  "points": 55},
    {"name": "阳阳 🐏",  "radius": 52,  "color": (150, 60, 210),  "image": "10.png", "points": 66},
    {"name": "马恕 🐎",  "radius": 58,  "color": (200, 55, 180),  "image": "11.png", "points": 78},
    {"name": "雪豹 🏐",  "radius": 63,  "color": (220, 55, 130),  "image": "12.png", "points": 91},
    {"name": "恐龙 🦖",  "radius": 69,  "color": (220, 70, 80),   "image": "13.png", "points": 105},
    {"name": "狒狒 🙉",  "radius": 74,  "color": (210, 100, 60),  "image": "14.png", "points": 120},
    {"name": "锐哥 🦌",  "radius": 80,  "color": (190, 140, 50),  "image": "15.png", "points": 136},
    {"name": "钇钾 🪙",  "radius": 87,  "color": (255, 80, 40),   "image": "16.png", "points": 200},
]

# ---- 11 元素（大西瓜模式）----
# 取原 17 元素的后 11 个（家畜→钇钾），重编号 0-10
# 只掉落 new 0-4（家畜~疯狗）
TIERS_LITE = [
    # 11元素半径，精确匹配 daxigua 水果/容器比例（507px 容器宽）
    {"name": "家畜 🐱",  "radius": 18,  "color": (50, 190, 160),  "image": "6.png",  "points": 28},
    {"name": "猴子 🐒",  "radius": 28,  "color": (50, 160, 210),  "image": "7.png",  "points": 36},
    {"name": "考拉 🐨",  "radius": 38,  "color": (60, 120, 220),  "image": "8.png",  "points": 45},
    {"name": "疯狗 🐕",  "radius": 42,  "color": (90, 80, 220),   "image": "9.png",  "points": 55},
    {"name": "阳阳 🐏",  "radius": 54,  "color": (150, 60, 210),  "image": "10.png", "points": 66},
    {"name": "马恕 🐎",  "radius": 64,  "color": (200, 55, 180),  "image": "11.png", "points": 78},
    {"name": "雪豹 🏐",  "radius": 68,  "color": (220, 55, 130),  "image": "12.png", "points": 91},
    {"name": "恐龙 🦖",  "radius": 91,  "color": (220, 70, 80),   "image": "13.png", "points": 105},
    {"name": "狒狒 🙉",  "radius": 108, "color": (210, 100, 60),  "image": "14.png", "points": 120},
    {"name": "锐哥 🦌",  "radius": 108, "color": (190, 140, 50),  "image": "15.png", "points": 136},
    {"name": "钇钾 🪙",  "radius": 144, "color": (255, 80, 40),   "image": "16.png", "points": 200},
]

# ---- Active tier set ----
TIERS: list[dict] = list(TIERS_FULL)
# Use list container so imports see mutations (int imports are value copies)
_MAX_DROP = [8]  # tiers 0-8 drop for full mode (物理掉落延迟后需提高)


def get_max_drop() -> int:
    return _MAX_DROP[0]


def set_active_mode(mode: str):
    """Switch active tier list. 'full' = 17 elements, 'lite' = 11 elements."""
    if mode == "full":
        TIERS.clear()
        TIERS.extend(TIERS_FULL)
        _MAX_DROP[0] = 5
    elif mode == "lite":
        TIERS.clear()
        TIERS.extend(TIERS_LITE)
        _MAX_DROP[0] = 4  # tiers 0-4 drop (5 types: 家畜~阳阳)


def random_drop_tier() -> int:
    """Equal-probability random tier from 0 to get_max_drop()."""
    return random.randint(0, get_max_drop())
