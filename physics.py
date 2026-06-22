"""Circle-circle collision, wall clamping, magnetic attraction + spatial grid."""

import math
import constants
from constants import s


class SpatialGrid:
    """Grid-based spatial partition for O(n) neighbor lookup.

    Divides container into cells of size >= max_ball_diameter.
    Any overlapping pair guaranteed to be in same or adjacent cells.
    """

    def __init__(self, left: float, top: float, right: float, bottom: float,
                 cell_size: float):
        self.left = left
        self.top = top
        self.cell_size = cell_size
        self.cols = max(1, int((right - left) / cell_size) + 1)
        self.rows = max(1, int((bottom - top) / cell_size) + 1)
        self.cells: dict[int, list] = {}

    def clear(self):
        self.cells.clear()

    def _key(self, col: int, row: int) -> int:
        return row * self.cols + col

    def insert(self, item):
        col = int((item.x - self.left) / self.cell_size)
        row = int((item.y - self.top) / self.cell_size)
        col = max(0, min(self.cols - 1, col))
        row = max(0, min(self.rows - 1, row))
        key = self._key(col, row)
        self.cells.setdefault(key, []).append(item)

    def yield_pairs(self):
        """Yield all (a, b) pairs that might interact. Each pair once."""
        for key, items in self.cells.items():
            col = key % self.cols
            row = key // self.cols
            # Within same cell
            for i in range(len(items)):
                for j in range(i + 1, len(items)):
                    yield (items[i], items[j])
            # Forward neighbors: right, down, down-right, down-left
            for dc, dr in [(1, 0), (0, 1), (1, 1), (-1, 1)]:
                nc, nr = col + dc, row + dr
                if 0 <= nc < self.cols and 0 <= nr < self.rows:
                    nkey = self._key(nc, nr)
                    if nkey in self.cells:
                        for a in items:
                            for b in self.cells[nkey]:
                                yield (a, b)


def circles_overlap(x1, y1, r1, x2, y2, r2):
    """True if two circles overlap."""
    dx = x1 - x2
    dy = y1 - y2
    min_dist = r1 + r2
    return dx * dx + dy * dy < min_dist * min_dist


def circles_near(x1, y1, r1, x2, y2, r2, tolerance: float = 3.0):
    """v2.2.2.4: True if two circles are within tolerance px of touching.

    用于即时合成：两球距离 ≤ 半径和+tolerance → 触发合成。
    比 circles_overlap 更宽松，球靠近（未完全重叠）即合成。
    """
    dx = x1 - x2
    dy = y1 - y2
    min_dist = r1 + r2 + tolerance
    return dx * dx + dy * dy < min_dist * min_dist


def resolve_collision(item1, item2):
    """Push apart two overlapping circles. Exchange velocity along normal.

    质量缩放: 轻球比重球位移更大，速度交换也按质量反比。
    DAMPING=0 (JFT2刚性) → 完全非弹性碰撞（沿法线方向粘合）。
    过度修正 20% 确保重叠完全分离，防止穿模。
    """
    dx = item1.x - item2.x
    dy = item1.y - item2.y
    dist_sq = dx * dx + dy * dy
    dist = math.sqrt(dist_sq) if dist_sq > 0.0 else 0.001

    min_dist = item1.radius + item2.radius
    overlap = min_dist - dist
    if overlap <= 0.0:
        return

    # 过度修正 20% — 确保球完全分离，不残留重叠
    overlap *= 1.2

    # Normal
    nx = dx / dist
    ny = dy / dist

    # Push apart — lighter item moves more (质量反比)
    m1 = item1.mass
    m2 = item2.mass
    total_m = m1 + m2
    ratio1 = m2 / total_m  # item1 位移比例（轻 → 大）
    ratio2 = m1 / total_m  # item2 位移比例
    item1.x += nx * overlap * ratio1
    item1.y += ny * overlap * ratio1
    item2.x -= nx * overlap * ratio2
    item2.y -= ny * overlap * ratio2

    # 唤醒两个球（被碰撞击中 → 退出睡眠）
    item1._sleep_time = 0.0
    item2._sleep_time = 0.0

    # Relative velocity along normal
    rel_vn = (item1.vx - item2.vx) * nx + (item1.vy - item2.vy) * ny
    if rel_vn > 0.0:
        return  # separating

    # Impulse with mass scaling and damping
    # j/m1 = -(1+e) * rel_vn * m2/(m1+m2)
    # DAMPING 即恢复系数 e
    impulse = rel_vn * (1.0 + constants.DAMPING)
    item1.vx -= impulse * ratio1 * nx
    item1.vy -= impulse * ratio1 * ny
    item2.vx += impulse * ratio2 * nx
    item2.vy += impulse * ratio2 * ny

    # ---- 球间接触摩擦（切向）+ 旋转扭矩（v2.0.0.0）----
    # 容器内真空，摩擦力仅在两球接触碰撞时沿切向生效。
    # 摩擦系数 = constants.FRICTION（JFT2=0.95 → 强摩擦，减少滑动）
    # 切向摩擦力同时产生扭矩，驱动球旋转。
    rel_vx = item1.vx - item2.vx
    rel_vy = item1.vy - item2.vy
    # 切向分量 = 相对速度 - 法向分量
    tvx = rel_vx - rel_vn * nx
    tvy = rel_vy - rel_vn * ny
    rel_vt = math.sqrt(tvx * tvx + tvy * tvy)
    if rel_vt > 0.001:
        tx = tvx / rel_vt
        ty = tvy / rel_vt
        # 库伦摩擦：冲量正比于法向冲量 × 摩擦系数
        friction_impulse = abs(impulse) * constants.FRICTION
        # 钳制：不反转切向相对速度
        friction_impulse = min(friction_impulse, rel_vt)
        item1.vx -= friction_impulse * tx * ratio1
        item1.vy -= friction_impulse * ty * ratio1
        item2.vx += friction_impulse * tx * ratio2
        item2.vy += friction_impulse * ty * ratio2

        # 旋转扭矩（v2.0.0.0）：摩擦力作用在接触点 → 角速度变化
        # cross = nx*ty - ny*tx = ±1 (切向与法向的叉积符号)
        # delta_omega = f_impulse * ratio * cross * 2 / r
        if constants.ROTATION_ENABLED:
            cross = nx * ty - ny * tx  # ±1
            r1 = item1.radius
            r2 = item2.radius
            if r1 > 0.001:
                item1.angular_velocity += friction_impulse * ratio1 * cross * 1.0 / r1
            if r2 > 0.001:
                item2.angular_velocity += friction_impulse * ratio2 * cross * 1.0 / r2


def apply_gravity(item, dt):
    """Add gravity to velocity."""
    item.vy += s(constants.GRAVITY) * dt


def apply_friction(item):
    """容器内真空 — 无空气阻力。
    球间摩擦在 resolve_collision() 的切向冲量中处理。
    """
    pass


def wall_clamp(item, box_left, box_right, box_top, box_bottom, dt):
    """Constrain item to container. 自然壁摩擦（v2.2.2.3 重写）。

    物理模型：
      - 位置修正：推出壁外，不归零速度
      - 法向速度：仅当球压入壁时反弹（弹性 0.15），分离中不干预
      - 正压力 = m·g（自重），均匀用于底壁和侧壁
      - 库伦摩擦力 = μ × 正压力，方向与切向速度相反
      - 旋转扭矩：触壁摩擦自然驱动球旋转
    """
    r = item.radius
    mu_w = constants.FRICTION_WALL
    g = s(constants.GRAVITY)
    m = item.mass
    elasticity_wall = 0.15  # 壁反弹系数（低弹性，不反弹过高）
    base_normal = m * g     # 统一正压力 = 自重（物理正确：壁面支持力 = 重力）
    touched = False

    mu_wr = constants.WALL_ROTATIONAL_FRICTION
    tc = constants.WALL_TORQUE_COUPLING

    def _friction_decel(v_t: float) -> float:
        """库伦摩擦减速。正压力统一用自重。摩擦不超过使球停下的量。"""
        if abs(v_t) < 0.1:
            return 0.0
        friction_force = mu_w * base_normal
        dv = (friction_force / m) * dt
        if dv >= abs(v_t):
            return 0.0
        return v_t - dv * (1.0 if v_t > 0 else -1.0)

    # 左壁
    if item.x - r < box_left:
        penetration = box_left - (item.x - r)
        item.x = box_left + r
        # 仅当压入壁时反弹法向速度，分离中不干预
        if item.vx < 0:
            item.vx = abs(item.vx) * elasticity_wall
        item.vy = _friction_decel(item.vy)
        if constants.ROTATION_ENABLED and r > 0.001:
            item.angular_velocity *= (1.0 - mu_wr * dt)
            if abs(item.vy) > 0.5:
                item.angular_velocity += item.vy * mu_w * tc / r * min(penetration / r, 1.0)
        touched = True

    # 右壁
    if item.x + r > box_right:
        penetration = (item.x + r) - box_right
        item.x = box_right - r
        if item.vx > 0:
            item.vx = -abs(item.vx) * elasticity_wall
        item.vy = _friction_decel(item.vy)
        if constants.ROTATION_ENABLED and r > 0.001:
            item.angular_velocity *= (1.0 - mu_wr * dt)
            if abs(item.vy) > 0.5:
                item.angular_velocity -= item.vy * mu_w * tc / r * min(penetration / r, 1.0)
        touched = True

    # 底部 — 最常接触面，正压力 = 自重
    if item.y + r > box_bottom:
        penetration = (item.y + r) - box_bottom
        item.y = box_bottom - r
        if item.vy > 0:
            item.vy = -abs(item.vy) * elasticity_wall
        item.vx = _friction_decel(item.vx)
        if constants.ROTATION_ENABLED and r > 0.001:
            item.angular_velocity *= (1.0 - mu_wr * dt)
            if abs(item.vx) > 0.5:
                item.angular_velocity -= item.vx * mu_w * tc / r
        touched = True

    # 顶部 — 仅上升中压入时
    if item.y - r < box_top and item.vy < -50:
        penetration = box_top - (item.y - r)
        item.y = box_top + r
        if item.vy < 0:
            item.vy = abs(item.vy) * elasticity_wall
        item.vx = _friction_decel(item.vx)
        if constants.ROTATION_ENABLED and r > 0.001:
            item.angular_velocity *= (1.0 - mu_wr * dt)
        touched = True

    if touched:
        item._sleep_time = 0.0  # 触壁唤醒，重新累计稳定时间


def apply_sleep(item, dt):
    """静止睡眠机制：球速度低于阈值累计静止时间。
    超过 SLEEP_SETTLE_TIME → 速度归零（深度休眠），
    直到被其他球碰撞唤醒（resolve_collision 清零 _sleep_time）。
    """
    speed = math.sqrt(item.vx * item.vx + item.vy * item.vy)
    threshold = s(constants.SLEEP_VELOCITY)
    if speed < threshold:
        item._sleep_time += dt
        if item._sleep_time > constants.SLEEP_SETTLE_TIME:
            # 深度休眠：完全归零
            item.vx = 0.0
            item.vy = 0.0
    else:
        item._sleep_time = 0.0


def apply_angular_damping(item, dt):
    """旋转角速度衰减（v2.0.1.0：dt无关指数衰减）。

    ω *= damping ** dt   →  每秒保留 damping 比例，与帧率无关。
    damping=0.85 → 1秒后保留85%，2秒后72%，5秒后44%。
    低于阈值直接归零，防止微旋转抖动。
    """
    if not constants.ROTATION_ENABLED:
        item.angular_velocity = 0.0
        return
    if abs(item.angular_velocity) < 0.001:
        item.angular_velocity = 0.0
        return
    item.angular_velocity *= constants.ANGULAR_DAMPING ** dt
    if abs(item.angular_velocity) < 0.005:
        item.angular_velocity = 0.0
    item.angle += item.angular_velocity * dt


def apply_attraction(a, b, dt):
    """Pull same-tier items together when close but not overlapping.
    Creates magnetic snap-to-merge feel."""
    dx = b.x - a.x
    dy = b.y - a.y
    dist_sq = dx * dx + dy * dy
    dist = math.sqrt(dist_sq) if dist_sq > 0.0 else 0.001

    gap = dist - a.radius - b.radius
    attract_range = s(constants.ATTRACT_RANGE)

    if gap <= 0.0 or gap >= attract_range:
        return

    # Force: strongest when closest
    t = 1.0 - gap / attract_range   # 0→1 as gap shrinks
    force = s(constants.ATTRACT_FORCE) * t * t * dt

    nx = dx / dist
    ny = dy / dist
    a.vx += nx * force
    a.vy += ny * force
    b.vx -= nx * force
    b.vy -= ny * force
