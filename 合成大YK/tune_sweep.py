"""Parameter sweep: find optimal radii + physics for target gameplay.

Target:
  Smart bot: wins (tier 16) in 20-25 min
  Dumb bot:  overflows in 10-15 min

Strategy: Phase 1 = quick radii scan (5 games/scale, capped 30min).
Phase 2 = fine-tune best scale with physics params.
"""

import time
import copy
from constants import set_scale, s
from data import TIERS
from autoplay import run_batch, print_stats, SmartBot, DumbBot

ORIG_RADII = [t["radius"] for t in TIERS]


def set_radii(factor):
    for i, t in enumerate(TIERS):
        t["radius"] = ORIG_RADII[i] * factor


def reset_radii():
    for i, t in enumerate(TIERS):
        t["radius"] = ORIG_RADII[i]


def patch_constants(**kwargs):
    import constants
    for k, v in kwargs.items():
        if v is not None and hasattr(constants, k.upper()):
            setattr(constants, k.upper(), v)


def score_params(smart: dict, dumb: dict) -> float:
    """Score parameter set. Higher = better match to targets.

    Ideal: smart wins in 20-25min, dumb overflows in 10-15min.
    """
    s = 0.0

    # Smart bot scoring
    sw = smart["win_rate"]
    st = smart["avg_time"]
    stier = smart["avg_max_tier"]

    # Win rate: want > 30% smart bot wins
    s += min(sw * 100, 40)

    # Game time for smart: want 900-1500s (15-25 min)
    if 900 <= st <= 1500:
        s += 30
    elif 600 <= st < 900:
        s += 15
    elif st > 1500:
        s += 5  # too long

    # Max tier for smart: want close to 16
    s += stier * 3

    # Dumb bot scoring
    dt = dumb["avg_time"]
    dgo = dumb["game_over_rate"]

    # Dumb game time: want 600-900s (10-15 min) and high overflow
    if 600 <= dt <= 900:
        s += 30
    elif 450 <= dt < 600:
        s += 20
    elif 300 <= dt < 450:
        s += 10

    # Dumb overflow rate: want high
    s += dgo * 20

    return s


def phase1_radii():
    """Quick scan of radii scales."""
    print("=" * 65)
    print("PHASE 1: Radii Scale Quick Scan")
    print("=" * 65)

    scales = [0.45, 0.50, 0.55, 0.60, 0.65, 0.70]
    results = []

    for scale in scales:
        set_radii(scale)
        max_r = ORIG_RADII[-1] * scale
        print(f"\n--- Scale {scale:.2f} (max radius={max_r:.0f}) ---")

        t0 = time.time()
        smart = run_batch(num_games=5, max_time=1800.0, fast_dt=1/40.0,
                          bot_mode="smart", verbose=False)
        dt1 = time.time() - t0

        print(f"  SMART: score={smart['avg_score']:.0f} "
              f"t={smart['avg_time']:.0f}s({smart['avg_time']/60:.1f}m) "
              f"tier={smart['avg_max_tier']:.1f} win={smart['win_rate']:.0%} "
              f"overflow={smart['game_over_rate']:.0%} "
              f"({dt1:.0f}s real)")

        t0 = time.time()
        dumb = run_batch(num_games=5, max_time=1800.0, fast_dt=1/40.0,
                         bot_mode="dumb", verbose=False)
        dt2 = time.time() - t0

        print(f"  DUMB:  score={dumb['avg_score']:.0f} "
              f"t={dumb['avg_time']:.0f}s({dumb['avg_time']/60:.1f}m) "
              f"tier={dumb['avg_max_tier']:.1f} "
              f"overflow={dumb['game_over_rate']:.0%} "
              f"({dt2:.0f}s real)")

        s = score_params(smart, dumb)
        print(f"  >>> SCORE: {s:.1f}")

        results.append({
            "scale": scale,
            "max_radius": max_r,
            "smart": smart,
            "dumb": dumb,
            "_score": s,
        })

    reset_radii()

    best = max(results, key=lambda r: r["_score"])
    print(f"\n>>> Best scale: {best['scale']:.2f} (score={best['_score']:.1f})")
    print_stats(best["smart"])
    print_stats(best["dumb"])

    return best


def phase2_finetune(best_scale):
    """Fine-tune drop delay and attraction with best radii."""
    print("\n" + "=" * 65)
    print("PHASE 2: Drop Delay + Attraction Fine-tune")
    print("=" * 65)

    set_radii(best_scale)
    results = []

    # Test drop delays (controls game pace) and attraction force
    drop_delays = [0.06, 0.08, 0.10, 0.12, 0.15]
    attract_forces = [800, 1000, 1200]

    for dd in drop_delays:
        for af in attract_forces:
            patch_constants(drop_delay=dd, attract_force=af)
            print(f"\n--- DD={dd} AF={af} ---")

            t0 = time.time()
            smart = run_batch(num_games=5, max_time=1800.0, fast_dt=1/40.0,
                              bot_mode="smart", verbose=False)
            dt = time.time() - t0

            print(f"  SMART: t={smart['avg_time']:.0f}s "
                  f"tier={smart['avg_max_tier']:.1f} win={smart['win_rate']:.0%} "
                  f"({dt:.0f}s)")

            t0 = time.time()
            dumb = run_batch(num_games=5, max_time=1800.0, fast_dt=1/40.0,
                             bot_mode="dumb", verbose=False)
            print(f"  DUMB:  t={dumb['avg_time']:.0f}s "
                  f"overflow={dumb['game_over_rate']:.0%}")

            s = score_params(smart, dumb)
            print(f"  SCORE: {s:.1f}")

            results.append({
                "drop_delay": dd,
                "attract_force": af,
                "smart": smart,
                "dumb": dumb,
                "_score": s,
            })

    reset_radii()

    best = max(results, key=lambda r: r["_score"])
    print(f"\n>>> Best: DD={best['drop_delay']} AF={best['attract_force']} "
          f"(score={best['_score']:.1f})")
    return best


def apply_best_params(radii_result, phys_result):
    """Print recommended settings."""
    scale = radii_result["scale"]
    dd = phys_result.get("drop_delay", 0.08)
    af = phys_result.get("attract_force", 1000)

    print("\n" + "=" * 65)
    print("RECOMMENDED SETTINGS")
    print("=" * 65)

    new_radii = [ORIG_RADII[i] * scale for i in range(len(TIERS))]
    print(f"  Radii scale: {scale:.3f}")
    print(f"  New radii:   {[round(r, 1) for r in new_radii]}")
    print(f"  DROP_DELAY:  {dd}")
    print(f"  ATTRACT_FORCE: {af}")
    print(f"  (keep: GRAVITY=1400 ATTRACT_RANGE=35 DAMPING=0.18 FRICTION=0.997)")
    print()

    # Print tier table for easy copy
    print("  Tier table for data.py:")
    for i, (t, r) in enumerate(zip(TIERS, new_radii)):
        name = t["name"]
        pts = t["points"]
        print(f'    {{"name": "{name}", "radius": {round(r, 1)}, '
              f'"color": {t["color"]}, "image": "{i}.png", "points": {pts}}},')


if __name__ == "__main__":
    set_scale(1.0)
    print("=== Big Alloy Merge: Parameter Tuning ===\n")

    # Phase 1: find best radii
    radii_result = phase1_radii()

    # Phase 2: fine-tune with best radii
    phys_result = phase2_finetune(radii_result["scale"])

    # Print final recommendations
    apply_best_params(radii_result, phys_result)
