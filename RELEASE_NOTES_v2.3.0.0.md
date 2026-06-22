# Big Alloy Merge v2.3.0.0 🌊 长风破浪版 (Wind and Waves)

> "Sometimes you ride the wind; sometimes you face it."

---

## 🕴️ New Elements

| Change | Tier | Name | Hint | Image |
|--------|------|------|------|-------|
| ✨ New | 0 | 西西 🕴️ | xiiiiii | New art |
| ✨ New | 14 | 春宇 ♾️ | 闭嘴吧啊 | New art |
| 🗑️ Removed | — | 雪豹 🏐 | — | Goodbye snow leopard |

- **西西** replaces 嘟嘟 as tier 0 — uses 嘟嘟's doo-doo sound effect
- **春宇** inserted before 锐哥 as tier 14 — uses 雪豹's snowball sound effect
- All shifted elements keep their original sound, image, and merge message

## ⚡ Dynamic Drop System (Full Mode)

Synthesizing higher tiers now **unlocks** drop tiers previously only available by merging:

| Synthesize | Unlocks Drop | Rate Limit |
|------------|-------------|------------|
| Tier 8 | Tier 6 | Every 5 balls |
| Tier 10 | Tiers 7–8 | Tiers 7–8: every 8 balls |
| Tier N | Tier N–2 | Configurable |

All parameters are customizable in `constants.py`:
```python
DYNAMIC_DROP_ENABLED = True
DYNAMIC_DROP_UNLOCK_OFFSET = 2
DYNAMIC_DROP_RATE_LIMIT = 5
DYNAMIC_DROP_RATE_LIMIT_TIGHT = 8
```

Faster games, fewer early-tier dead ends.

## 🚀 Performance & Physics

- **FPS**: 120 → **480** with **vsync** on all windows — buttery smooth, zero tearing
- **Rotation damping**: `ANGULAR_DAMPING` 0.98 → 0.92 — balls spin down naturally
- **Collision torque**: 2.0 → 1.0 — less chaotic bounces
- **Wall coupling**: 0.03 → 0.015 — walls don't over-rotate balls

## 📝 UI Updates

- **Drop info**: preview ball now shows `{tier} {name}` + hint message above the drop line
- **Splash screen**: updated to `newflash.jfif`
- **Window icon**: updated to `newicon.ico`

## 💿 NSIS Installer (New!)

`Big_Alloy_Merge_Setup.exe` — full Windows installer:

- Desktop + Start Menu shortcuts
- Includes **all resources** (images, sound effects, background music)
- Includes **Python source code**
- Optional: enter debug password (3919) during install to pre-authorize developer tools
- Clean uninstall with option to keep user data

## 🔑 AppData Migration

Writable files now live in `%APPDATA%\Trash Panda Q Opal\Big Alloy Merge\`:
- Saves, high scores, mode configs, audio settings
- **No admin rights needed** — works installed in Program Files
- User data survives upgrades and uninstalls

## 🐛 Bug Fixes

- Fixed `_dynamic_drop` AttributeError crash on startup (init order)
- Sound effect loading now searches multiple locations including AppData

## 📦 Download

| File | Description |
|------|-------------|
| `Big_Alloy_Merge.exe` | Standalone (portable) — just run it |
| `Big_Alloy_Merge_Setup.exe` | NSIS installer with resources + source |
| `Big_Alloy_Merge_Source.zip` | Python source code only |

---

**Full Changelog**: [CHANGELOG.md](CHANGELOG.md)  
**GitHub**: https://github.com/wanchengyang2010/big-alloy-merge

🤖 Published by Trash Panda Q Opal
