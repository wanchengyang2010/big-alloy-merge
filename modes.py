"""v2.0.0.0 模式系统 — ModeDefinition + ModeManager。

每个模式集成三类参数：
  LambertLiuTheory（数学）— 容器、半径、概率、初始序列
  JaneFlyThought（物理）— 重力、速度、质量、摩擦、弹性、旋转
  BurningIsm（艺术）— 图片、消息、背景、音效

ModeManager 负责持久化到 modes.json，管理 CRUD + 排序。
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any

from constants import get_user_data_dir

MODES_FILE = os.path.join(get_user_data_dir(), "modes.json")
MODES_DIR = os.path.join(get_user_data_dir(), "modes")

# ── Tier 定义 ──────────────────────────────────────────────

@dataclass
class TierDef:
    """单个 tier 的数学+物理+艺术定义。"""
    name: str               # "家畜 🐖"
    radius: int             # 参考分辨率下半径 (px)
    color: tuple[int, int, int]  # RGB
    points: int             # 合成得分
    drop_weight: float = 1.0     # 掉落概率权重
    # 物理（None = 继承模式默认值）
    mass: float | None = None          # 质量 (None→radius*10)
    friction: float | None = None      # 球间摩擦 (None→模式默认)
    elasticity: float | None = None    # 弹性系数 (None→模式默认)
    # 艺术
    image: str = ""         # 图片文件名 (如 "6.png")
    message: str = ""       # 合成时自定义消息
    sound: str = ""         # v2.2.0.0: 每级自定义音效（空=用默认映射）

    def to_dict(self) -> dict:
        d = asdict(self)
        d["color"] = list(self.color)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "TierDef":
        d = dict(d)  # shallow copy
        d["color"] = tuple(d["color"])
        return cls(**d)


# ── 默认 TIERS_FULL (17元素) ──────────────────────────────

DEFAULT_TIERS_FULL: list[TierDef] = [
    TierDef("西西 🕴️",  18,  (220, 60, 60),   1,  drop_weight=1.0, image="0.png", message="xiiiiii"),
    TierDef("张骞 🎗️",  24, (220, 100, 50),  3,  drop_weight=1.0, image="1.png"),
    TierDef("党项 🍩",  30, (220, 140, 50),  6,  drop_weight=1.0, image="2.png"),
    TierDef("蟑螂 🪳",  38, (200, 180, 50),  10, drop_weight=1.0, image="3.png"),
    TierDef("仓鼠 🐹",  44, (140, 200, 60),  15, drop_weight=1.0, image="4.png"),
    TierDef("灰鼠 🐁",  50, (60, 200, 80),   21, drop_weight=1.0, image="5.png"),
    TierDef("家畜 🐖",  58, (50, 190, 160),  28, drop_weight=1.0, image="6.png"),
    TierDef("猴子 🐒",  66, (50, 160, 210),  36, drop_weight=1.0, image="7.png"),
    TierDef("考拉 🐨",  74, (60, 120, 220),  45, drop_weight=1.0, image="8.png"),
    TierDef("疯狗 🐕",  84, (90, 80, 220),   55, drop_weight=1.0, image="9.png"),
    TierDef("阳阳 🐏",  94, (150, 60, 210),  66, drop_weight=1.0, image="10.png"),
    TierDef("马恕 🐎", 104, (200, 55, 180),  78, drop_weight=1.0, image="11.png"),
    TierDef("恐龙 🦖", 128, (220, 70, 80),  105, drop_weight=1.0, image="12.png"),
    TierDef("狒狒 🙉", 140, (210, 100, 60), 120, drop_weight=1.0, image="13.png"),
    TierDef("春宇 ♾️", 146, (200, 120, 55), 128, drop_weight=1.0, image="14.png", message="闭嘴吧啊"),
    TierDef("锐哥 🔪", 152, (190, 140, 50), 136, drop_weight=1.0, image="15.png"),
    TierDef("钇钾 🪙", 166, (255, 80, 40),  200, drop_weight=1.0, image="16.png"),
]

# ── 默认 TIERS_LITE (12元素, 统一编号5~16, v2.0.2.0) ──────────
# 数学物理参数顺次平移：新增5号(灰鼠)用旧6号(家畜)参数，
# 6号(家畜)用旧7号(猴子)参数…15号(锐哥)用旧16号(钇钾)参数，
# 16号(钇钾)全新扩大参数(r=168,pts=280)。图片/名称/颜色不变。

DEFAULT_TIERS_LITE: list[TierDef] = [
    TierDef("灰鼠 🐁",  18,  (60, 200, 80),   21, drop_weight=1.0, image="5.png",
            message="7+2吱吱吱！"),
    TierDef("家畜 🐖",  28,  (50, 190, 160),  36, drop_weight=1.0, image="6.png",
            message="该呀！"),
    TierDef("猴子 🐒",  38,  (50, 160, 210),  45, drop_weight=1.0, image="7.png",
            message=""),
    TierDef("考拉 🐨",  42,  (60, 120, 220),  55, drop_weight=1.0, image="8.png",
            message=""),
    TierDef("疯狗 🐕",  54,  (90, 80, 220),   66, drop_weight=1.0, image="9.png",
            message=""),
    TierDef("阳阳 🐏",  64,  (150, 60, 210),  78, drop_weight=1.0, image="10.png",
            message=""),
    TierDef("马恕 🐎",  68,  (200, 55, 180),  91, drop_weight=1.0, image="11.png",
            message=""),
    TierDef("恐龙 🦖", 108,  (220, 70, 80),  120, drop_weight=1.0, image="12.png",
            message=""),
    TierDef("狒狒 🙉", 108,  (210, 100, 60), 136, drop_weight=1.0, image="13.png",
            message=""),
    TierDef("春宇 ♾️", 126,  (200, 120, 55), 168, drop_weight=1.0, image="14.png",
            message="闭嘴吧啊"),
    TierDef("锐哥 🔪", 144,  (190, 140, 50), 200, drop_weight=1.0, image="15.png",
            message=""),
    TierDef("钇钾 🪙", 168,  (255, 80, 40),  280, drop_weight=1.0, image="16.png",
            message="不说！打倒钇钾合金！！！"),
]


# ── ModeDefinition ────────────────────────────────────────

@dataclass
class ModeDefinition:
    """一个完整游戏模式：数学+物理+艺术全部参数。"""
    id: str                             # "lite" | "full" | "custom_xxx"
    name: str                           # "轻量模式"
    builtin: bool = False               # 内置模式不可删除
    locked: bool = False                # 🔒 仅显示不可选
    order: int = 0                      # 排序位置

    # === LambertLiuTheory（数学） ===
    container_width: int = 507          # 参考分辨率下容器宽（等比例缩放基准）
    container_left: int = 46            # 容器左边界
    container_top: int = 60             # 容器顶边界
    container_bottom: int = 822         # 容器底边界
    drop_line_y: int = 84               # 掉落线Y
    overflow_line_y: int = 155          # 溢出线Y
    n_tiers: int = 11                   # 使用的 tier 数量（从尾部取）
    tiers: list[TierDef] = field(default_factory=list)
    initial_sequence: list[int] = field(default_factory=lambda: [0, 0, 1, 2, 2, 3])
    max_drop: int = 4                   # 随机掉落范围 0~max_drop

    # === JaneFlyThought（物理） ===
    gravity: float = 1800.0             # 重力加速度
    initial_vy: float = 1600.0          # 初始下坠速度
    damping: float = 0.0                # 球弹性 (0=完全非弹性)
    friction_ball: float = 0.20         # 球间接触摩擦系数 (v2.2.2.3: 不粘)
    friction_wall: float = 0.08         # 容器壁摩擦系数 (v2.2.2.3: 不粘壁)
    air_resistance: float = 0.0         # 空气阻力 (0=真空)
    elasticity_wall: float = 0.0        # 壁弹性
    drop_delay: float = 0.25            # 掉落冷却 (秒)
    overflow_time: float = 3.0          # 超线容忍时间 (秒)
    attract_force: float = 0.0          # 磁力吸引强度
    attract_range: float = 0.0          # 磁力触发距离
    rotation_enabled: bool = True       # 旋转物理 (v2.0新增)
    angular_damping: float = 0.92       # 角速度每秒保留系数 (v2.3.0.0: 0.92 更快衰减)
    wall_rotational_friction: float = 0.03  # 壁面旋转摩擦 (v2.2.2.3: 触壁不杀旋转)
    dynamic_drop_enabled: bool = False  # v2.3.0.0: 动态掉落（合成N→解锁N-2）

    # === BurningIsm（艺术） ===
    background_image: str = ""          # 背景图文件名 ("" = 无)
    background_overlay_alpha: int = 140 # 背景图上方暗色遮罩 (0-255)
    merge_sound: str = ""               # 合成音效文件名
    victory_sound: str = ""             # 胜利音效文件名 (短音效, Sound)
    victory_music: str = ""             # 胜利音乐文件名 (长音乐, mixer.music 流式播放)

    @property
    def container_right(self) -> int:
        return self.container_left + self.container_width

    def to_dict(self) -> dict:
        d = asdict(self)
        d["tiers"] = [t.to_dict() for t in self.tiers]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "ModeDefinition":
        d = dict(d)
        d["tiers"] = [TierDef.from_dict(t) for t in d.get("tiers", [])]
        return cls(**{k: v for k, v in d.items() if k != "container_right"})


# ── 默认模式工厂 ──────────────────────────────────────────

def _make_lite_mode() -> ModeDefinition:
    """轻量模式 (mode 0)：12元素 5~16 + JFT2 + theme.png 背景。
    v2.0.2.0: 统一编号5~16，容器480×135溢线，整体难度大幅提高。
    """
    return ModeDefinition(
        id="lite", name="轻量模式", builtin=True, locked=False, order=0,
        container_width=480,
        container_left=46, container_top=60, container_bottom=822,
        drop_line_y=84, overflow_line_y=135,
        n_tiers=12,  # v2.0.2.0: 5~16号共12个
        tiers=list(DEFAULT_TIERS_LITE),
        initial_sequence=[0, 0, 1, 2, 2, 3],  # 灰鼠,灰鼠,家畜,猴子,猴子,考拉
        max_drop=5,  # v2.0.2.0: 掉落0~5号(灰鼠~阳阳)
        gravity=1800.0, initial_vy=1600.0,
        damping=0.0, friction_ball=0.20, friction_wall=0.08,
        air_resistance=0.0, elasticity_wall=0.0,
        drop_delay=0.25, overflow_time=3.0,
        attract_force=0.0, attract_range=0.0,
        rotation_enabled=True,
        angular_damping=0.92,
        wall_rotational_friction=0.03,
        background_image="theme.png",
        background_overlay_alpha=140,
        victory_music="victory.mp3",
    )


def _make_full_mode() -> ModeDefinition:
    """完整模式 (mode 1)：17元素 0~16，lite 级难度。
    v2.0.4.0: 解锁，物理参数对齐轻量模式（同难度），17元素全链 0→16。
    """
    return ModeDefinition(
        id="full", name="完整模式", builtin=True, locked=False, order=1,
        container_width=540,
        container_left=46, container_top=60, container_bottom=822,
        drop_line_y=84, overflow_line_y=179,
        n_tiers=17,
        tiers=list(DEFAULT_TIERS_FULL),
        initial_sequence=[0, 0, 1, 2, 2, 3, 0, 1, 2, 3, 4, 5],
        max_drop=5,  # 掉落 0~5 号（西西~灰鼠）
        # 物理 = lite 级（同难度）
        gravity=1800.0, initial_vy=1600.0,
        damping=0.0, friction_ball=0.20, friction_wall=0.08,
        air_resistance=0.0, elasticity_wall=0.0,
        drop_delay=0.25, overflow_time=3.0,
        attract_force=0.0, attract_range=0.0,
        rotation_enabled=True,
        angular_damping=0.92,
        wall_rotational_friction=0.03,
        dynamic_drop_enabled=True,  # v2.3.0.0: 全模式启用动态掉落
        background_image="theme.png",
        background_overlay_alpha=140,
        victory_music="victory.mp3",
    )


def _make_full_debug_mode() -> ModeDefinition:
    """完整调试模式 (v2.0.4.0)：17元素 + 实时参数面板。密码保护。"""
    md = _make_full_mode()
    md.id = "full_debug"
    md.name = "完整调试"
    md.builtin = True
    md.locked = False
    md.order = 4
    md.background_image = ""  # 调试无背景以免干扰
    return md


def _make_demo_mode() -> ModeDefinition:
    """演示模式：同轻量模式，但由 AI 控制。"""
    md = _make_lite_mode()
    md.id = "demo"
    md.name = "演示模式"
    md.builtin = True
    md.locked = False
    md.order = 2
    md.background_image = ""  # demo 不设背景以免干扰观看
    return md


def _make_debug_mode() -> ModeDefinition:
    """调试模式 (mode 3)：同轻量模式12元素，可调参数。密码保护。"""
    md = _make_lite_mode()
    md.id = "debug"
    md.name = "调试模式"
    md.builtin = True
    md.locked = False
    md.order = 3
    md.background_image = ""  # 调试无背景以免干扰
    return md


# ── ModeManager ───────────────────────────────────────────

class ModeManager:
    """模式管理器：加载/保存/CRUD/排序。单例。"""

    _instance: "ModeManager | None" = None

    def __init__(self):
        self.modes: dict[str, ModeDefinition] = {}
        self.active_id: str = "lite"
        if not os.path.isdir(MODES_DIR):
            os.makedirs(MODES_DIR, exist_ok=True)
        self.load()

    @classmethod
    def instance(cls) -> "ModeManager":
        """获取全局单例。"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── 持久化 ──

    def load(self):
        """从 modes.json 加载。不存在则从内置默认创建。
        版本变更时强制刷新内置模式参数。
        """
        _CURRENT_VERSION = "v2.3.0.0"
        if os.path.isfile(MODES_FILE):
            try:
                with open(MODES_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                saved_version = data.get("version", "v2.0.0.0")
                self.active_id = data.get("active_mode", "lite")
                self.modes = {}
                for md in data.get("modes", []):
                    mode = ModeDefinition.from_dict(md)
                    self.modes[mode.id] = mode
                # v2.0.0.0: 迁移旧 q_custom.json
                self._migrate_q_custom()
                # 确保内置模式始终存在
                self._ensure_builtins()
                # 版本升级时强制刷新内置模式参数
                if saved_version != _CURRENT_VERSION:
                    self._refresh_builtins()
                return
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        # 首次启动：从内置默认创建
        self._create_defaults()
        # 迁移旧配置（首次启动时也可能有）
        self._migrate_q_custom()

    def save(self):
        """持久化到 modes.json。"""
        data = {
            "version": "v2.3.0.0",
            "active_mode": self.active_id,
            "modes": [m.to_dict() for m in sorted(
                self.modes.values(), key=lambda x: x.order
            )],
        }
        try:
            with open(MODES_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def _create_defaults(self):
        self.modes.clear()
        for factory in [_make_lite_mode, _make_full_mode, _make_demo_mode,
                        _make_debug_mode, _make_full_debug_mode]:
            md = factory()
            self.modes[md.id] = md
        self.active_id = "lite"
        self.save()

    def _ensure_builtins(self):
        """确保内置模式存在（升级/损坏修复）。不覆盖已有参数。"""
        builtins = {
            "lite": _make_lite_mode,
            "full": _make_full_mode,
            "demo": _make_demo_mode,
            "debug": _make_debug_mode,
            "full_debug": _make_full_debug_mode,
        }
        for bid, factory in builtins.items():
            if bid not in self.modes:
                self.modes[bid] = factory()
        self.save()

    def _refresh_builtins(self):
        """版本升级时强制用新工厂参数覆盖内置模式（保留非内置模式不变）。"""
        builtins = {
            "lite": _make_lite_mode,
            "full": _make_full_mode,
            "demo": _make_demo_mode,
            "debug": _make_debug_mode,
            "full_debug": _make_full_debug_mode,
        }
        for bid, factory in builtins.items():
            new_md = factory()
            if bid in self.modes:
                old_md = self.modes[bid]
                # 保留 order 不变
                new_md.order = old_md.order
            self.modes[bid] = new_md
        self.save()

    def _migrate_q_custom(self):
        """v2.0.0.0: 将旧 q_custom.json 迁移为自定义模式。"""
        q_path = os.path.join(get_user_data_dir(), "q_custom.json")
        if not os.path.isfile(q_path):
            return
        try:
            with open(q_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            old_tiers = data.get("tiers", [])
            if not old_tiers:
                return
            # 从 lite 模式复制创建
            base = self.modes.get("lite") or _make_lite_mode()
            new_mode = ModeDefinition.from_dict(base.to_dict())
            new_mode.id = "qself"
            new_mode.name = "Q自我（已迁移）"
            new_mode.builtin = False
            new_mode.locked = False
            max_order = max((m.order for m in self.modes.values()), default=0)
            new_mode.order = max_order + 1
            # 覆盖 tiers
            for i, td in enumerate(old_tiers):
                if i < len(new_mode.tiers):
                    new_mode.tiers[i].name = td.get("name", new_mode.tiers[i].name)
                    new_mode.tiers[i].image = td.get("image", new_mode.tiers[i].image)
                    new_mode.tiers[i].message = td.get("message", "")
            self.modes[new_mode.id] = new_mode
            # 重命名旧文件（备份而非删除）
            bak = q_path + ".bak"
            os.rename(q_path, bak)
            self.save()
        except (json.JSONDecodeError, OSError, KeyError):
            pass

    # ── 查询 ──

    def get(self, mode_id: str) -> ModeDefinition | None:
        return self.modes.get(mode_id)

    def get_active(self) -> ModeDefinition:
        return self.modes.get(self.active_id, self.modes["lite"])

    def list_all(self) -> list[ModeDefinition]:
        return sorted(self.modes.values(), key=lambda m: m.order)

    def list_playable(self) -> list[ModeDefinition]:
        """可游玩的模式（未锁定）。"""
        return [m for m in self.list_all() if not m.locked]

    # ── 操作 ──

    def set_active(self, mode_id: str):
        if mode_id in self.modes and not self.modes[mode_id].locked:
            self.active_id = mode_id
            self.save()

    def create(self, name: str, base_mode_id: str = "lite") -> ModeDefinition | None:
        """从 base_mode 复制创建新自定义模式。"""
        base = self.modes.get(base_mode_id)
        if base is None:
            return None
        new_id = f"custom_{uuid.uuid4().hex[:8]}"
        new_mode = ModeDefinition.from_dict(base.to_dict())
        new_mode.id = new_id
        new_mode.name = name
        new_mode.builtin = False
        new_mode.locked = False
        # 排在最后
        max_order = max((m.order for m in self.modes.values()), default=0)
        new_mode.order = max_order + 1
        self.modes[new_id] = new_mode
        self.save()
        return new_mode

    def delete(self, mode_id: str) -> bool:
        """删除自定义模式。内置模式不可删。"""
        md = self.modes.get(mode_id)
        if md is None or md.builtin:
            return False
        del self.modes[mode_id]
        # 如果删除的是活跃模式，切回 lite
        if self.active_id == mode_id:
            self.active_id = "lite"
        self.save()
        return True

    def reorder(self, id_list: list[str]):
        """批量更新排序顺序。id_list 按新顺序排列。"""
        for i, mid in enumerate(id_list):
            if mid in self.modes:
                self.modes[mid].order = i
        self.save()

    def update(self, mode_id: str, **kwargs):
        """更新模式参数。kwargs: field_name=new_value 或嵌套路径。"""
        md = self.modes.get(mode_id)
        if md is None or md.builtin:
            return
        for key, value in kwargs.items():
            if hasattr(md, key):
                setattr(md, key, value)
        self.save()

    def update_tier(self, mode_id: str, tier_idx: int, **kwargs):
        """更新单个 tier 参数。"""
        md = self.modes.get(mode_id)
        if md is None or md.builtin:
            return
        if 0 <= tier_idx < len(md.tiers):
            td = md.tiers[tier_idx]
            for key, value in kwargs.items():
                if hasattr(td, key):
                    setattr(td, key, value)
            self.save()

    def duplicate(self, mode_id: str) -> ModeDefinition | None:
        """复制模式（含自定义模式）。"""
        md = self.modes.get(mode_id)
        if md is None:
            return None
        new_id = f"custom_{uuid.uuid4().hex[:8]}"
        new_mode = ModeDefinition.from_dict(md.to_dict())
        new_mode.id = new_id
        new_mode.name = f"{md.name} (副本)"
        new_mode.builtin = False
        new_mode.locked = False
        max_order = max((m.order for m in self.modes.values()), default=0)
        new_mode.order = max_order + 1
        self.modes[new_id] = new_mode
        self.save()
        return new_mode

    def rename(self, mode_id: str, new_name: str):
        md = self.modes.get(mode_id)
        if md and not md.builtin:
            md.name = new_name
            self.save()


# ── 全局单例 ──

mode_manager = ModeManager.instance()
