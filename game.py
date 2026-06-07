"""Game state — items, physics, merge logic, scoring, game-over."""

import os
import json
import random

import constants
from constants import (
    DROP_LINE_Y, OVERFLOW_TIME,
    MERGE_COOLDOWN, COLLISION_PASSES,
    LITE_GRAVITY, LITE_DAMPING, LITE_FRICTION,
    LITE_DROP_DELAY, LITE_INITIAL_VY,
    LITE_ATTRACT_FORCE, LITE_ATTRACT_RANGE,
    LITE_DROP_LINE_Y, LITE_CONTAINER_TOP, LITE_CONTAINER_BOTTOM,
    LITE_CONTAINER_LEFT, LITE_CONTAINER_RIGHT, LITE_OVERFLOW_Y,
    LITE_OVERFLOW_TIME,
    s, get_scale, resource_path,
)
from data import TIERS, get_max_drop, random_drop_tier, set_active_mode
from item import Item
from physics import (
    circles_overlap, resolve_collision,
    apply_gravity, apply_friction,
    wall_clamp, apply_attraction,
    SpatialGrid,
)

# _MEIPASS is read-only (PyInstaller). Use CWD for writable files.
_HIGHSCORE_RESOURCE = resource_path("highscore.txt")
HIGHSCORE_FILE = os.path.join(os.getcwd(), "highscore.txt")
MAX_HISTORY = 20


class Game:
    def __init__(self, mode: str = "full"):
        set_active_mode(mode)  # switch TIERS before anything else
        self.mode = mode
        self._initial_vy = 0.0  # initial downward velocity on drop (set by mode)
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
        self.merge_effects: list[tuple[float, float, int, float]] = []
        self.text_popups: list[tuple[float, float, str, float]] = []
        self._scale = get_scale()

        self.debug_tier: int | None = None
        self.debug_weights: list[int] | None = None
        self.debug_tainted = False  # 本轮用过调试 → 不计分
        self.debug_allowed = False  # 仅密码验证通过后为 True
        self._lite_drop_seq = 0     # lite mode fixed drop sequence counter
        self.current_tier = self._random_tier()

        # Scaled container bounds (recomputed on resize)
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

        if self.debug_tier is not None:
            # 调试锁定：等级不变，冷却一样
            self.drop_cooldown = constants.DROP_DELAY
            self.current_tier = self.debug_tier  # always ready
        else:
            self.current_tier = None  # 消耗，冷却结束后再生成
            self.drop_cooldown = constants.DROP_DELAY

    def update(self, dt):
        """Advance game state by dt seconds."""
        if self.game_over:
            return

        dt = min(dt, 0.05)  # cap for stability
        self.drop_cooldown = max(0.0, self.drop_cooldown - dt)

        # 冷却结束 → 生成下一个球
        if self.current_tier is None and self.drop_cooldown <= 0.0:
            self.current_tier = self._random_tier()

        # Decay visual effects
        self._update_effects(dt)

        # 1. Tick cooldowns
        for item in self.items:
            if item.merge_cooldown > 0.0:
                item.merge_cooldown -= dt
            if item.spawn_protect > 0.0:
                item.spawn_protect -= dt

        # 2. Game over check (BEFORE gravity — uses settled velocities)
        self._check_game_over(dt)

        # 3. Gravity + friction + position
        for item in self.items:
            apply_gravity(item, dt)
            apply_friction(item)
            item.x += item.vx * dt
            item.y += item.vy * dt

        # Build spatial grid once per frame for efficient neighbor lookups
        grid = self._build_grid()

        # 4. Magnetic attraction (same-tier, close → pull together)
        self._apply_attraction(dt, grid)

        # 5. Wall clamp
        for item in self.items:
            wall_clamp(item, self.box_left, self.box_right,
                       self.box_top, self.box_bottom)

        # 6. Collision resolution
        self._resolve_collisions(grid)

        # 7. Merge check
        self._check_merges(grid)

    def restart(self):
        self.items.clear()
        self.merge_effects.clear()
        self.text_popups.clear()
        self.score = 0
        self.game_over = False
        self.drop_cooldown = 0.0
        self.debug_tainted = False
        self.current_tier = self._random_tier()

    def rescale(self, new_scale: float):
        """Update all radii and bounds after window resize."""
        self._scale = new_scale
        self._update_bounds()
        for item in self.items:
            item.compute_radius(new_scale)

    # ---- Internal ----

    def _random_tier(self) -> int:
        """随机掉落等级。debug_weights 非空时使用自定义权重，否则均等随机 0-5。
        Lite 模式：前6个固定序列 (0,0,1,2,2,3)，之后随机 0-4。
        """
        if self.debug_weights is not None:
            weights = self.debug_weights
            total = sum(weights)
            if total <= 0:
                return random.randint(0, get_max_drop())
            return random.choices(range(get_max_drop() + 1), weights=weights, k=1)[0]
        if self.mode == "lite":
            seq = [0, 0, 1, 2, 2, 3]
            if self._lite_drop_seq < len(seq):
                tier = seq[self._lite_drop_seq]
                self._lite_drop_seq += 1
                return tier
            return random.randint(0, get_max_drop())
        return random.randint(0, get_max_drop())

    def _apply_mode_physics(self):
        """Override physics constants for lite (11-element) mode."""
        if self.mode == "lite":
            constants.GRAVITY = LITE_GRAVITY
            constants.DAMPING = LITE_DAMPING
            constants.FRICTION = LITE_FRICTION
            constants.DROP_DELAY = LITE_DROP_DELAY
            constants.ATTRACT_FORCE = LITE_ATTRACT_FORCE
            constants.ATTRACT_RANGE = LITE_ATTRACT_RANGE
            constants.DROP_LINE_Y = LITE_DROP_LINE_Y
            constants.CONTAINER_TOP = LITE_CONTAINER_TOP
            constants.CONTAINER_LEFT = LITE_CONTAINER_LEFT
            constants.CONTAINER_RIGHT = LITE_CONTAINER_RIGHT
            constants.CONTAINER_BOTTOM = LITE_CONTAINER_BOTTOM
            constants.OVERFLOW_LINE_Y = LITE_OVERFLOW_Y
            constants.OVERFLOW_TIME = LITE_OVERFLOW_TIME
            self._initial_vy = LITE_INITIAL_VY
        else:
            self._initial_vy = 0.0
        # Note: full mode keeps defaults (set at module load or previous reset)

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
        """Pull same-tier close items together (magnetic snap)."""
        for a, b in grid.yield_pairs():
            if a.tier == b.tier and a.can_merge() and b.can_merge():
                apply_attraction(a, b, dt)

    def _resolve_collisions(self, grid):
        """Push apart overlapping DIFFERENT-tier items.
        Same-tier items skip collision — attraction pulls them in, merge handles them."""
        for _ in range(COLLISION_PASSES):
            any_collision = False
            for a, b in grid.yield_pairs():
                # Same tier → let them merge, don't push apart
                if a.tier == b.tier:
                    continue
                if circles_overlap(a.x, a.y, a.radius, b.x, b.y, b.radius):
                    resolve_collision(a, b)
                    any_collision = True
            if not any_collision:
                break

    def _check_merges(self, grid):
        """Merge overlapping same-tier items."""
        merges = []
        dead = set()

        for a, b in grid.yield_pairs():
            if a.tier != b.tier or a.tier >= len(TIERS) - 1:
                continue
            if not a.can_merge() or not b.can_merge():
                continue
            if a in dead or b in dead:
                continue
            if circles_overlap(a.x, a.y, a.radius, b.x, b.y, b.radius):
                # Find indices in self.items
                idx_a = self.items.index(a)
                idx_b = self.items.index(b)
                merges.append((idx_a, idx_b))
                dead.add(a)
                dead.add(b)

        for i, j in merges:
            a = self.items[i]
            b = self.items[j]
            if not a.alive or not b.alive:
                continue

            new_tier = a.tier + 1
            mid_x = (a.x + b.x) / 2.0
            mid_y = (a.y + b.y) / 2.0

            merged = Item(mid_x, mid_y, new_tier, self._scale)
            merged.merge_cooldown = MERGE_COOLDOWN
            merged.spawn_protect = 0.35
            self.items.append(merged)

            a.kill()
            b.kill()
            self.score += TIERS[new_tier]["points"]
            self.merge_effects.append((mid_x, mid_y, new_tier, 0.4))
            # 合成字幕
            merged_name = TIERS[new_tier]["name"]
            self.text_popups.append((mid_x, mid_y - a.radius, f"合成 {merged_name}!", 1.5))
            # 自定义消息（来自 Messages.txt）
            msg = self.merge_messages.get(new_tier, "")
            if msg:
                self.text_popups.append((mid_x, mid_y - a.radius + s(22), msg, 2.0))

        self.items = [it for it in self.items if it.alive]

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
        """Load merge messages from Messages.txt.
        Messages.txt uses full-mode tier indices (0-16). Lite mode
        uses tiers 6-16 mapped to 0-10, so we offset accordingly.
        """
        msg_path = resource_path("Messages.txt")
        tier_offset = 6 if self.mode == "lite" else 0
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
                        if mapped_tier >= 0:
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
