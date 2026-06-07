"""Item — a single mergeable ball."""

from data import TIERS


class Item:
    """Ball with tier (size/look), position, velocity."""

    __slots__ = ("x", "y", "vx", "vy", "tier", "alive",
                 "merge_cooldown", "stable_time", "spawn_protect",
                 "_cached_radius", "_cache_scale",
                 "_prev_x", "_prev_y")

    def __init__(self, x, y, tier, scale=1.0):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.tier = tier
        self.alive = True
        self.merge_cooldown = 0.0
        self.stable_time = 0.0
        self.spawn_protect = 0.2
        self._cached_radius = TIERS[tier]["radius"] * scale
        self._cache_scale = scale
        self._prev_x = float(x)
        self._prev_y = float(y)

    def compute_radius(self, scale: float):
        """Recalc radius for current window scale."""
        self._cached_radius = TIERS[self.tier]["radius"] * scale
        self._cache_scale = scale

    @property
    def radius(self) -> float:
        return self._cached_radius

    @property
    def name(self) -> str:
        return TIERS[self.tier]["name"]

    @property
    def color(self):
        return TIERS[self.tier]["color"]

    @property
    def points(self) -> int:
        return TIERS[self.tier]["points"]

    def can_merge(self) -> bool:
        return self.alive and self.merge_cooldown <= 0.0

    def kill(self):
        self.alive = False
