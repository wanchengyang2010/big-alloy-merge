"""Game state — items, physics, merge logic, scoring, game-over."""

import os
import json
import random

import pygame
import constants
from constants import (
    VERSION,
    DROP_LINE_Y, OVERFLOW_TIME,
    MERGE_COOLDOWN, COLLISION_PASSES, CELEBRATION_DURATION,
    SLEEP_VELOCITY, SLEEP_SETTLE_TIME, MERGE_TOLERANCE,
    DYNAMIC_DROP_ENABLED, DYNAMIC_DROP_UNLOCK_OFFSET,
    DYNAMIC_DROP_RATE_LIMIT, DYNAMIC_DROP_RATE_LIMIT_TIGHT,
    s, get_scale, resource_path, get_user_data_dir,
)
from data import TIERS, get_max_drop, random_drop_tier, set_active_mode, set_active_tiers_from_mode, TIER_MERGE_SOUNDS
from item import Item
from physics import (
    circles_overlap, circles_near, resolve_collision,
    apply_gravity, apply_friction, apply_angular_damping,
    wall_clamp, apply_attraction, apply_sleep,
    SpatialGrid,
)
from modes import mode_manager, ModeDefinition

# v2.0.0.0: 音效系统初始化
try:
    import pygame.mixer as _mixer
    _mixer.init()
    _SOUND_AVAILABLE = True
except Exception:
    _SOUND_AVAILABLE = False

# 音效缓存
_sound_cache: dict[str, object] = {}


def _play_sound(filename: str):
    """播放音效文件。_sound_cache 缓存已加载的 Sound 对象。"""
    global _sound_cache, _sound_enabled
    if not _SOUND_AVAILABLE or not filename or not _sound_enabled:
        return
    if filename not in _sound_cache:
        paths = [
            os.path.join(os.getcwd(), filename),
            os.path.join(os.getcwd(), "modes", filename),
            os.path.join(get_user_data_dir(), filename),
            os.path.join(get_user_data_dir(), "modes", filename),
            resource_path(f"assets/{filename}"),
            resource_path(filename),
        ]
        for p in paths:
            if os.path.isfile(p):
                try:
                    _sound_cache[filename] = _mixer.Sound(p)
                    break
                except Exception:
                    continue
        else:
            _sound_cache[filename] = None  # 标记已尝试加载
            return
    snd = _sound_cache.get(filename)
    if snd is not None:
        try:
            snd.play()
        except Exception:
            pass


def _play_tier_sound(tier: int):
    """v2.2.0.0: 播放指定 tier 的合成/掉落音效。"""
    global _sound_enabled
    if not _SOUND_AVAILABLE or not _sound_enabled:
        return
    if 0 <= tier < len(TIER_MERGE_SOUNDS):
        _play_sound(TIER_MERGE_SOUNDS[tier])


# v2.3.0.0: 可写文件放 %APPDATA%（安装到 Program Files 无需管理员权限）
_HIGHSCORE_RESOURCE = resource_path("highscore.txt")
HIGHSCORE_FILE = os.path.join(get_user_data_dir(), "highscore.txt")
SAVEGAME_FILE = os.path.join(get_user_data_dir(), "savegame.json")  # 旧版兼容
MAX_HISTORY = 20

# v2.1.0.0: 每个模式独立存档
def _save_path(mode_id: str) -> str:
    return os.path.join(get_user_data_dir(), f"savegame_{mode_id}.json")


# ── v2.2.0.0: 音频设置持久化 ──────────────────────────────

AUDIO_SETTINGS_FILE = os.path.join(get_user_data_dir(), "audio_settings.json")
_sound_enabled = True  # 默认开


def load_audio_settings() -> dict:
    """加载音频设置文件。"""
    global _sound_enabled
    try:
        if os.path.isfile(AUDIO_SETTINGS_FILE):
            with open(AUDIO_SETTINGS_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            _sound_enabled = data.get("sound_enabled", True)
    except Exception:
        _sound_enabled = True
    apply_sound_state()
    return {"sound_enabled": _sound_enabled}


def save_audio_settings():
    """保存音频设置到文件。"""
    try:
        with open(AUDIO_SETTINGS_FILE, "w", encoding="utf-8") as fh:
            json.dump({"sound_enabled": _sound_enabled}, fh)
    except Exception:
        pass


def apply_sound_state():
    """根据 _sound_enabled 设置全局音量。"""
    vol = 1.0 if _sound_enabled else 0.0
    try:
        if _SOUND_AVAILABLE:
            _mixer.music.set_volume(vol)
    except Exception:
        pass


def toggle_sound() -> bool:
    """切换声音开关，返回新状态。"""
    global _sound_enabled
    _sound_enabled = not _sound_enabled
    apply_sound_state()
    save_audio_settings()
    return _sound_enabled


class Game:
    def __init__(self, mode_id: str = "lite"):
        # v2.0.0.0: 从 ModeDefinition 获取所有参数
        self.mode_def = mode_manager.get(mode_id)
        if self.mode_def is None:
            self.mode_def = mode_manager.get("lite")
        self.mode_id = self.mode_def.id
        set_active_tiers_from_mode(self.mode_def)
        self._initial_vy = 0.0
        self._apply_mode_physics()
        self.items: list[Item] = []
        self.score = 0
        self.high_score = 0
        self.score_history: list[int] = []
        self._load_high_score()
        self.merge_messages: dict[int, str] = {}
        self._load_messages()
        self.game_over = False
        self.drop_cooldown = 0.0
        self.celebration_until = 0.0
        self.merge_effects: list[tuple[float, float, int, float]] = []
        self.text_popups: list[tuple[float, float, str, float]] = []
        self._scale = get_scale()

        self.debug_tier: int | None = None
        self.debug_weights: list[int] | None = None
        self.debug_tainted = False
        self.debug_allowed = False
        self._lite_drop_seq = 0

        # v2.3.0.0: 动态掉落系统（仅 full/full_debug 模式）
        # 必须在 _random_tier() 之前初始化
        self._dynamic_drop = self.mode_def.dynamic_drop_enabled
        self._highest_synthesized = 0       # 已合成最高等级
        self._dynamic_max_drop = self.mode_def.max_drop  # 动态最大掉落
        self._drop_counter = 0              # 全局掉落计数器
        self._rate_limit_last = {}          # {tier: last_drop_at_counter}
        self._rate_limit_interval = {}      # {tier: K balls between drops}

        self.current_tier = self._random_tier()

        # v2.0.4.0: 完整调试模式
        self._full_debug = (self.mode_id == "full_debug")
        self.debug_panel_open = self._full_debug  # 完整调试默认打开面板
        self._editing_initial_sequence = False     # 编辑初始序列标志

        # v2.2.0.0: 音频系统重构
        load_audio_settings()                      # 加载持久化声音开关
        self._music_tier = -1                      # 当前背景音乐对应 tier
        self._current_music_file = ""              # 当前播放的音乐路径

        # Scaled container bounds
        self._update_bounds()

    # ---- Public API ----

    def drop(self, mouse_x):
        """Spawn current item at mouse_x (clamped to container)."""
        if self.game_over or self.drop_cooldown > 0.0:
            return
        if self.current_tier is None and self.debug_tier is None:
            return  # 球尚未生成

        drop_tier = self.debug_tier if self.debug_tier is not None else self.current_tier
        r = TIERS[drop_tier]["radius"] * self._scale
        x = max(self.box_left + r, min(self.box_right - r, float(mouse_x)))
        y = s(constants.DROP_LINE_Y)

        item = Item(x, y, drop_tier, self._scale)
        # Apply initial downward velocity (daxigua reference: strong push)
        if self._initial_vy > 0:
            item.vy = s(self._initial_vy)
        self.items.append(item)

        # v2.2.0.0: 掉落音效
        _play_tier_sound(drop_tier)

        if self.debug_tier is not None:
            # 调试锁定：等级不变，冷却一样
            self.drop_cooldown = constants.DROP_DELAY
            self.current_tier = self.debug_tier  # always ready
        else:
            self.current_tier = None  # 消耗，冷却结束后再生成
            self.drop_cooldown = constants.DROP_DELAY

    def update(self, dt):
        """Advance game state by dt seconds.
        v2.0.4.1: 物理子步长 — 小球不再隧穿大球。
        """
        if self.game_over:
            return

        dt = min(dt, 0.05)  # cap for stability
        self.drop_cooldown = max(0.0, self.drop_cooldown - dt)

        # 庆祝特效计时（不阻止游戏逻辑）
        if self.celebration_until > 0.0:
            self.celebration_until -= dt
            if self.celebration_until < 0.0:
                self.celebration_until = 0.0

        pass  # v2.2.0.0: 背景音乐循环播放，无需检测自然结束

        # 冷却结束 → 生成下一个球
        if self.current_tier is None and self.drop_cooldown <= 0.0:
            self.current_tier = self._random_tier()

        # Decay visual effects (once per frame)
        self._update_effects(dt)

        # 1. Tick cooldowns (once per frame)
        for item in self.items:
            if item.merge_cooldown > 0.0:
                item.merge_cooldown -= dt
            if item.spawn_protect > 0.0:
                item.spawn_protect -= dt

        # 2. Game over check (once per frame, before gravity)
        self._check_game_over(dt)

        # ═══ 3-7. 物理子步长 (v2.0.4.1) ═══
        # 小球模式下每帧移动量可能超过自身半径 → 隧穿。
        # 子步长确保每步移动不超过 min_radius * 0.35
        n_sub = self._compute_substeps(dt)
        sub_dt = dt / n_sub

        for _ in range(n_sub):
            # 3. Gravity + friction + position
            for item in self.items:
                if item.alive:
                    apply_gravity(item, sub_dt)
                    apply_friction(item)
                    item.x += item.vx * sub_dt
                    item.y += item.vy * sub_dt

            # Rebuild spatial grid (positions changed)
            grid = self._build_grid()

            # 4. Magnetic attraction
            self._apply_attraction(sub_dt, grid)

            # 5. Collision resolution
            self._resolve_collisions(grid, dt)

            # 6. Wall clamp (after collision, catch any push-out)
            for item in self.items:
                if item.alive:
                    wall_clamp(item, self.box_left, self.box_right,
                               self.box_top, self.box_bottom, dt)

            # 7. Merge check
            self._check_merges(grid)

        # 8. 睡眠 + 角速度衰减（每帧一次，用完整 dt）
        for item in self.items:
            if item.alive:
                apply_sleep(item, dt)
                apply_angular_damping(item, dt)

    def _compute_substeps(self, dt: float) -> int:
        """v2.0.4.1: 计算物理子步数，防止小球隧穿。
        基于最小球半径和最大可能速度：每子步移动 ≤ 0.35×半径。
        """
        import math as _math
        # 最小球半径（来自 TIERS 定义，缩放后）
        min_r = min((t.radius for t in self.mode_def.tiers), default=18)
        min_r_scaled = min_r * self._scale
        if min_r_scaled <= 0:
            return 1
        # 最大可能速度：自由落体从顶到底 + 初始速度（缩放后）
        g = s(constants.GRAVITY)
        fall_dist = s(constants.CONTAINER_BOTTOM - constants.DROP_LINE_Y)
        freefall_v = _math.sqrt(max(0, 2 * g * fall_dist))
        max_v = max(freefall_v, s(self._initial_vy), 1.0)
        # 每帧最大移动距离
        move_per_frame = max_v * dt
        # 子步数：确保每步移动 ≤ 0.35×最小半径
        return max(1, int(move_per_frame / (min_r_scaled * 0.35)) + 1)

    def restart(self):
        self.items.clear()
        self.merge_effects.clear()
        self.text_popups.clear()
        self.score = 0
        self.game_over = False
        self.drop_cooldown = 0.0
        self.celebration_until = 0.0
        self.debug_tainted = False
        self.stop_music()  # v2.0.3.0: 重开时停止音乐
        self.current_tier = self._random_tier()

    def rescale(self, new_scale: float):
        """Update all radii and bounds after window resize."""
        self._scale = new_scale
        self._update_bounds()
        for item in self.items:
            item.compute_radius(new_scale)

    # ---- Music (v2.2.0.0) ----

    # 背景音乐文件（相对 CWD 路径，PyInstaller 下自动转 resource_path）
    _BG_MUSIC = [
        (10, "music/Two Steps From Hell - Victory.mp3"),
        (13, "music/Two Steps From Hell、Merethe Soltvedt - Impossible.mp3"),
        (15, "music/Two Steps From Hell、Merethe Soltvedt - Impossible.mp3"),
    ]
    _VICTORY_MUSIC = "music/Çeşitli Sanatçılar - L'internationale.mp3"
    _VICTORY_SFX = "music/游戏音效备选/war-shootout-shells.mp3"
    _UNITY_MUSIC = "music/TheFatRat - Unity.mp3"

    @staticmethod
    def _resolve_music_path(rel_path: str) -> str | None:
        """解析音乐文件路径：CWD → _MEIPASS → assets/ 兜底。"""
        # 1) CWD 直接路径
        cwd_path = os.path.join(os.getcwd(), rel_path)
        if os.path.isfile(cwd_path):
            return cwd_path
        # 2) resource_path（PyInstaller _MEIPASS）
        rp = resource_path(rel_path)
        if os.path.isfile(rp):
            return rp
        # 3) resource_path 仅文件名（兜底）
        base_rp = resource_path(os.path.basename(rel_path))
        if os.path.isfile(base_rp):
            return base_rp
        # 4) assets/ 目录兜底
        asset_rp = resource_path(f"assets/{os.path.basename(rel_path)}")
        if os.path.isfile(asset_rp):
            return asset_rp
        return None

    def _start_background_music(self):
        """开始循环播放背景音乐 TheFatRat - Unity。"""
        if not _SOUND_AVAILABLE:
            return
        resolved = self._resolve_music_path(self._UNITY_MUSIC)
        if resolved is None:
            return
        try:
            _mixer.music.load(resolved)
            _mixer.music.play(-1)  # 无限循环
            apply_sound_state()    # 应用静音状态
            self._music_tier = -1
            self._current_music_file = resolved
        except Exception:
            pass

    def _check_music_progression(self, new_tier: int):
        """根据合成 tier 切换背景音乐（v2.2.0.0）。"""
        if not _SOUND_AVAILABLE:
            return
        # 胜利音乐：tier 16
        n_tiers = len(self.mode_def.tiers)
        if new_tier >= n_tiers - 1:  # 最终球
            self._play_victory_music()
            return
        # 渐进音乐
        for threshold, path in self._BG_MUSIC:
            if new_tier >= threshold and self._music_tier < threshold:
                resolved = self._resolve_music_path(path)
                if resolved:
                    try:
                        _mixer.music.load(resolved)
                        _mixer.music.play(-1)
                        apply_sound_state()
                        self._music_tier = threshold
                        self._current_music_file = resolved
                    except Exception:
                        pass
                break

    def _play_victory_music(self):
        """播放胜利音乐 L'Internationale + war-shootout-shells SFX。"""
        if not _SOUND_AVAILABLE:
            return
        # 主音乐：L'Internationale（流式）
        resolved = self._resolve_music_path(self._VICTORY_MUSIC)
        if resolved:
            try:
                _mixer.music.load(resolved)
                _mixer.music.play()
                apply_sound_state()
            except Exception:
                pass
        # 同步 SFX：war-shootout-shells
        sfx_resolved = None
        sfx_path = self._VICTORY_SFX
        for p in [sfx_path,
                  resource_path(f"assets/{os.path.basename(sfx_path)}"),
                  resource_path(os.path.basename(sfx_path))]:
            if os.path.isfile(p):
                sfx_resolved = p
                break
        if sfx_resolved:
            _play_sound(sfx_path)  # 走 _play_sound 的缓存路径解析

    def stop_music(self):
        """停止并卸载音乐。"""
        try:
            _mixer.music.stop()
            _mixer.music.unload()
        except Exception:
            pass

    # ---- Internal ----

    def _random_tier(self) -> int:
        """随机掉落等级，支持动态掉落范围扩展 + 限频（v2.3.0.0）。

        debug_weights 非空时使用自定义权重。
        使用 ModeDefinition.initial_sequence 决定前几个固定掉落（v2.0.0.0）。
        """
        # 动态掉落：取 dynamic_max_drop 和 mode_def.max_drop 中较大者
        max_drop = get_max_drop()
        if self._dynamic_drop and DYNAMIC_DROP_ENABLED:
            max_drop = max(max_drop, self._dynamic_max_drop)

        if self.debug_weights is not None:
            weights = self.debug_weights
            total = sum(weights)
            if total <= 0:
                return random.randint(0, max_drop)
            return random.choices(range(max_drop + 1), weights=weights, k=1)[0]
        # 初始固定序列（各模式定义在 ModeDefinition 中）
        seq = self.mode_def.initial_sequence
        if self._lite_drop_seq < len(seq):
            tier = seq[self._lite_drop_seq]
            self._lite_drop_seq += 1
            return min(tier, max_drop)
        # 随机范围（支持加权掉落 + 动态限频）
        tiers_in_range = list(range(max_drop + 1))
        weights = [self.mode_def.tiers[i].drop_weight for i in tiers_in_range]

        # v2.3.0.0: 限频检查——跳过被限制的 tier
        if self._dynamic_drop and DYNAMIC_DROP_ENABLED:
            for t in list(self._rate_limit_interval.keys()):
                if t >= len(weights):
                    continue
                last = self._rate_limit_last.get(t, -9999)
                interval = self._rate_limit_interval[t]
                if self._drop_counter - last < interval:
                    weights[t] = 0.0  # 限频中，权重置零

        total_w = sum(weights)
        if total_w <= 0:
            # 所有权重被限频 → 只掉落最低几个
            safe = [i for i in tiers_in_range if i < min(self._rate_limit_interval.keys(), default=99)]
            if not safe:
                safe = [0]
            return random.choice(safe)

        tier = random.choices(tiers_in_range, weights=weights, k=1)[0]

        # 记录限频 tier 的本次掉落
        if self._dynamic_drop and DYNAMIC_DROP_ENABLED:
            if tier in self._rate_limit_interval:
                self._rate_limit_last[tier] = self._drop_counter

        self._drop_counter += 1
        return tier

    def _update_dynamic_drop(self, new_tier: int):
        """v2.3.0.0: 合成出 new_tier 后更新动态掉落范围 + 限频。

        规则：
        - 合成 N 级 → 解锁掉落 N-2 级（dynamic_max_drop）
        - N-3 级：每 DYNAMIC_DROP_RATE_LIMIT 个球限 1 次
        - N-2 级：每 DYNAMIC_DROP_RATE_LIMIT_TIGHT 个球限 1 次
        - 最高不掉落最后两级（仅合成可得）
        """
        if new_tier <= self._highest_synthesized:
            return  # 已处理过此等级
        self._highest_synthesized = new_tier

        unlock = new_tier - DYNAMIC_DROP_UNLOCK_OFFSET
        max_possible = len(TIERS) - 3  # 最后两级只能合成
        unlock = min(unlock, max_possible)
        if unlock > self._dynamic_max_drop:
            self._dynamic_max_drop = unlock

        # N-3 级限频
        limited_n3 = new_tier - 3
        if limited_n3 >= 0 and limited_n3 not in self._rate_limit_interval:
            self._rate_limit_interval[limited_n3] = DYNAMIC_DROP_RATE_LIMIT
            self._rate_limit_last[limited_n3] = -9999

        # N-2 级更严格限频
        limited_n2 = new_tier - 2
        if limited_n2 >= 0 and limited_n2 not in self._rate_limit_interval:
            self._rate_limit_interval[limited_n2] = DYNAMIC_DROP_RATE_LIMIT_TIGHT
            self._rate_limit_last[limited_n2] = -9999

    def _apply_mode_physics(self):
        """从 ModeDefinition 覆写 constants 模块全局变量（v2.0.0.0）。"""
        md = self.mode_def
        constants.GRAVITY = md.gravity
        constants.DAMPING = md.damping
        constants.FRICTION = md.friction_ball
        constants.FRICTION_WALL = md.friction_wall
        constants.DROP_DELAY = md.drop_delay
        constants.ATTRACT_FORCE = md.attract_force
        constants.ATTRACT_RANGE = md.attract_range
        constants.ROTATION_ENABLED = md.rotation_enabled
        constants.ANGULAR_DAMPING = md.angular_damping
        constants.WALL_ROTATIONAL_FRICTION = md.wall_rotational_friction
        constants.DROP_LINE_Y = md.drop_line_y
        constants.CONTAINER_TOP = md.container_top
        constants.CONTAINER_LEFT = md.container_left
        constants.CONTAINER_RIGHT = md.container_right
        constants.CONTAINER_BOTTOM = md.container_bottom
        constants.OVERFLOW_LINE_Y = md.overflow_line_y
        constants.OVERFLOW_TIME = md.overflow_time
        self._initial_vy = md.initial_vy
        # 同步 CONTAINER_WIDTH
        constants.CONTAINER_WIDTH = md.container_width

    def sync_mode_def_to_runtime(self):
        """v2.0.4.0: 将 mode_def 的所有参数实时同步到运行时。
        调试面板修改参数后调用此方法，使变更立即生效。
        """
        self._apply_mode_physics()
        self._update_bounds()
        # 同步 TIERS 数据（可能更改了 tier 参数）
        from data import set_active_tiers_from_mode
        set_active_tiers_from_mode(self.mode_def)
        # 重新计算所有现有球的半径（容器/半径变更时）
        scale = get_scale()
        for item in self.items:
            if item.alive:
                item.compute_radius(scale)
        # 重新加载消息（tier 信息可能变更）
        self.merge_messages.clear()
        self._load_messages()

    def _update_bounds(self):
        self.box_left = s(constants.CONTAINER_LEFT)
        self.box_right = s(constants.CONTAINER_RIGHT)
        self.box_top = s(constants.CONTAINER_TOP)
        self.box_bottom = s(constants.CONTAINER_BOTTOM)

    def _update_effects(self, dt):
        for i in range(len(self.merge_effects) - 1, -1, -1):
            fx, fy, tier, life = self.merge_effects[i]
            life -= dt
            if life <= 0.0:
                self.merge_effects.pop(i)
            else:
                self.merge_effects[i] = (fx, fy, tier, life)

        for i in range(len(self.text_popups) - 1, -1, -1):
            tx, ty, text, life = self.text_popups[i]
            life -= dt
            if life <= 0.0:
                self.text_popups.pop(i)
            else:
                # Float upward
                self.text_popups[i] = (tx, ty - s(40) * dt, text, life)

    def _build_grid(self):
        """Build spatial grid for current items. Cell size = max ball diameter."""
        max_r = max((it.radius for it in self.items if it.alive), default=50)
        cell_size = max_r * 2.5  # slightly larger than max diameter
        grid = SpatialGrid(self.box_left, self.box_top,
                           self.box_right, self.box_bottom, cell_size)
        for it in self.items:
            if it.alive:
                grid.insert(it)
        return grid

    def _apply_attraction(self, dt, grid):
        """Pull same-tier close items together (magnetic snap).
        最高级球不吸引 — 它们无法合成，吸引只会导致重叠。"""
        max_tier = len(TIERS) - 1
        for a, b in grid.yield_pairs():
            if a.tier == b.tier and a.tier < max_tier and a.can_merge() and b.can_merge():
                apply_attraction(a, b, dt)

    def _resolve_collisions(self, grid, dt):
        """Push apart overlapping items.
        同等级 + 非最高级 + 两者都可合成 → 跳过碰撞（留给吸引和合并处理）。
        同等级 + 冷却中 → 正常碰撞分离（防止冷却期内穿模重叠）。
        最高级同等级球 → 正常碰撞分离（它们无法合成，作为独立球）。
        v2.2.2.4: 移除冗余 wall_clamp — 主循环在碰撞后统一调。
        """
        max_tier = len(TIERS) - 1
        for _ in range(COLLISION_PASSES):
            any_collision = False
            for a, b in grid.yield_pairs():
                # 同等级 + 非最高级 + 都可合成 → 跳过碰撞，让它们重叠合并
                if a.tier == b.tier and a.tier < max_tier and a.can_merge() and b.can_merge():
                    continue
                if circles_overlap(a.x, a.y, a.radius, b.x, b.y, b.radius):
                    resolve_collision(a, b)
                    any_collision = True
            if not any_collision:
                break

    def _check_merges(self, grid):
        """Merge same-tier items. 迭代至无新合成（v2.2.2.4 即时合成 + 链式）。

        v2.2.2.4: 用 circles_near(tolerance=3px) 替代 circles_overlap。
        同等级球靠近到 3px 以内即触发合成，比严格重叠判断更流畅。
        """
        while True:
            merges = []
            dead = set()

            for a, b in grid.yield_pairs():
                if a.tier != b.tier or a.tier >= len(TIERS) - 1:
                    continue
                if not a.can_merge() or not b.can_merge():
                    continue
                if a in dead or b in dead:
                    continue
                if circles_near(a.x, a.y, a.radius, b.x, b.y, b.radius, MERGE_TOLERANCE):
                    idx_a = self.items.index(a)
                    idx_b = self.items.index(b)
                    merges.append((idx_a, idx_b))
                    dead.add(a)
                    dead.add(b)

            if not merges:
                break

            for i, j in merges:
                a = self.items[i]
                b = self.items[j]
                if not a.alive or not b.alive:
                    continue

                new_tier = a.tier + 1
                # 速度倒数加权归中（v2.2.2.2）：分轴独立。
                eps = 0.01  # 防除零
                wx_a = 1.0 / (abs(a.vx) + eps)
                wx_b = 1.0 / (abs(b.vx) + eps)
                wx_total = wx_a + wx_b
                new_x = (a.x * wx_a + b.x * wx_b) / wx_total

                wy_a = 1.0 / (abs(a.vy) + eps)
                wy_b = 1.0 / (abs(b.vy) + eps)
                wy_total = wy_a + wy_b
                new_y = (a.y * wy_a + b.y * wy_b) / wy_total

                merged = Item(new_x, new_y, new_tier, self._scale)
                # 动量守恒：新球速度 = 两球质心速度
                total_mass = a.mass + b.mass
                merged.vx = (a.vx * a.mass + b.vx * b.mass) / total_mass
                merged.vy = (a.vy * a.mass + b.vy * b.mass) / total_mass
                merged.merge_cooldown = 0.0   # v2.2.2.2: 允许即时链式
                merged.spawn_protect = 0.35
                self.items.append(merged)

                a.kill()
                b.kill()
                self.score += TIERS[new_tier]["points"]
                self.merge_effects.append((new_x, new_y, new_tier, 0.4))

                # v2.3.0.0: 动态掉落——合成高等级后解锁更大的掉落范围
                if self._dynamic_drop and DYNAMIC_DROP_ENABLED and new_tier >= 8:
                    self._update_dynamic_drop(new_tier)

                # 合成字幕
                merged_name = TIERS[new_tier]["name"]
                self.text_popups.append((new_x, new_y - a.radius, f"合成 {merged_name}!", 1.5))
                # 自定义消息（来自 Messages.txt）
                msg = self.merge_messages.get(new_tier, "")
                if msg:
                    self.text_popups.append((new_x, new_y - a.radius + s(22), msg, 2.0))

                # v2.2.0.0: 每级合成音效
                _play_tier_sound(new_tier)

                # v2.2.0.0: 音乐渐进
                self._check_music_progression(new_tier)

                # 合成终极球 → 全屏庆祝 + 胜利音乐
                max_tier = len(TIERS) - 1
                if new_tier == max_tier:
                    import time as _time
                    self.celebration_until = CELEBRATION_DURATION
                    self._play_victory_music()

            # 清理 + 重建 grid 让新球进入下一轮检测
            self.items = [it for it in self.items if it.alive]
            grid = self._build_grid()

    def _check_game_over(self, dt):
        """Game over if any item rests above overflow line too long.
        使用位置变化量判断稳定（不受重力加速影响）。"""
        overflow_y = s(constants.OVERFLOW_LINE_Y)
        for item in self.items:
            # 更新位置变化追踪
            dx = item.x - item._prev_x
            dy = item.y - item._prev_y
            item._prev_x = item.x
            item._prev_y = item.y
            moved = (dx * dx + dy * dy) ** 0.5

            if item.spawn_protect > 0.0:
                item.stable_time = 0.0
                continue
            if item.y - item.radius < overflow_y:
                if moved < s(3.0):  # 每帧移动 < 3px 视为稳定
                    item.stable_time += dt
                    if item.stable_time > OVERFLOW_TIME:
                        self.game_over = True
                        if not self.debug_tainted and self.score > 0:
                            self._record_score(self.score)
                        return
                else:
                    item.stable_time = 0.0
            else:
                item.stable_time = 0.0

    def _load_high_score(self):
        """加载历史最高分列表。文件每行一个分数，首行为最高。"""
        try:
            with open(HIGHSCORE_FILE, "r") as f:
                scores = []
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            scores.append(int(line))
                        except ValueError:
                            continue
                if scores:
                    self.score_history = scores[:MAX_HISTORY]
                    self.high_score = max(scores)
        except FileNotFoundError:
            self.score_history = []
            self.high_score = 0

    def _load_messages(self):
        """从 TIERS 的 'message' 字段加载合成消息（v2.0.0.0）。

        TIERS 已由 set_active_tiers_from_mode() 填充，message 字段
        来自 ModeDefinition.tiers[i].message。若为空，回退到 Messages.txt。
        """
        # 优先使用 ModeDefinition 中存储的消息
        for tier in range(len(TIERS)):
            msg = TIERS[tier].get("message", "")
            if msg:
                self.merge_messages[tier] = msg

        # 若消息已全部覆盖则不读 Messages.txt
        if len(self.merge_messages) >= len(TIERS):
            return

        # 回退：从 Messages.txt 加载（全模式索引 0-16 → 根据 n_tiers 映射）
        msg_path = resource_path("Messages.txt")
        n_tiers = self.mode_def.n_tiers
        tier_offset = 17 - n_tiers  # lite(11): offset=6, full(17): offset=0
        try:
            with open(msg_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    tier = int(line[:2])
                    parts = line.split(" ", 1)
                    if len(parts) == 2:
                        mapped_tier = tier - tier_offset
                        if mapped_tier >= 0 and mapped_tier not in self.merge_messages:
                            self.merge_messages[mapped_tier] = parts[1]
        except (FileNotFoundError, ValueError):
            pass

    def _record_score(self, score):
        """记录新分数到历史。最高分保持首行。"""
        self.score_history.append(score)
        self.score_history.sort(reverse=True)
        if len(self.score_history) > MAX_HISTORY:
            self.score_history = self.score_history[:MAX_HISTORY]
        self.high_score = self.score_history[0]
        self._save_high_score()

    def _save_high_score(self):
        """保存分数历史到文件，每行一个分数。"""
        try:
            with open(HIGHSCORE_FILE, "w") as f:
                for s in self.score_history:
                    f.write(f"{s}\n")
        except OSError:
            pass

    # ---- 自动恢复 ----

    def can_save(self) -> bool:
        """是否应保存：非演示、至少有一球在场。"""
        if self.game_over:
            return False
        if self.mode_id == "demo":
            return False  # AI 游戏不保存
        alive = [it for it in self.items if it.alive]
        if not alive:
            return False  # 无球在场不保存
        return True

    def save_state(self) -> dict:
        """序列化当前游戏状态。v2.1.0.0: mode_id 为存档文件名依据。"""
        return {
            "version": VERSION,
            "mode_id": self.mode_id,
            "score": self.score,
            "current_tier": self.current_tier,
            "drop_cooldown": self.drop_cooldown,
            "_lite_drop_seq": self._lite_drop_seq,
            "debug_allowed": self.debug_allowed,
            "debug_tainted": self.debug_tainted,
            "items": [
                {
                    "x": it.x, "y": it.y,
                    "vx": it.vx, "vy": it.vy,
                    "tier": it.tier,
                    "angle": it.angle,
                    "angular_velocity": it.angular_velocity,
                    "merge_cooldown": it.merge_cooldown,
                    "spawn_protect": it.spawn_protect,
                    "stable_time": it.stable_time,
                    "_sleep_time": it._sleep_time,
                }
                for it in self.items if it.alive
            ],
        }

    def save_to_file(self):
        """v2.1.0.0: 持久化到 savegame_{mode_id}.json。"""
        if not self.can_save():
            return
        try:
            state = self.save_state()
            if not state["items"]:
                return
            path = _save_path(self.mode_id)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    @staticmethod
    def check_save_exists() -> bool:
        """v2.0.x 兼容：检查旧版 savegame.json。"""
        return os.path.isfile(SAVEGAME_FILE)

    @staticmethod
    def list_saves() -> list[tuple[str, str]]:
        """v2.1.0.0: 列出所有存档。返回 [(mode_id, mode_name), ...]。
        也检查旧版 savegame.json（迁移用）。
        """
        from modes import mode_manager as _mm
        saves = []
        # 旧版兼容
        if os.path.isfile(SAVEGAME_FILE):
            try:
                with open(SAVEGAME_FILE, "r", encoding="utf-8") as f:
                    old = json.load(f)
                old_mode = old.get("mode_id") or old.get("mode", "lite")
                if old_mode == "qself":
                    old_mode = "lite"
                md = _mm.get(old_mode)
                name = md.name if md else old_mode
                saves.append((old_mode, f"{name} (旧版存档)"))
            except Exception:
                pass
        # 新版 per-mode 存档
        for mid in ["lite", "full", "debug", "full_debug", "demo"]:
            path = _save_path(mid)
            if os.path.isfile(path):
                md = _mm.get(mid)
                name = md.name if md else mid
                if (mid, name) not in [(s[0], s[1].replace(" (旧版存档)", "")) for s in saves]:
                    saves.append((mid, name))
        return saves

    @staticmethod
    def load_save_state(mode_id: str | None = None) -> dict | None:
        """v2.1.0.0: 读取存档。mode_id 指定时读取对应文件，否则自动查找。"""
        try:
            if mode_id:
                path = _save_path(mode_id)
                if not os.path.isfile(path):
                    return None
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            # 自动查找：先新版后旧版
            paths = [_save_path(mid) for mid in
                     ["lite", "full", "debug", "full_debug", "demo"]]
            paths.append(SAVEGAME_FILE)  # 旧版兼容
            for p in paths:
                if os.path.isfile(p):
                    with open(p, "r", encoding="utf-8") as f:
                        state = json.load(f)
                    if "mode_id" in state or "mode" in state:
                        return state
            return None
        except (json.JSONDecodeError, OSError):
            return None

    @staticmethod
    def remove_save(mode_id: str | None = None):
        """v2.1.0.0: 删除存档。mode_id=None 时删全部。"""
        try:
            if mode_id:
                path = _save_path(mode_id)
                if os.path.isfile(path):
                    os.remove(path)
            else:
                for mid in ["lite", "full", "debug", "full_debug", "demo"]:
                    path = _save_path(mid)
                    if os.path.isfile(path):
                        os.remove(path)
            # 总是清理旧版
            if os.path.isfile(SAVEGAME_FILE):
                os.remove(SAVEGAME_FILE)
        except OSError:
            pass

    def restore_from_save(self, state: dict):
        """从存档字典恢复游戏状态（v2.0.0.0：mode_id）。兼容旧存档（mode 字段）。"""
        from data import load_q_custom_tiers

        # 恢复模式（兼容旧字段名 mode / physics_model）
        saved_mode_id = state.get("mode_id") or state.get("mode", "lite")
        if saved_mode_id == "qself":
            load_q_custom_tiers()
        # 旧存档只有 "lite"/"full"/"qself"/"demo" → 映射到新 mode_id
        old_to_new = {"qself": "lite"}
        saved_mode_id = old_to_new.get(saved_mode_id, saved_mode_id)

        self.mode_def = mode_manager.get(saved_mode_id)
        if self.mode_def is None:
            self.mode_def = mode_manager.get("lite")
        self.mode_id = self.mode_def.id
        set_active_tiers_from_mode(self.mode_def)

        # 应用物理学模式
        self._apply_mode_physics()
        self._update_bounds()

        # 恢复物品
        self.items.clear()
        self._scale = get_scale()
        for it_data in state.get("items", []):
            item = Item(it_data["x"], it_data["y"], it_data["tier"], self._scale)
            item.vx = it_data.get("vx", 0.0)
            item.vy = it_data.get("vy", 0.0)
            item.angle = it_data.get("angle", 0.0)
            item.angular_velocity = it_data.get("angular_velocity", 0.0)
            item.merge_cooldown = it_data.get("merge_cooldown", 0.0)
            item.spawn_protect = it_data.get("spawn_protect", 0.0)
            item.stable_time = it_data.get("stable_time", 0.0)
            item._sleep_time = it_data.get("_sleep_time", 0.0)
            item._prev_x = item.x
            item._prev_y = item.y
            self.items.append(item)

        # 恢复分数与状态
        self.score = state.get("score", 0)
        self.current_tier = state.get("current_tier", None)
        self.drop_cooldown = state.get("drop_cooldown", 0.0)
        self._lite_drop_seq = state.get("_lite_drop_seq", 0)
        self.debug_allowed = state.get("debug_allowed", False)
        self.debug_tainted = state.get("debug_tainted", False)

        # 重新加载消息
        self.merge_messages.clear()
        self._load_messages()

        # 清理存档
        Game.remove_save()
