"""Item tier definitions. Base radii at reference resolution 600×900.

Two modes:
  full — 17 elements (2222模式), 0-5 drop randomly
  lite — 12 elements (大西瓜模式), 0-5 drop randomly
  qself — 12 elements (Q自我模式), custom images/names/messages

set_active_mode(mode) switches the active TIERS list in-place.
All modules see changes because TIERS is the same list object.
"""

import json
import os
import random

from constants import get_user_data_dir

# ---- 17 元素（2222 模式）----
TIERS_FULL = [
    #  Tier  Name      Radius  Color            Image        Points   v2.3.0.0: 嘟嘟→西西, 删雪豹, 春宇插入锐哥前
    {"name": "西西 🕴️",  "radius": 18,  "color": (220, 60, 60),   "image": "0.png",  "points": 1},
    {"name": "张骞 🎗️",  "radius": 24,  "color": (220, 100, 50),  "image": "1.png",  "points": 3},
    {"name": "党项 🍩",  "radius": 30,  "color": (220, 140, 50),  "image": "2.png",  "points": 6},
    {"name": "蟑螂 🪳",  "radius": 38,  "color": (200, 180, 50),  "image": "3.png",  "points": 10},
    {"name": "仓鼠 🐹",  "radius": 44,  "color": (140, 200, 60),  "image": "4.png",  "points": 15},
    {"name": "灰鼠 🐁",  "radius": 50,  "color": (60, 200, 80),   "image": "5.png",  "points": 21},
    {"name": "家畜 🐖",  "radius": 58,  "color": (50, 190, 160),  "image": "6.png",  "points": 28},
    {"name": "猴子 🐒",  "radius": 66,  "color": (50, 160, 210),  "image": "7.png",  "points": 36},
    {"name": "考拉 🐨",  "radius": 74,  "color": (60, 120, 220),  "image": "8.png",  "points": 45},
    {"name": "疯狗 🐕",  "radius": 84,  "color": (90, 80, 220),   "image": "9.png",  "points": 55},
    {"name": "阳阳 🐏",  "radius": 94,  "color": (150, 60, 210),  "image": "10.png", "points": 66},
    {"name": "马恕 🐎",  "radius": 104, "color": (200, 55, 180),  "image": "11.png", "points": 78},
    {"name": "恐龙 🦖",  "radius": 128, "color": (220, 70, 80),   "image": "12.png", "points": 105},
    {"name": "狒狒 🙉",  "radius": 140, "color": (210, 100, 60),  "image": "13.png", "points": 120},
    {"name": "春宇 ♾️",  "radius": 146, "color": (200, 120, 55),  "image": "14.png", "points": 128},
    {"name": "锐哥 🔪",  "radius": 152, "color": (190, 140, 50),  "image": "15.png", "points": 136},
    {"name": "钇钾 🪙",  "radius": 166, "color": (255, 80, 40),   "image": "16.png", "points": 200},
]

# ---- 12 元素（大西瓜模式 v2.0.2.0）----
# 统一编号 5~16（全模式17元素的后12个），数学物理参数顺次平移
# 掉落 0~5（灰鼠~阳阳）
TIERS_LITE = [
    {"name": "灰鼠 🐁",  "radius": 18,  "color": (60, 200, 80),   "image": "5.png",  "points": 21},
    {"name": "家畜 🐖",  "radius": 28,  "color": (50, 190, 160),  "image": "6.png",  "points": 36},
    {"name": "猴子 🐒",  "radius": 38,  "color": (50, 160, 210),  "image": "7.png",  "points": 45},
    {"name": "考拉 🐨",  "radius": 42,  "color": (60, 120, 220),  "image": "8.png",  "points": 55},
    {"name": "疯狗 🐕",  "radius": 54,  "color": (90, 80, 220),   "image": "9.png",  "points": 66},
    {"name": "阳阳 🐏",  "radius": 64,  "color": (150, 60, 210),  "image": "10.png", "points": 78},
    {"name": "马恕 🐎",  "radius": 68,  "color": (200, 55, 180),  "image": "11.png", "points": 91},
    {"name": "恐龙 🦖",  "radius": 108, "color": (220, 70, 80),   "image": "12.png", "points": 120},
    {"name": "狒狒 🙉",  "radius": 108, "color": (210, 100, 60),  "image": "13.png", "points": 136},
    {"name": "春宇 ♾️",  "radius": 126, "color": (200, 120, 55),  "image": "14.png", "points": 168},
    {"name": "锐哥 🔪",  "radius": 144, "color": (190, 140, 50),  "image": "15.png", "points": 200},
    {"name": "钇钾 🪙",  "radius": 168, "color": (255, 80, 40),   "image": "16.png", "points": 280},
]

# ---- Active tier set ----
TIERS: list[dict] = list(TIERS_FULL)
# Use list container so imports see mutations (int imports are value copies)
_MAX_DROP = [8]  # tiers 0-8 drop for full mode (物理掉落延迟后需提高)

# ---- Q自我模式自定义数据 ----
TIERS_Q_CUSTOM: list[dict] = []
_Q_CUSTOM_PATH = os.path.join(get_user_data_dir(), "q_custom.json")


def load_q_custom_tiers() -> list[dict]:
    """加载 Q自我模式自定义等级配置。
    若 q_custom.json 不存在，从 TIERS_LITE 复制默认值并写入。
    返回 tier dict 列表。
    """
    global TIERS_Q_CUSTOM
    default = [
        {
            "name": t["name"],
            "radius": t["radius"],
            "color": t["color"],
            "image": t["image"],
            "points": t["points"],
            "message": "",
        }
        for t in TIERS_LITE
    ]
    try:
        if os.path.isfile(_Q_CUSTOM_PATH):
            with open(_Q_CUSTOM_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            tiers = loaded.get("tiers", [])
            # 确保有12项，用默认值补全
            result = []
            for i in range(12):
                if i < len(tiers):
                    t = tiers[i]
                    result.append({
                        "name": t.get("name", default[i]["name"]),
                        "radius": t.get("radius", default[i]["radius"]),
                        "color": t.get("color", default[i]["color"]),
                        "image": t.get("image", default[i]["image"]),
                        "points": t.get("points", default[i]["points"]),
                        "message": t.get("message", ""),
                    })
                else:
                    result.append(default[i])
            TIERS_Q_CUSTOM = result
        else:
            # 首次启动：写入默认配置
            TIERS_Q_CUSTOM = default
            _save_q_custom()
    except (json.JSONDecodeError, OSError):
        TIERS_Q_CUSTOM = default
    return TIERS_Q_CUSTOM


def _save_q_custom():
    """持久化 q_custom.json。"""
    try:
        with open(_Q_CUSTOM_PATH, "w", encoding="utf-8") as f:
            json.dump({"tiers": TIERS_Q_CUSTOM}, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def save_q_custom_tiers():
    """外部调用：保存当前 TIERS_Q_CUSTOM 到文件。"""
    _save_q_custom()


# v2.2.0.0: 每级合成/掉落音效映射（0~15，16 号由胜利音乐系统处理）
# 用相对路径：开发时 CWD 解析，PyInstaller 下 resource_path() 解析
_SFX_PREFIX = "music/游戏音效备选"
TIER_MERGE_SOUNDS = [
    f"{_SFX_PREFIX}/doo-doo-hast.mp3",                                                    # 0 西西 (原嘟嘟音效)
    f"{_SFX_PREFIX}/mystical-atmosphere-7.mp3",                                           # 1 张骞
    f"{_SFX_PREFIX}/sigh-through-the-nose.mp3",                                           # 2 党项
    f"{_SFX_PREFIX}/cockroach-squeaks.mp3",                                               # 3 蟑螂
    f"{_SFX_PREFIX}/duck-called-apple-phone-comes-with-sound-game-sound-alert.mp3",       # 4 仓鼠
    f"{_SFX_PREFIX}/loud-squeak.mp3",                                                     # 5 灰鼠
    f"{_SFX_PREFIX}/virtuoso-swings-of-the-hussar-saber.mp3",                             # 6 家畜
    f"{_SFX_PREFIX}/the-sound-of-a-man-vomiting-cartoon.mp3",                             # 7 猴子
    f"{_SFX_PREFIX}/the-rough-squeak-of-a-child39s-pipe.mp3",                             # 8 考拉
    f"{_SFX_PREFIX}/big-guard-dog-barking.mp3",                                           # 9 疯狗
    f"{_SFX_PREFIX}/goat-bleats.mp3",                                                     # 10 阳阳
    f"{_SFX_PREFIX}/neighing-horse.mp3",                                                  # 11 马恕
    f"{_SFX_PREFIX}/prehistoric-dinosaur-sound.mp3",                                      # 12 恐龙 (原13→12)
    f"{_SFX_PREFIX}/baboon-voice-sound.mp3",                                              # 13 狒狒 (原14→13)
    f"{_SFX_PREFIX}/snowball-throw.mp3",                                                  # 14 春宇 (用原雪豹音效)
    f"{_SFX_PREFIX}/game-skills-release-archery.mp3",                                     # 15 锐哥
    # 16 钇钾：L'Internationale + war-shootout-shells（game.py _play_victory_music 处理）
]


def get_max_drop() -> int:
    return _MAX_DROP[0]


def set_active_mode(mode: str):
    """Switch active tier list. 'full' = 17 elements, 'lite' = 11 elements, 'qself' = Q自定义."""
    if mode == "full":
        TIERS.clear()
        TIERS.extend(TIERS_FULL)
        _MAX_DROP[0] = 5
    elif mode == "lite":
        TIERS.clear()
        TIERS.extend(TIERS_LITE)
        _MAX_DROP[0] = 5  # v2.0.2.0: tiers 0-5 drop (6 types: 灰鼠~阳阳)
    elif mode == "qself":
        if not TIERS_Q_CUSTOM:
            load_q_custom_tiers()
        TIERS.clear()
        TIERS.extend(TIERS_Q_CUSTOM)
        _MAX_DROP[0] = 4  # 同lite: tiers 0-4 drop


def set_active_tiers_from_mode(mode_def):
    """从 ModeDefinition 填充 TIERS 列表和掉落范围（v2.0.0.0）。

    mode_def: modes.ModeDefinition 实例。
    """
    TIERS.clear()
    for td in mode_def.tiers:
        TIERS.append({
            "name": td.name,
            "radius": td.radius,
            "color": td.color,
            "image": td.image,
            "points": td.points,
            "mass": td.mass,
            "friction": td.friction,
            "elasticity": td.elasticity,
            "message": td.message,
            "sound": td.sound,
        })
    _MAX_DROP[0] = mode_def.max_drop


def random_drop_tier() -> int:
    """Equal-probability random tier from 0 to get_max_drop()."""
    return random.randint(0, get_max_drop())
