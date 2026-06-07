"""Auto-play bot + headless simulation for parameter tuning.

Two bot modes:
  Smart — pair same-tier items, strategic positions
  Dumb  — random drops, poor positioning (simulates bad play)

Headless mode runs without pygame for fast batch testing.
Target: smart play wins (tier 16) in ~20-25min; dumb play loses in ~10-15min.
"""

import random
import time
import constants
from constants import set_scale, get_scale, s
from data import TIERS
from game import Game


class SmartBot:
    """AI that strategically merges: precise drops, low-tier priority, space-aware."""

    def __init__(self, game: Game):
        self.game = game
        self.drop_index = 0

    def decide_drop_x(self) -> float:
        tier = self.game.current_tier
        same = [it for it in self.game.items if it.tier == tier and it.alive]

        if same:
            # Pick the LOWEST same-tier item (most stable, easiest merge)
            target = min(same, key=lambda it: it.y)
            # Drop BESIDE target with small gap (not overlapping)
            # Balls must be pulled together by physics to merge
            r_new = TIERS[tier]["radius"] * self.game._scale
            gap = target.radius * random.uniform(0.1, 0.3)
            direction = random.choice([-1, 1])
            x = target.x + direction * (target.radius + r_new + gap)
        else:
            # No same-tier target: find least crowded area
            x = self._find_open_spot()
            self.drop_index += 1

        r = TIERS[tier]["radius"] * self.game._scale
        x = max(self.game.box_left + r, min(self.game.box_right - r, x))
        return x

    def _find_open_spot(self) -> float:
        """Find least crowded horizontal zone in upper container area."""
        left = self.game.box_left
        right = self.game.box_right
        w = right - left
        overflow_y = s(constants.OVERFLOW_LINE_Y)

        # Divide into 5 zones, score each by: items in zone + penalty for high items
        zones = 5
        zone_w = w / zones
        scores = []
        for zi in range(zones):
            z_left = left + zi * zone_w
            z_right = z_left + zone_w
            penalty = 0
            for it in self.game.items:
                if not it.alive:
                    continue
                if z_left <= it.x <= z_right:
                    # Higher items = more penalty (closer to overflow = dangerous)
                    height_factor = max(0, 1.0 - (it.y - overflow_y) / s(500))
                    penalty += 1.0 + height_factor * 2.0
            scores.append((penalty, zi))

        # Pick best zone (lowest penalty), add jitter
        best_zone = min(scores)[1]
        x = left + zone_w * (best_zone + 0.5)
        x += random.uniform(-zone_w * 0.3, zone_w * 0.3)
        return x


class DumbBot:
    """Simulates worst play: always drops dead center, ignores everything."""

    def __init__(self, game: Game):
        self.game = game

    def decide_drop_x(self) -> float:
        tier = self.game.current_tier
        left = self.game.box_left
        right = self.game.box_right
        r = TIERS[tier]["radius"] * self.game._scale
        # Worst play: always center, slight jitter
        mid = (left + right) / 2
        x = mid + random.uniform(-s(8), s(8))
        x = max(left + r, min(right - r, x))
        return x


class DemoBot:
    """Demo bot for visual showcase. Builds on SmartBot strategy with visual hooks."""

    def __init__(self, game: Game):
        self.game = game
        self.drop_index = 0
        self.target_item = None   # ball being aimed at (for renderer highlight)
        self.aim_x = 0.0          # drop x coordinate (for renderer aim line)

    def decide_drop_x(self) -> float:
        tier = self.game.current_tier
        same = [it for it in self.game.items if it.tier == tier and it.alive]

        if same:
            # Pick the LOWEST same-tier item
            target = min(same, key=lambda it: it.y)
            self.target_item = target
            r_new = TIERS[tier]["radius"] * self.game._scale
            gap = target.radius * random.uniform(0.08, 0.22)
            # Prefer direction with more open space
            left_space = target.x - self.game.box_left
            right_space = self.game.box_right - target.x
            direction = -1 if left_space > right_space else 1
            x = target.x + direction * (target.radius + r_new + gap)
        else:
            self.target_item = None
            # Look for tier-1 partners too (they'll merge to current tier soon)
            near_tier = [it for it in self.game.items
                         if it.tier == tier - 1 and it.alive and tier > 0]
            if near_tier:
                # Drop near a tier-1 ball, hoping to merge same-tier soon
                target = min(near_tier, key=lambda it: it.y)
                self.target_item = target
                x = target.x + random.uniform(-s(30), s(30))
            else:
                x = self._find_open_spot()
            self.drop_index += 1

        self.aim_x = x
        r = TIERS[tier]["radius"] * self.game._scale
        x = max(self.game.box_left + r, min(self.game.box_right - r, x))
        self.aim_x = x
        return x

    def _find_open_spot(self) -> float:
        left = self.game.box_left
        right = self.game.box_right
        w = right - left
        overflow_y = s(constants.OVERFLOW_LINE_Y)
        # 7 zones for finer placement
        zones = 7
        zone_w = w / zones
        scores = []
        for zi in range(zones):
            z_left = left + zi * zone_w
            z_right = z_left + zone_w
            penalty = 0
            for it in self.game.items:
                if not it.alive:
                    continue
                if z_left <= it.x <= z_right:
                    height_factor = max(0, 1.0 - (it.y - overflow_y) / s(500))
                    penalty += 1.0 + height_factor * 2.0
            scores.append((penalty, zi))
        best_zone = min(scores)[1]
        x = left + zone_w * (best_zone + 0.5)
        x += random.uniform(-zone_w * 0.25, zone_w * 0.25)
        return x


def run_headless_game(
    seed: int = 0,
    max_time: float = 1800.0,
    fast_dt: float = 1 / 40.0,
    bot_mode: str = "smart",
    game_mode: str = "full",
) -> dict:
    """Run one headless game.

    Args:
        seed: random seed
        max_time: max in-game seconds (default 30 min)
        fast_dt: simulation timestep
        bot_mode: "smart" or "dumb"
        game_mode: "full" (17-tier) or "lite" (11-tier)
    """
    random.seed(seed)
    game = Game(mode=game_mode)
    bot = SmartBot(game) if bot_mode == "smart" else DumbBot(game)
    elapsed = 0.0
    drops = 0
    won = False  # reached tier 16

    while not game.game_over and elapsed < max_time and not won:
        if game.drop_cooldown <= 0.0:
            x = bot.decide_drop_x()
            game.drop(x)
            drops += 1
        game.update(fast_dt)
        elapsed += fast_dt

        # Check win condition: any alive tier 16
        if not won:
            for it in game.items:
                if it.alive and it.tier == len(TIERS) - 1:
                    won = True
                    break

    alive_items = [it for it in game.items if it.alive]
    tiers = [it.tier for it in alive_items]
    max_tier = max(tiers) if tiers else 0
    top_y = min((it.y - it.radius for it in alive_items), default=0)

    # game_over reason
    if won:
        end_reason = "win"
    elif game.game_over:
        end_reason = "overflow"
    elif elapsed >= max_time:
        end_reason = "timeout"
    else:
        end_reason = "unknown"

    return {
        "seed": seed,
        "score": game.score,
        "time": elapsed,
        "drops": drops,
        "item_count": len(alive_items),
        "max_tier": max_tier,
        "top_y": top_y,
        "game_over": game.game_over,
        "won": won,
        "end_reason": end_reason,
        "tiers": tiers,
    }


def run_batch(
    num_games: int = 50,
    max_time: float = 1800.0,
    fast_dt: float = 1 / 40.0,
    bot_mode: str = "smart",
    game_mode: str = "full",
    verbose: bool = True,
) -> dict:
    """Run multiple headless games. Returns aggregate stats."""
    scores = []
    times = []
    max_tiers = []
    item_counts = []
    game_overs = 0
    wins = 0
    tier_histogram = [0] * len(TIERS)
    top_ys = []
    end_reasons = {"win": 0, "overflow": 0, "timeout": 0, "unknown": 0}

    for i in range(num_games):
        result = run_headless_game(
            seed=i, max_time=max_time, fast_dt=fast_dt, bot_mode=bot_mode,
            game_mode=game_mode,
        )
        scores.append(result["score"])
        times.append(result["time"])
        max_tiers.append(result["max_tier"])
        item_counts.append(result["item_count"])
        top_ys.append(result["top_y"])
        if result["game_over"]:
            game_overs += 1
        if result["won"]:
            wins += 1
        end_reasons[result["end_reason"]] += 1
        for t in result["tiers"]:
            if 0 <= t < len(TIERS):
                tier_histogram[t] += 1

        if verbose and (i + 1) % max(1, num_games // 5) == 0:
            print(f"  [{i + 1}/{num_games}] "
                  f"score={result['score']} tier={result['max_tier']} "
                  f"t={result['time']:.0f}s {result['end_reason']}")

    n = num_games
    return {
        "num_games": n,
        "bot_mode": bot_mode,
        "avg_score": sum(scores) / n if n else 0,
        "avg_time": sum(times) / n if n else 0,
        "avg_max_tier": sum(max_tiers) / n if n else 0,
        "avg_item_count": sum(item_counts) / n if n else 0,
        "avg_top_y": sum(top_ys) / n if n else 0,
        "game_over_rate": game_overs / n if n else 0,
        "win_rate": wins / n if n else 0,
        "end_reasons": end_reasons,
        "tier_histogram": tier_histogram,
        "scores": scores,
        "times": times,
        "max_tiers": max_tiers,
    }


def print_stats(stats: dict):
    """Pretty-print batch statistics."""
    n = stats["num_games"]
    print(f"\n{'='*65}")
    print(f"  Bot: {stats.get('bot_mode', '?')} | Games: {n}")
    print(f"  Score: {stats['avg_score']:.0f} avg")
    print(f"  Time:  {stats['avg_time']:.0f}s = {stats['avg_time']/60:.1f}min avg")
    print(f"  Tier:  {stats['avg_max_tier']:.1f} avg max (of {len(TIERS)})")
    print(f"  Items: {stats['avg_item_count']:.0f} at end")
    print(f"  TopY:  {stats['avg_top_y']:.0f} (overflow={s(constants.OVERFLOW_LINE_Y):.0f})")
    print(f"  Wins:  {stats['win_rate']:.0%}  "
          f"Overflow: {stats['game_over_rate']:.0%}")
    er = stats["end_reasons"]
    print(f"  Reasons: win={er['win']} overflow={er['overflow']} "
          f"timeout={er['timeout']}")
    print(f"  Tier histogram:")
    for t in range(len(TIERS)):
        count = stats["tier_histogram"][t]
        bar = "#" * max(1, count // max(1, n // 2))
        name = TIERS[t]["name"].split()[0]
        print(f"    T{t:2d} {name:8s}: {count:4d}  {bar}")
    print(f"{'='*65}")


# ---- Quick test ----
if __name__ == "__main__":
    set_scale(1.0)
    t0 = time.time()
    print("Smart bot test (10 games, max 15min each)...")
    stats = run_batch(num_games=10, max_time=900.0, fast_dt=1/40.0, bot_mode="smart")
    print(f"\nReal time: {time.time() - t0:.1f}s")
    print_stats(stats)

    t0 = time.time()
    print("\nDumb bot test (10 games, max 15min each)...")
    stats2 = run_batch(num_games=10, max_time=900.0, fast_dt=1/40.0, bot_mode="dumb")
    print(f"\nReal time: {time.time() - t0:.1f}s")
    print_stats(stats2)
