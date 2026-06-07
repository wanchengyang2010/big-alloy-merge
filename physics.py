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


def resolve_collision(item1, item2):
    """Push apart two overlapping circles. Exchange velocity along normal."""
    dx = item1.x - item2.x
    dy = item1.y - item2.y
    dist_sq = dx * dx + dy * dy
    dist = math.sqrt(dist_sq) if dist_sq > 0.0 else 0.001

    min_dist = item1.radius + item2.radius
    overlap = min_dist - dist
    if overlap <= 0.0:
        return

    # Normal
    nx = dx / dist
    ny = dy / dist

    # Push apart — smaller item moves more
    total_r = item1.radius + item2.radius
    ratio1 = item2.radius / total_r
    ratio2 = item1.radius / total_r
    item1.x += nx * overlap * ratio1
    item1.y += ny * overlap * ratio1
    item2.x -= nx * overlap * ratio2
    item2.y -= ny * overlap * ratio2

    # Relative velocity along normal
    rel_vn = (item1.vx - item2.vx) * nx + (item1.vy - item2.vy) * ny
    if rel_vn > 0.0:
        return  # separating

    # Impulse with damping
    impulse = rel_vn * (1.0 + constants.DAMPING) / 2.0
    item1.vx -= impulse * nx
    item1.vy -= impulse * ny
    item2.vx += impulse * nx
    item2.vy += impulse * ny


def apply_gravity(item, dt):
    """Add gravity to velocity."""
    item.vy += s(constants.GRAVITY) * dt


def apply_friction(item):
    """Air/ground friction damping."""
    item.vx *= constants.FRICTION
    item.vy *= constants.FRICTION


def wall_clamp(item, box_left, box_right, box_top, box_bottom):
    """Constrain item to container. Reflect with damping on wall hit."""
    r = item.radius

    if item.x - r < box_left:
        item.x = box_left + r
        item.vx = abs(item.vx) * constants.DAMPING
    if item.x + r > box_right:
        item.x = box_right - r
        item.vx = -abs(item.vx) * constants.DAMPING
    if item.y + r > box_bottom:
        item.y = box_bottom - r
        item.vy = -abs(item.vy) * constants.DAMPING
        item.vx *= 0.88  # ground friction
    # Mild ceiling — only when moving upward strongly
    if item.y - r < box_top and item.vy < -50:
        item.y = box_top + r
        item.vy = abs(item.vy) * constants.DAMPING


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
