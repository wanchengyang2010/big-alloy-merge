"""Rendering — background, container, items, UI, effects, game-over."""

import os
import time
import pygame
import constants as _c

from constants import (
    VERSION,
    DROP_LINE_Y,
    BG_COLOR, CONTAINER_BG, CONTAINER_BORDER, DANGER_LINE_COLOR,
    TEXT_COLOR, SCORE_COLOR, TEXT_CYAN, PREVIEW_ALPHA, OVERLAY_COLOR,
    BUTTON_BAR_H, BUTTONS,
    s, si, get_scale, resource_path,
)
from data import TIERS, get_max_drop
from modes import mode_manager

ASSETS_DIR = resource_path("assets/images")


# ── 程序化图标生成（v2.2.0.0）──────────────────────────────

def _generate_sound_icon(enabled: bool, size: int) -> pygame.Surface:
    """生成声音开/关图标。enabled=True → 青色喇叭+声波，False → 金色喇叭+X。"""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size
    m = c // 2
    s = c / 128.0  # scale factor from 128 reference

    if enabled:
        color = (104, 246, 248, 255)  # 青 #68f6f8
        # 喇叭箱体
        box_x = int(18 * s)
        box_y = int(44 * s)
        box_w = int(22 * s)
        box_h = int(40 * s)
        pygame.draw.rect(surf, color, (box_x, box_y, box_w, box_h), border_radius=int(4 * s))
        # 喇叭锥形 (三角形)
        cone_pts = [
            (int(40 * s), int(28 * s)),
            (int(40 * s), int(100 * s)),
            (int(74 * s), int(64 * s)),
        ]
        pygame.draw.polygon(surf, color, cone_pts)
        # 声波弧线
        arc_cx = int(74 * s)
        arc_cy = int(64 * s)
        for i in range(2):
            r = int((18 + i * 14) * s)
            pygame.draw.arc(surf, color,
                            (arc_cx - r, arc_cy - r, r * 2, r * 2),
                            4.2, 5.1, width=max(1, int(3 * s)))
    else:
        color = (242, 175, 76, 255)  # 金 #f2af4c
        # 喇叭箱体
        box_x = int(20 * s)
        box_y = int(42 * s)
        box_w = int(22 * s)
        box_h = int(42 * s)
        pygame.draw.rect(surf, color, (box_x, box_y, box_w, box_h), border_radius=int(4 * s))
        # 喇叭锥形
        cone_pts = [
            (int(42 * s), int(26 * s)),
            (int(42 * s), int(100 * s)),
            (int(78 * s), int(63 * s)),
        ]
        pygame.draw.polygon(surf, color, cone_pts)
        # X 标记
        x_color = (255, 80, 80, 220)
        x_margin = int(10 * s)
        x_lw = max(1, int(5 * s))
        pygame.draw.line(surf, x_color,
                         (x_margin, x_margin),
                         (c - x_margin, c - x_margin), x_lw)
        pygame.draw.line(surf, x_color,
                         (c - x_margin, x_margin),
                         (x_margin, c - x_margin), x_lw)
    return surf


def _generate_settings_icon(size: int) -> pygame.Surface:
    """生成设置齿轮图标。紫色 #cd8cf6。"""
    import math
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size
    m = c // 2
    s = c / 128.0
    color = (205, 140, 246, 255)  # 紫 #cd8cf6

    # 齿轮外圈
    outer_r = int(52 * s)
    inner_r = int(26 * s)
    teeth = 8
    tooth_h = int(12 * s)
    tooth_w = int(10 * s)

    # 画齿轮齿
    for i in range(teeth):
        angle = 2 * math.pi * i / teeth
        cx = int(m + (outer_r - tooth_h // 2) * math.cos(angle))
        cy = int(m + (outer_r - tooth_h // 2) * math.sin(angle))
        # 旋转的小矩形作为齿
        tooth_surf = pygame.Surface((tooth_w, tooth_h), pygame.SRCALPHA)
        tooth_surf.fill(color)
        rotated = pygame.transform.rotate(tooth_surf, -math.degrees(angle))
        surf.blit(rotated, (cx - rotated.get_width() // 2,
                            cy - rotated.get_height() // 2))

    # 齿轮主体圆
    pygame.draw.circle(surf, color, (m, m), int(outer_r), width=max(1, int(6 * s)))
    # 内圆（镂空）
    pygame.draw.circle(surf, (0, 0, 0, 0), (m, m), int(inner_r))
    pygame.draw.circle(surf, color, (m, m), int(inner_r), width=max(1, int(3 * s)))
    # 中心小圆
    center_r = int(8 * s)
    pygame.draw.circle(surf, color, (m, m), center_r)

    return surf


class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.images: dict[int, pygame.Surface | None] = {}
        self._font_path = None
        self._icon_cache: dict[str, pygame.Surface | None] = {}  # v2.2.0: 图标缓存
        self._init_font()
        # v2.2.0.1: 图片延迟加载——闪屏优先显示

    # ---- Font ----

    def _init_font(self):
        """Load CJK + Emoji fonts for mixed rendering."""
        # CJK candidates
        cjk_candidates = [
            resource_path("msyh.ttc"),
            resource_path("simhei.ttf"),
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
        ]
        self._font_path = None
        for path in cjk_candidates:
            if os.path.isfile(path):
                try:
                    pygame.font.Font(path, 20)
                    self._font_path = path
                    break
                except Exception:
                    continue

        # Emoji candidates
        emoji_candidates = [
            resource_path("emoji.ttf"),
            "C:/Windows/Fonts/seguiemj.ttf",
        ]
        self._emoji_font_path = None
        for path in emoji_candidates:
            if os.path.isfile(path):
                try:
                    pygame.font.Font(path, 20)
                    self._emoji_font_path = path
                    break
                except Exception:
                    continue

    @staticmethod
    def _has_emoji(text: str) -> bool:
        """Check if text contains emoji-range characters."""
        for ch in text:
            cp = ord(ch)
            if cp >= 0x1F000 or (0x2600 <= cp <= 0x27BF) or cp == 0xFE0F:
                return True
        return False

    def _font(self, size: int):
        """Return a font-like object with .render() that handles CJK+emoji.
        Transparent emoji support — zero changes needed at call sites.
        """
        cjk = pygame.font.Font(self._font_path, size) if self._font_path \
              else pygame.font.Font(None, size)

        emoji_path = self._emoji_font_path

        class _MixedFont:
            def render(_self, text, aa, color):
                if not emoji_path or not Renderer._has_emoji(text):
                    return cjk.render(text, aa, color)
                emoji = pygame.font.Font(emoji_path, size)
                # Split into CJK/emoji segments
                segments = []  # [(text, is_emoji)]
                buf = ""
                buf_emoji = None
                for ch in text:
                    ch_emoji = Renderer._has_emoji(ch)
                    if buf and ch_emoji != buf_emoji:
                        segments.append((buf, buf_emoji))
                        buf = ""
                    buf += ch
                    buf_emoji = ch_emoji
                if buf:
                    segments.append((buf, buf_emoji))
                surfs = []
                for seg_text, is_emoji in segments:
                    font = emoji if is_emoji else cjk
                    s = font.render(seg_text, aa, color)
                    if s.get_width() > 0:
                        surfs.append(s)
                if not surfs:
                    return cjk.render(text, aa, color)
                total_w = sum(s.get_width() for s in surfs)
                max_h = max(s.get_height() for s in surfs)
                result = pygame.Surface((total_w, max_h), pygame.SRCALPHA)
                x = 0
                for s in surfs:
                    result.blit(s, (x, 0))
                    x += s.get_width()
                return result

        return _MixedFont()

    # ---- Image loading ----

    def _load_images(self):
        self.images.clear()
        os.makedirs(ASSETS_DIR, exist_ok=True)
        cwd = os.getcwd()
        for tier in range(len(TIERS)):
            filename = TIERS[tier].get("image", "")
            img = None
            if filename:
                # 优先从 CWD 加载（Q自我模式用户自定义图片 / exe 同目录覆盖）
                cwd_path = os.path.join(cwd, filename)
                bundled_path = os.path.join(ASSETS_DIR, filename)
                for path in (cwd_path, bundled_path):
                    if os.path.isfile(path):
                        try:
                            raw = pygame.image.load(path).convert_alpha()
                            img = raw
                            break
                        except Exception:
                            continue
            self.images[tier] = img

    def reload_images(self):
        """Call after window resize if images need re-scaling."""
        self._load_images()

    def _get_icon(self, filename: str, size: int) -> pygame.Surface | None:
        """加载并缓存图标 PNG，缩放到指定尺寸。"""
        if filename in self._icon_cache:
            cached = self._icon_cache[filename]
            if cached is not None:
                return cached
            return None  # 之前尝试加载失败
        cwd = os.getcwd()
        paths = [
            os.path.join(cwd, filename),
            os.path.join(cwd, "pictures", filename),
            resource_path(f"assets/{filename}"),
            resource_path(filename),
        ]
        for p in paths:
            if os.path.isfile(p):
                try:
                    raw = pygame.image.load(p).convert_alpha()
                    scaled = pygame.transform.smoothscale(raw, (size, size))
                    self._icon_cache[filename] = scaled
                    return scaled
                except Exception:
                    continue
        self._icon_cache[filename] = None  # 标记已尝试
        return None

    def _get_or_generate_icon(self, key: str, size: int) -> pygame.Surface:
        """获取图标：先尝试 PNG，失败则程序化生成。"""
        cache_key = f"!gen_{key}"
        if cache_key in self._icon_cache:
            cached = self._icon_cache[cache_key]
            if cached is not None:
                return pygame.transform.smoothscale(cached, (size, size))
        # 尝试找 PNG
        png = self._get_icon(key, size)
        if png is not None:
            self._icon_cache[cache_key] = png
            return png
        # 程序化生成
        gen_size = 128
        surf = None
        if key == "声音开.png":
            surf = _generate_sound_icon(True, gen_size)
        elif key == "声音关.png":
            surf = _generate_sound_icon(False, gen_size)
        elif key == "设置面板.png":
            surf = _generate_settings_icon(gen_size)
        if surf is not None:
            self._icon_cache[cache_key] = surf
            return pygame.transform.smoothscale(surf, (size, size))
        # 最终兜底
        fallback = pygame.Surface((size, size), pygame.SRCALPHA)
        fallback.fill((80, 80, 100))
        return fallback

    # ---- Mode Selection ----

    def draw_mode_selection(self, has_save: bool = False):
        """Render the mode selection screen. has_save: show restore card."""
        self.screen.fill(BG_COLOR)

        w, h = self.screen.get_size()
        scale = get_scale()
        title_font = self._font(si(36))
        card_font = self._font(si(20))
        desc_font = self._font(si(14))

        # Title
        title = title_font.render("选择模式", True, SCORE_COLOR)
        self.screen.blit(title, ((w - title.get_width()) // 2, si(150)))

        # 如果有存档，标题上面显示提示
        save_offset = 0
        card_w = si(400)
        card_h = si(80)
        gap = si(20)

        if has_save:
            save_offset = 1
            # 恢复存档卡片（顶部，金色高亮）
            cy = si(300)
            cx = (w - card_w) // 2
            r_color = (255, 180, 50)
            r_card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            r_card.fill((*r_color, 60))
            pygame.draw.rect(r_card, (*r_color, 220), r_card.get_rect(),
                             width=si(3), border_radius=si(8))
            self.screen.blit(r_card, (cx, cy))
            # 图标
            save_icon = card_font.render("💾", True, (255, 255, 255))
            self.screen.blit(save_icon, (cx + si(16), cy + si(12)))
            # 名称
            r_name = card_font.render("恢复游戏", True, r_color)
            self.screen.blit(r_name, (cx + si(60), cy + si(10)))
            # 描述
            r_desc = desc_font.render("检测到未完成的游戏 · 按 [r] 或点击恢复", True, (*r_color, 200))
            self.screen.blit(r_desc, (cx + si(60), cy + si(44)))

        modes = [
            ("a", "2222 模式", "17 元素完整版 · 待开发", (100, 100, 100)),
            ("b", "大西瓜模式", "11 元素经典版 · 纯碰撞合成", (60, 200, 100)),
            ("c", "调试模式", "需要密码才能进入", (200, 140, 60)),
            ("d", "演示模式", "AI 自动游玩 · 观看通关过程", (180, 120, 220)),
            ("q", "Q自我模式", "自定义球图/名称/合成提示词 · 持久化", (100, 200, 220)),
        ]

        start_y = si(300) + save_offset * (card_h + gap)

        for i, (key, name, desc, color) in enumerate(modes):
            cy = start_y + i * (card_h + gap)
            cx = (w - card_w) // 2
            locked = (i == 0)  # 全模式锁定

            # Card background
            card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            alpha = 20 if locked else 40
            border_alpha = 100 if locked else 180
            card.fill((*color, alpha))
            pygame.draw.rect(card, (*color, border_alpha), card.get_rect(), width=si(2), border_radius=si(8))
            self.screen.blit(card, (cx, cy))

            # Key label (left side)
            key_color = (120, 120, 120) if locked else (255, 255, 255)
            key_text = card_font.render(f"[{key}]", True, key_color)
            self.screen.blit(key_text, (cx + si(16), cy + si(12)))

            # Mode name
            name_color = (140, 140, 140) if locked else TEXT_COLOR
            name_text = card_font.render(name, True, name_color)
            self.screen.blit(name_text, (cx + si(60), cy + si(10)))

            # Description
            desc_color = (100, 100, 100, 150) if locked else (*color, 200)
            desc_text = desc_font.render(desc, True, desc_color)
            self.screen.blit(desc_text, (cx + si(60), cy + si(44)))

            # Lock indicator
            if locked:
                lock_font = self._font(si(18))
                lock_text = lock_font.render("\U0001f512", True, (120, 120, 120))
                self.screen.blit(lock_text, (cx + card_w - si(40), cy + si(20)))

        # Footer
        if has_save:
            footer_text = "点击卡片选择模式 · 键盘 b / c / d / q · 按 r 恢复存档"
        else:
            footer_text = "点击卡片选择模式 · 键盘 b / c / d / q 快速选择"
        footer = desc_font.render(footer_text, True, TEXT_CYAN)
        self.screen.blit(footer, ((w - footer.get_width()) // 2, h - si(60)))

        pygame.display.flip()

    # ── v2.0.0.0 新模式选择 ──

    def draw_mode_selection_v2(self, modes, has_save: bool = False,
                                drag_idx: int | None = None, drag_y: float = 0.0,
                                saved_ids: set | None = None):
        """v2.1.0.0 模式选择界面：动态卡片 + 存档指示 + 拖拽排序 + 齿轮按钮。

        modes: list[ModeDefinition] 已按 order 排序。
        saved_ids: set of mode_id that have save files.
        """
        if saved_ids is None:
            saved_ids = set()
        self.screen.fill(BG_COLOR)
        w, h = self.screen.get_size()

        title_font = self._font(si(36))
        card_font = self._font(si(19))
        desc_font = self._font(si(13))
        num_font = self._font(si(22))
        small_font = self._font(si(12))

        # ── 齿轮按钮（右上角）──
        gear_x = w - si(50)
        gear_y = si(20)
        gear_sz = si(36)
        gear_btn = pygame.Surface((gear_sz, gear_sz), pygame.SRCALPHA)
        gear_btn.fill((60, 60, 80, 120))
        pygame.draw.rect(gear_btn, (140, 140, 170, 200),
                         gear_btn.get_rect(), width=si(2), border_radius=si(6))
        self.screen.blit(gear_btn, (gear_x - gear_sz // 2, gear_y - gear_sz // 2))
        # v2.0.3.0: 使用 settings.png 图标，回退到 ⚙ 文字
        icon_sz = int(gear_sz * 0.7)
        settings_icon = self._get_icon("settings.png", icon_sz)
        if settings_icon:
            self.screen.blit(settings_icon,
                             (gear_x - icon_sz // 2, gear_y - icon_sz // 2))
        else:
            gear_text = title_font.render("⚙", True, TEXT_COLOR)
            self.screen.blit(gear_text, (gear_x - gear_text.get_width() // 2,
                                          gear_y - gear_text.get_height() // 2))
        # 标签
        gear_label = small_font.render("设置", True, (180, 180, 200))
        self.screen.blit(gear_label, (gear_x - gear_label.get_width() // 2,
                                       gear_y + gear_sz // 2 + si(2)))

        # ── v2.2.0.0: 声音按钮（齿轮左侧）──
        import game as game_module
        sound_x = gear_x - si(50)
        sound_y = gear_y
        sound_sz = gear_sz
        sound_btn = pygame.Surface((sound_sz, sound_sz), pygame.SRCALPHA)
        sound_btn.fill((60, 60, 80, 120))
        pygame.draw.rect(sound_btn, (140, 140, 170, 200),
                         sound_btn.get_rect(), width=si(2), border_radius=si(6))
        self.screen.blit(sound_btn, (sound_x - sound_sz // 2, sound_y - sound_sz // 2))
        sound_icon_sz = int(sound_sz * 0.7)
        sound_icon_key = "声音开.png" if game_module._sound_enabled else "声音关.png"
        sound_icon = self._get_or_generate_icon(sound_icon_key, sound_icon_sz)
        if sound_icon:
            self.screen.blit(sound_icon,
                             (sound_x - sound_icon_sz // 2, sound_y - sound_icon_sz // 2))
        sound_label = small_font.render("声音", True, (180, 180, 200))
        self.screen.blit(sound_label, (sound_x - sound_label.get_width() // 2,
                                        sound_y + sound_sz // 2 + si(2)))

        # ── 标题 ──
        title = title_font.render("选择模式", True, SCORE_COLOR)
        self.screen.blit(title, ((w - title.get_width()) // 2, si(150)))

        card_w = si(420)
        card_h = si(76)
        gap = si(14)
        cx = (w - card_w) // 2

        save_offset = 1 if has_save else 0
        start_y = si(280) + save_offset * (card_h + gap)

        # ── 恢复存档卡片 ──
        if has_save:
            ry = si(280)
            r_color = (255, 180, 50)
            r_card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            r_card.fill((*r_color, 60))
            pygame.draw.rect(r_card, (*r_color, 220), r_card.get_rect(),
                             width=si(3), border_radius=si(8))
            self.screen.blit(r_card, (cx, ry))
            save_icon = card_font.render("💾", True, (255, 255, 255))
            self.screen.blit(save_icon, (cx + si(16), ry + si(12)))
            r_name = card_font.render("恢复游戏", True, r_color)
            self.screen.blit(r_name, (cx + si(60), ry + si(10)))
            r_desc = desc_font.render("检测到未完成的游戏 · 按 [r] 或点击恢复",
                                      True, (*r_color, 200))
            self.screen.blit(r_desc, (cx + si(60), ry + si(44)))

        # ── 模式卡片 ──
        for i, md in enumerate(modes):
            cy = start_y + i * (card_h + gap)

            # 拖拽中的卡片：绘制在拖拽位置
            draw_cy = drag_y if (drag_idx is not None and i == drag_idx) else cy

            # 跳过被拖拽卡片原位置（视觉上已移走）
            if drag_idx is not None and i == drag_idx:
                # 在原位画一个虚线占位
                placeholder = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                placeholder.fill((80, 80, 100, 30))
                pygame.draw.rect(placeholder, (120, 120, 150, 80),
                                 placeholder.get_rect(), width=si(1),
                                 border_radius=si(8))
                self.screen.blit(placeholder, (cx, cy))
                # 然后在拖拽位置画卡片
                cy = int(drag_y)

            locked = md.locked
            is_demo = (md.id == "demo")
            is_active = (md.id == mode_manager.active_id)

            # 卡片背景色
            if locked:
                card_color = (100, 100, 100)
                card_alpha = 20
                border_alpha = 100
            elif is_demo:
                card_color = (180, 120, 220)
                card_alpha = 35
                border_alpha = 160
            elif md.builtin:
                card_color = (60, 200, 100) if md.id == "lite" else (100, 200, 220)
                card_alpha = 30
                border_alpha = 180
            else:
                card_color = (180, 160, 100)
                card_alpha = 35
                border_alpha = 180

            if is_active:
                border_alpha = 255
                card_alpha = 55

            card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            card.fill((*card_color, card_alpha))
            bw = si(3) if is_active else si(2)
            pygame.draw.rect(card, (*card_color, border_alpha),
                             card.get_rect(), width=bw, border_radius=si(8))
            self.screen.blit(card, (cx, cy))

            # 编号
            num_color = (120, 120, 120) if locked else (255, 255, 255)
            num_text = num_font.render(str(i), True, num_color)
            self.screen.blit(num_text, (cx + si(16), cy + (card_h - num_text.get_height()) // 2))

            # 模式名称 + 锁定图标 + 存档指示
            name_color = (140, 140, 140) if locked else TEXT_COLOR
            name_str = f"🔒 {md.name}" if locked else md.name
            if md.id in saved_ids:
                name_str = f"💾 {name_str}"
            name_text = card_font.render(name_str, True, name_color)
            self.screen.blit(name_text, (cx + si(52), cy + si(8)))

            # 描述行
            n_tiers = md.n_tiers
            phys = f"g={md.gravity:.0f} μ={md.friction_ball:.2f}" if not locked else "待开发"
            desc_str = f"{n_tiers}元素 · {phys}"
            desc_text = desc_font.render(desc_str, True, (*card_color, 180))
            self.screen.blit(desc_text, (cx + si(52), cy + si(44)))

            # 拖拽手柄提示（右侧 ≡ 符号）
            if not locked:
                handle = desc_font.render("≡", True, (160, 160, 180))
                self.screen.blit(handle, (cx + card_w - si(36), cy + (card_h - handle.get_height()) // 2))

        # ── 新建模式按钮 ──
        new_y = start_y + len(modes) * (card_h + gap) + gap
        new_w = si(180)
        new_h = si(36)
        new_x = (w - new_w) // 2
        new_btn = pygame.Surface((new_w, new_h), pygame.SRCALPHA)
        new_btn.fill((60, 60, 80, 100))
        pygame.draw.rect(new_btn, (120, 120, 150, 200),
                         new_btn.get_rect(), width=si(1), border_radius=si(6))
        self.screen.blit(new_btn, (new_x, new_y))
        new_text = desc_font.render("+ 新建模式", True, (200, 200, 220))
        self.screen.blit(new_text, (new_x + (new_w - new_text.get_width()) // 2,
                                     new_y + (new_h - new_text.get_height()) // 2))

        # ── 底部提示 ──
        footer_text = "点击卡片选择模式 · 拖拽 ≡ 排序 · 数字键快捷选择 · 右上⚙设置"
        footer = small_font.render(footer_text, True, TEXT_CYAN)
        self.screen.blit(footer, ((w - footer.get_width()) // 2, h - si(50)))

        pygame.display.flip()

    # ── 密码对话框 ──

    def draw_password_dialog(self, password: str, error: bool = False):
        """Render password input dialog over the mode selection screen."""
        w, h = self.screen.get_size()
        dialog_w = si(300)
        dialog_h = si(140)
        dx = (w - dialog_w) // 2
        dy = (h - dialog_h) // 2

        font = self._font(si(18))
        small = self._font(si(13))

        # Overlay
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        # Dialog box
        dlg = pygame.Surface((dialog_w, dialog_h), pygame.SRCALPHA)
        dlg.fill((40, 42, 60, 240))
        pygame.draw.rect(dlg, (80, 85, 120, 255), dlg.get_rect(), width=si(2), border_radius=si(6))
        self.screen.blit(dlg, (dx, dy))

        # Title
        title = font.render("请输入调试密码", True, TEXT_COLOR)
        self.screen.blit(title, (dx + si(16), dy + si(14)))

        # Password field (show * for each char)
        masked = "*" * len(password) if password else "___"
        pwd_text = font.render(masked, True, (255, 215, 90))
        self.screen.blit(pwd_text, (dx + si(20), dy + si(50)))

        # Error message
        if error:
            err = small.render("密码错误！请重试", True, (255, 80, 80))
            self.screen.blit(err, (dx + si(20), dy + si(78)))

        # Hint
        hint = small.render("输入密码后按回车确认 · ESC 返回", True, (140, 140, 160))
        self.screen.blit(hint, (dx + si(20), dy + si(100)))

        pygame.display.flip()

    # ---- 启动闪屏 ----

    # flash.jfif background (loaded once, cached) — v2.2.0.1
    _splash_bg = None

    def _load_splash_bg(self):
        """加载闪屏背景图（newflash.jfif）。"""
        w, h = self.screen.get_size()
        paths = [
            os.path.join(os.getcwd(), "pictures", "newflash.jfif"),
            resource_path("pictures/newflash.jfif"),
            resource_path("assets/yk.png"),
        ]
        for p in paths:
            if os.path.isfile(p):
                try:
                    raw = pygame.image.load(p)
                    try:
                        raw = raw.convert()
                    except Exception:
                        pass  # dummy display fallback
                    iw, ih = raw.get_size()
                    scale = max(w / iw, h / ih)  # 覆盖全屏
                    nw, nh = int(iw * scale), int(ih * scale)
                    Renderer._splash_bg = pygame.transform.smoothscale(raw, (nw, nh))
                    return
                except Exception:
                    continue
        Renderer._splash_bg = False

    def draw_splash(self, state: str = "ready"):
        """v2.2.0.1: flash.jfif 全屏闪屏 + 加载提示。
        state: "loading" = 加载中  |  "ready" = 点击开始
        """
        w, h = self.screen.get_size()

        # 加载背景图（缓存）
        if Renderer._splash_bg is None:
            self._load_splash_bg()

        # 深色填充
        self.screen.fill((8, 8, 18))

        # 背景图居中填满
        if Renderer._splash_bg and Renderer._splash_bg is not False:
            bg = Renderer._splash_bg
            bw, bh = bg.get_size()
            self.screen.blit(bg, ((w - bw) // 2, (h - bh) // 2))

        # 半透明遮罩（底部 45%）
        overlay = pygame.Surface((w, int(h * 0.45)), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, int(h * 0.55)))

        # ---- 文字叠加 ----
        cx = w // 2
        title_y = int(h * 0.60)

        # 应用名
        title_font = self._font(si(40))
        title = title_font.render("合成大YK", True, SCORE_COLOR)
        self.screen.blit(title, (cx - title.get_width() // 2, title_y))

        # 英文副标题
        sub_font = self._font(si(15))
        sub = sub_font.render("Big Alloy Merge", True, TEXT_COLOR)
        self.screen.blit(sub, (cx - sub.get_width() // 2, title_y + si(46)))

        # 版本号
        ver_font = self._font(si(18))
        ver = ver_font.render(VERSION, True, TEXT_CYAN)
        self.screen.blit(ver, (cx - ver.get_width() // 2, title_y + si(72)))

        # 发布者
        pub_font = self._font(si(16))
        pub = pub_font.render("Trash Panda Q Opal", True, (170, 170, 200))
        self.screen.blit(pub, (cx - pub.get_width() // 2, title_y + si(98)))

        # 底部提示文字
        hint_font = self._font(si(16))
        if state == "loading":
            hint_text = "加载中…"
            hint_color = SCORE_COLOR
        else:
            hint_text = "点击任意位置开始游戏"
            hint_color = TEXT_COLOR
        hint = hint_font.render(hint_text, True, hint_color)
        self.screen.blit(hint, (cx - hint.get_width() // 2, int(h * 0.88)))

        pygame.display.flip()

    # ---- 合成终极球庆祝特效 ----

    _theme_bg = None  # theme.png 缓存

    def _draw_celebration(self, game):
        """合成终极球全屏庆祝：theme.png + 滚动文字。不阻塞游戏。"""
        w, h = self.screen.get_size()
        remaining = game.celebration_until
        alpha = int(min(255, remaining / 10.0 * 255))  # 最后渐隐

        # 加载 theme.png（缓存）
        if Renderer._theme_bg is None:
            theme_path = resource_path("assets/theme.png")
            # 也检查 CWD（用户可能放在 exe 同目录）
            cwd_path = os.path.join(os.getcwd(), "theme.png")
            for path in (cwd_path, theme_path):
                if os.path.isfile(path):
                    try:
                        raw = pygame.image.load(path).convert_alpha()
                        scale = min(w / raw.get_width(), h / raw.get_height())
                        nw, nh = int(raw.get_width() * scale), int(raw.get_height() * scale)
                        Renderer._theme_bg = pygame.transform.smoothscale(raw, (nw, nh))
                        break
                    except Exception:
                        continue
            if Renderer._theme_bg is None:
                Renderer._theme_bg = False

        if Renderer._theme_bg and Renderer._theme_bg is not False:
            bg = Renderer._theme_bg
            bg_copy = bg.copy()
            bg_copy.set_alpha(min(220, alpha))
            bw, bh = bg_copy.get_size()
            self.screen.blit(bg_copy, ((w - bw) // 2, (h - bh) // 2))

        # 半透明深色遮罩
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, min(140, 255 - alpha)))
        self.screen.blit(overlay, (0, 0))

        # 滚动文字（往返移动）
        t = time.time()
        cx = w // 2

        # 第一行：你合成了大YK!（金色大号，水平摆动）
        big_font = self._font(si(48))
        line1 = big_font.render("你合成了大YK!", True, (255, 215, 50))
        # 左右摆动幅度
        sway1 = int(si(60) * (t * 1.3 % 2.0 - 1.0))  # ±60px 慢速摆动
        l1y = int(h * 0.30)
        self.screen.blit(line1, (cx - line1.get_width() // 2 + sway1, l1y))

        # 第二行：打倒YK反动统治!!!（红色大号，反向摆动）
        mid_font = self._font(si(36))
        line2 = mid_font.render("打倒YK反动统治!!!", True, (255, 60, 40))
        sway2 = int(si(60) * -(t * 1.3 % 2.0 - 1.0))  # 反方向摆动
        l2y = int(h * 0.42)
        self.screen.blit(line2, (cx - line2.get_width() // 2 + sway2, l2y))

        # 倒计时提示
        small_font = self._font(si(14))
        countdown = small_font.render(f"庆祝中… {remaining:.0f}s · 游戏可继续操作", True, (200, 200, 200))
        self.screen.blit(countdown, (cx - countdown.get_width() // 2, int(h * 0.88)))

    # ---- Frame ----

    def draw(self, game, debug_mode=False, demo_bot=None, drag_x=None,
             debug_panel=None):
        self.screen.fill(BG_COLOR)
        self._draw_background(game)
        self._draw_button_bar(game)
        self._draw_container()
        self._draw_danger_line()
        self._draw_items(game)
        self._draw_demo_overlay(game, demo_bot)
        self._draw_merge_effects(game)
        self._draw_text_popups(game)
        if demo_bot is None:
            self._draw_preview(game, drag_x)
        else:
            self._draw_demo_preview(game, demo_bot)
        self._draw_ui(game)
        if debug_mode:
            # v2.0.4.0: 完整调试模式使用独立面板 + 始终显示等级选择器
            if getattr(game, '_full_debug', False):
                bar_bottom = self._draw_tier_selector(game)
                self._draw_weight_editor(game, bar_bottom)
            else:
                self._draw_debug(game)
        if game.game_over:
            self._draw_game_over(game)

        # v2.2.0.0: 声音开关按钮（始终显示，替换旧音乐按钮）
        self._draw_sound_button(game)

        # 合成终极球庆祝特效
        if game.celebration_until > 0.0:
            self._draw_celebration(game)

        # v2.0.4.0: 完整调试面板（在 flip 之前渲染，确保显示）
        if debug_panel is not None and debug_panel.visible:
            debug_panel.render(self.screen, self)

        pygame.display.flip()

    # ---- Sections ----

    # 背景图缓存（按文件名）
    _bg_cache: dict[str, pygame.Surface | None] = {}

    def _draw_background(self, game):
        """v2.0.0.0: 渲染模式背景图 + 上方暗色渐变遮罩。"""
        bg_file = getattr(game.mode_def, 'background_image', '')
        if not bg_file:
            return
        w, h = self.screen.get_size()

        # 加载缓存
        cache_key = bg_file
        if cache_key not in Renderer._bg_cache:
            cwd = os.getcwd()
            paths = [
                os.path.join(cwd, bg_file),
                resource_path(f"assets/{bg_file}"),
                resource_path(bg_file),
            ]
            loaded = None
            for p in paths:
                if os.path.isfile(p):
                    try:
                        raw = pygame.image.load(p).convert()
                        scale = max(w / raw.get_width(), h / raw.get_height())
                        nw, nh = int(raw.get_width() * scale), int(raw.get_height() * scale)
                        loaded = pygame.transform.smoothscale(raw, (nw, nh))
                        break
                    except Exception:
                        continue
            Renderer._bg_cache[cache_key] = loaded

        bg = Renderer._bg_cache.get(cache_key)
        if bg is None:
            return

        bw, bh = bg.get_size()
        # 居中绘制
        self.screen.blit(bg, ((w - bw) // 2, (h - bh) // 2))

        # 上方暗色渐变遮罩（确保 UI 可读）
        overlay_alpha = getattr(game.mode_def, 'background_overlay_alpha', 140)
        if overlay_alpha > 0:
            overlay_h = int(h * 0.45)
            if overlay_h > 0:
                overlay = pygame.Surface((w, overlay_h), pygame.SRCALPHA)
                for i in range(overlay_h):
                    alpha = int(overlay_alpha * (1.0 - i / overlay_h))
                    if alpha > 0:
                        pygame.draw.line(overlay, (0, 0, 0, alpha), (0, i), (w, i))
                self.screen.blit(overlay, (0, 0))

    def _draw_container(self):
        left = si(_c.CONTAINER_LEFT)
        top = si(_c.CONTAINER_TOP)
        w = si(_c.CONTAINER_RIGHT) - left
        h = si(_c.CONTAINER_BOTTOM) - top
        rect = pygame.Rect(left, top, w, h)
        pygame.draw.rect(self.screen, CONTAINER_BG, rect, border_radius=si(14))
        pygame.draw.rect(self.screen, CONTAINER_BORDER, rect, width=max(2, si(2)), border_radius=si(14))

    def _draw_danger_line(self):
        y = si(_c.OVERFLOW_LINE_Y)
        left = si(_c.CONTAINER_LEFT) + 5
        right = si(_c.CONTAINER_RIGHT) - 5
        dash = max(4, si(8))
        gap = max(3, si(6))
        x = left
        toggle = True
        while x < right:
            end = min(x + dash, right)
            if toggle:
                pygame.draw.line(self.screen, DANGER_LINE_COLOR,
                                 (int(x), y), (int(end), y),
                                 max(1, si(1)))
            x += dash if toggle else gap
            toggle = not toggle

    def _draw_items(self, game):
        for item in game.items:
            if not item.alive:
                continue
            img = self.images.get(item.tier)
            if img is not None:
                self._draw_image_item(item, img)
            else:
                self._draw_text_item(item)

    def _draw_image_item(self, item, img: pygame.Surface):
        d = int(item.radius * 2)
        if d < 2:
            return
        cx, cy = int(item.x), int(item.y)
        r = int(item.radius)

        # Scale image to current item diameter
        try:
            scaled = pygame.transform.smoothscale(img, (d, d))
        except Exception:
            scaled = pygame.transform.scale(img, (d, d))

        # 旋转（v2.0.0.0）：球可绕中心旋转
        if item.angular_velocity != 0.0 or item.angle != 0.0:
            import math as _math
            angle_deg = -_math.degrees(item.angle)  # 负号：pygame 顺时针
            scaled = pygame.transform.rotate(scaled, angle_deg)

        # 旋转后尺寸可能变大，取新尺寸居中绘制圆形遮罩
        new_d = scaled.get_width()
        mask = pygame.Surface((new_d, new_d), pygame.SRCALPHA)
        mask.fill((0, 0, 0, 0))
        pygame.draw.circle(mask, (255, 255, 255, 255), (new_d // 2, new_d // 2), r)

        result = scaled.copy()
        result.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # Border
        bw = max(1, si(2))
        pygame.draw.circle(self.screen, CONTAINER_BORDER, (cx, cy), r, width=bw)

        self.screen.blit(result, (cx - new_d // 2, cy - new_d // 2))

        # Tier number badge (bottom-center of ball)
        num_fs = max(8, int(r * 0.45))
        num_font = self._font(num_fs)
        num_text = num_font.render(str(item.tier), True, (255, 255, 255))
        num_surf = pygame.Surface((num_text.get_width() + si(8),
                                    num_text.get_height() + si(4)), pygame.SRCALPHA)
        num_surf.fill((0, 0, 0, 160))
        num_surf.blit(num_text, (si(4), si(2)))
        self.screen.blit(num_surf, (cx - num_surf.get_width() // 2,
                                     cy + r - num_surf.get_height() - si(2)))

    def _draw_text_item(self, item):
        cx, cy = int(item.x), int(item.y)
        r = int(item.radius)
        if r < 2:
            return

        color = item.color

        # Filled circle
        pygame.draw.circle(self.screen, color, (cx, cy), r)

        # Highlight
        hl = tuple(min(255, c + 55) for c in color)
        pygame.draw.circle(self.screen, hl, (cx - r // 4, cy - r // 3),
                           max(2, r // 2))

        # Border
        border = tuple(max(0, c - 45) for c in color)
        bw = max(1, si(2))
        pygame.draw.circle(self.screen, border, (cx, cy), r, width=bw)

        # Name with tier number
        name = f"{item.tier} {item.name}"
        fs = max(8, int(r * 0.5))
        font = self._font(fs)
        text = font.render(name, True, TEXT_COLOR)
        self.screen.blit(text, (cx - text.get_width() // 2,
                                cy - text.get_height() // 2))

    def _draw_merge_effects(self, game):
        for fx, fy, tier, life in game.merge_effects:
            alpha = int(255 * max(0.0, life / 0.4))
            if alpha <= 0:
                continue
            base_r = TIERS[tier]["radius"] * get_scale()
            grow = s(15) * (1.0 - life / 0.4)
            r = int(base_r + grow)
            color = (*TIERS[tier]["color"], alpha)
            size = r * 2 + 6
            ring = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(ring, color, (size // 2, size // 2), r, width=max(1, si(3)))
            self.screen.blit(ring, (int(fx - size // 2), int(fy - size // 2)))

    def _draw_text_popups(self, game):
        """Floating merge text: '合成 XX!' — rises and fades."""
        for tx, ty, text, life in game.text_popups:
            alpha = int(255 * min(1.0, life / 0.6))
            if alpha <= 0:
                continue
            fs = max(10, si(20))
            font = self._font(fs)
            # Text with shadow
            shadow = font.render(text, True, (0, 0, 0))
            s = shadow.copy()
            s.set_alpha(alpha)
            self.screen.blit(s, (int(tx - s.get_width() // 2 + 2),
                                 int(ty - s.get_height() // 2 + 2)))
            fg = font.render(text, True, (255, 255, 100))
            fg.set_alpha(alpha)
            self.screen.blit(fg, (int(tx - fg.get_width() // 2),
                                  int(ty - fg.get_height() // 2)))

    def _draw_preview(self, game, drag_x=None):
        """Show item at drop line. drag_x overrides mouse pos (touch drag).
        仅在球准备好时显示（冷却结束后生成）。"""
        if game.game_over or game.current_tier is None:
            return

        mx = drag_x if drag_x is not None else pygame.mouse.get_pos()[0]
        tier = game.current_tier
        r = int(TIERS[tier]["radius"] * get_scale())
        if r < 2:
            return

        x = max(si(_c.CONTAINER_LEFT) + r, min(si(_c.CONTAINER_RIGHT) - r, mx))
        y = si(DROP_LINE_Y)

        # Draw full-opacity preview (not translucent — must match what drops)
        img = self.images.get(tier)
        if img is not None:
            d = r * 2
            mask = pygame.Surface((d, d), pygame.SRCALPHA)
            mask.fill((0, 0, 0, 0))
            pygame.draw.circle(mask, (255, 255, 255, 255), (r, r), r)
            try:
                scaled = pygame.transform.smoothscale(img, (d, d))
            except Exception:
                scaled = pygame.transform.scale(img, (d, d))
            result = scaled.copy()
            result.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            self.screen.blit(result, (x - r, y - r))
            bw = max(1, si(2))
            pygame.draw.circle(self.screen, CONTAINER_BORDER, (x, y), r, width=bw)
        else:
            pygame.draw.circle(self.screen, TIERS[tier]["color"], (x, y), r)
            border = tuple(max(0, c - 45) for c in TIERS[tier]["color"])
            bw = max(1, si(2))
            pygame.draw.circle(self.screen, border, (x, y), r, width=bw)
            # Name on preview
            name = f"{tier} {TIERS[tier]['name']}"
            fs = max(8, int(r * 0.5))
            font = self._font(fs)
            text = font.render(name, True, TEXT_COLOR)
            self.screen.blit(text, (x - text.get_width() // 2,
                                    y - text.get_height() // 2))

        # Number badge on image preview too
        if img is not None:
            num_fs = max(8, int(r * 0.45))
            num_font = self._font(num_fs)
            num_text = num_font.render(str(tier), True, (255, 255, 255))
            num_bg = pygame.Surface((num_text.get_width() + si(8),
                                      num_text.get_height() + si(4)), pygame.SRCALPHA)
            num_bg.fill((0, 0, 0, 160))
            num_bg.blit(num_text, (si(4), si(2)))
            self.screen.blit(num_bg, (x - num_bg.get_width() // 2,
                                       y + r - num_bg.get_height() - si(2)))

        # v2.3.0.0: 掉落球信息显示在预览球上方
        name_text = f"{tier} {TIERS[tier]['name']}"
        name_fs = max(8, si(14))
        name_font = self._font(name_fs)
        name_surf = name_font.render(name_text, True, SCORE_COLOR)
        name_y = y - r - name_surf.get_height() - si(6)
        # 黑色阴影提高可读性
        shadow = name_font.render(name_text, True, (0, 0, 0))
        self.screen.blit(shadow, (x - name_surf.get_width() // 2 + si(1), name_y + si(1)))
        self.screen.blit(name_surf, (x - name_surf.get_width() // 2, name_y))
        # 合成提示消息
        msg = TIERS[tier].get("message", "")
        if not msg:
            # 从 Messages.txt 查找
            msg = game.merge_messages.get(tier, "")
        if msg:
            msg_fs = max(6, si(11))
            msg_font = self._font(msg_fs)
            msg_surf = msg_font.render(msg, True, TEXT_CYAN)
            msg_shadow = msg_font.render(msg, True, (0, 0, 0))
            msg_y = name_y - msg_surf.get_height() - si(3)
            self.screen.blit(msg_shadow, (x - msg_surf.get_width() // 2 + si(1), msg_y + si(1)))
            self.screen.blit(msg_surf, (x - msg_surf.get_width() // 2, msg_y))

    def _draw_demo_overlay(self, game, demo_bot):
        """Demo mode: highlight target ball and show aim crosshair."""
        if demo_bot is None or game.game_over:
            return
        if demo_bot.target_item is not None and demo_bot.target_item.alive:
            t = demo_bot.target_item
            cx, cy = int(t.x), int(t.y)
            r = int(t.radius)
            # Pulsing glow ring
            pulse = 0.5 + 0.5 * abs((time.time() * 3) % 2.0 - 1.0)
            glow_r = r + si(6) + int(si(4) * pulse)
            alpha = int(100 + 80 * pulse)
            glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 215, 90, alpha), (glow_r, glow_r), glow_r, width=si(3))
            self.screen.blit(glow, (cx - glow_r, cy - glow_r))

    def _draw_demo_preview(self, game, demo_bot):
        """Demo mode preview ball at bot's aim position."""
        if game.game_over or demo_bot is None or game.current_tier is None:
            return

        tier = game.current_tier
        r = int(TIERS[tier]["radius"] * get_scale())
        if r < 2:
            return

        x = max(si(_c.CONTAINER_LEFT) + r,
                min(si(_c.CONTAINER_RIGHT) - r, int(demo_bot.aim_x)))
        y = si(DROP_LINE_Y)

        # Aim line from preview to drop zone
        line_surf = pygame.Surface((self.screen.get_width(), self.screen.get_height()),
                                    pygame.SRCALPHA)
        # Dashed vertical aim line
        dash_len = si(6)
        gap_len = si(4)
        cur_y = y + r
        end_y = si(_c.CONTAINER_TOP) + si(20)
        while cur_y < end_y:
            seg_end = min(cur_y + dash_len, end_y)
            pygame.draw.line(line_surf, (255, 215, 90, 80), (x, cur_y), (x, seg_end), si(2))
            cur_y = seg_end + gap_len
        self.screen.blit(line_surf, (0, 0))

        # Draw preview ball (same as normal preview)
        img = self.images.get(tier)
        d = r * 2
        if img is not None:
            mask = pygame.Surface((d, d), pygame.SRCALPHA)
            mask.fill((0, 0, 0, 0))
            pygame.draw.circle(mask, (255, 255, 255, 255), (r, r), r)
            try:
                scaled = pygame.transform.smoothscale(img, (d, d))
            except Exception:
                scaled = pygame.transform.scale(img, (d, d))
            result = scaled.copy()
            result.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            self.screen.blit(result, (x - r, y - r))
            bw = max(1, si(2))
            pygame.draw.circle(self.screen, SCORE_COLOR, (x, y), r, width=bw)
        else:
            pygame.draw.circle(self.screen, TIERS[tier]["color"], (x, y), r)
            bw = max(1, si(2))
            pygame.draw.circle(self.screen, SCORE_COLOR, (x, y), r, width=bw)

        # Crosshair at drop point
        cross_sz = si(6)
        pygame.draw.line(self.screen, (255, 215, 90, 200), (x - cross_sz, y), (x + cross_sz, y), si(2))
        pygame.draw.line(self.screen, (255, 215, 90, 200), (x, y - cross_sz), (x, y + cross_sz), si(2))

        # "DEMO" label top-right
        demo_font = self._font(si(16))
        demo_label = demo_font.render("🔴 演示模式", True, (255, 180, 60))
        self.screen.blit(demo_label, (self.screen.get_width() - demo_label.get_width() - si(8), si(8)))

    def _draw_sound_button(self, game):
        """v2.2.0.0: 右上角声音开关按钮（始终显示）。"""
        import game as game_module
        w = self.screen.get_width()
        btn_sz = si(36)
        bx = w - btn_sz - si(10)
        by = si(30)
        # 圆形背景
        bg = pygame.Surface((btn_sz, btn_sz), pygame.SRCALPHA)
        bg_color = (60, 80, 100, 200) if game_module._sound_enabled else (80, 60, 60, 200)
        pygame.draw.circle(bg, bg_color, (btn_sz // 2, btn_sz // 2), btn_sz // 2)
        pygame.draw.circle(bg, (140, 140, 170, 220), (btn_sz // 2, btn_sz // 2),
                           btn_sz // 2, width=max(1, si(2)))
        self.screen.blit(bg, (bx, by))
        # 声音开/关图标
        icon_sz = int(btn_sz * 0.65)
        icon_key = "声音开.png" if game_module._sound_enabled else "声音关.png"
        icon = self._get_or_generate_icon(icon_key, icon_sz)
        if icon:
            self.screen.blit(icon,
                             (bx + (btn_sz - icon_sz) // 2, by + (btn_sz - icon_sz) // 2))

    def _draw_ui(self, game):
        """Score, current item, version."""
        # ---- Top-left: Score ----
        sf = self._font(max(14, si(26)))
        st = sf.render(f"分数：{game.score}", True, SCORE_COLOR)
        self.screen.blit(st, (si(8), si(8)))

        # ---- Top-left: Best ----
        bf = self._font(max(12, si(18)))
        bt = bf.render(f"最高：{game.high_score}", True, TEXT_COLOR)
        self.screen.blit(bt, (si(8), si(36)))

        # ---- Top-right: Current ball (single-ball: only one at a time) ----
        ctx = si(_c.CONTAINER_RIGHT) - si(10)
        cy = si(8)
        cnf = self._font(max(10, si(13)))
        cnl = cnf.render("当前：", True, SCORE_COLOR)
        self.screen.blit(cnl, (ctx - cnl.get_width(), cy))

        if game.current_tier is not None:
            self._draw_ui_ball(game.current_tier, ctx - cnl.get_width() // 2,
                                cy + si(18), max_radius=si(22))
            cnnf = self._font(max(9, si(11)))
            cnn = cnnf.render(f"{game.current_tier} {TIERS[game.current_tier]['name']}",
                              True, TEXT_COLOR)
            self.screen.blit(cnn, (ctx - cnn.get_width() // 2, cy + si(42)))
        else:
            # 冷却中——球正在下落
            cnnf = self._font(max(9, si(11)))
            cnn = cnnf.render("冷却中…", True, (160, 160, 180))
            self.screen.blit(cnn, (ctx - cnn.get_width() // 2, cy + si(30)))

        # ---- Bottom: Version + Update ----
        vf = self._font(max(8, si(12)))
        vt = vf.render(VERSION, True, (*TEXT_CYAN, 120))
        self.screen.blit(vt, (si(_c.CONTAINER_LEFT) + si(4),
                              si(_c.CONTAINER_BOTTOM) + si(6)))

        # 更新提示
        if getattr(game, 'update_available', False) and game.update_info:
            remote_ver, _download = game.update_info
            uf = self._font(max(8, si(13)))
            ut = uf.render(f"新版本 {remote_ver} 可用！", True, (255, 200, 60))
            self.screen.blit(ut, (si(_c.CONTAINER_LEFT) + si(4),
                                  si(_c.CONTAINER_BOTTOM) + si(22)))

    def _draw_ui_ball(self, tier, cx, cy, max_radius=22):
        """Draw a small preview ball for the UI corner."""
        nr_base = TIERS[tier]["radius"] * get_scale()
        if nr_base <= 0:
            return
        local_scale = min(1.0, max_radius / nr_base)
        display_r = max(3, int(nr_base * local_scale))

        img = self.images.get(tier)
        if img is not None:
            d = display_r * 2
            try:
                scaled = pygame.transform.smoothscale(img, (d, d))
            except Exception:
                scaled = pygame.transform.scale(img, (d, d))
            mask = pygame.Surface((d, d), pygame.SRCALPHA)
            mask.fill((0, 0, 0, 0))
            pygame.draw.circle(mask, (255, 255, 255, 255),
                               (display_r, display_r), display_r)
            result = scaled.copy()
            result.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            self.screen.blit(result, (int(cx - display_r), int(cy - display_r)))
        else:
            pygame.draw.circle(self.screen, TIERS[tier]["color"],
                               (int(cx), int(cy)), display_r)
            border = tuple(max(0, c - 50) for c in TIERS[tier]["color"])
            bw = max(1, si(1))
            pygame.draw.circle(self.screen, border, (int(cx), int(cy)),
                               display_r, width=bw)

    def _draw_button_bar(self, game):
        """画面外左上角按钮栏：重来/放大/全屏/最小/调试"""
        by = si(2)
        bh = si(BUTTON_BAR_H)
        # 半透明背景条
        bg = pygame.Surface((self.screen.get_width(), bh), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 100))
        self.screen.blit(bg, (0, by))

        for bx, bw, label, _action in BUTTONS:
            # 非调试模式跳过调试按钮
            if _action == "debug" and not game.debug_allowed:
                continue
            left = si(bx)
            right = left + si(bw)
            w = right - left
            # 按钮背景
            btn = pygame.Surface((w, bh - si(2)), pygame.SRCALPHA)
            btn.fill((60, 60, 80, 150))
            pygame.draw.rect(btn, (120, 120, 150, 200),
                             btn.get_rect(), width=1, border_radius=si(3))
            self.screen.blit(btn, (left, by + si(1)))

            # 按钮文字
            fs = max(9, si(12))
            font = self._font(fs)
            txt = font.render(label, True, TEXT_COLOR)
            self.screen.blit(txt, (left + (w - txt.get_width()) // 2,
                                   by + (bh - txt.get_height()) // 2))

    def _draw_tier_selector(self, game):
        """等级选择器横条：点击锁定掉落等级。"""
        bar_y = si(BUTTON_BAR_H) + si(4)
        bar_h = si(24)

        bg = pygame.Surface((self.screen.get_width(), bar_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 120))
        self.screen.blit(bg, (0, bar_y))

        btn_w = si(28)
        gap = si(2)
        for t in range(len(TIERS)):
            left = si(4) + t * (btn_w + gap)
            color = TIERS[t]["color"]
            sel = (game.debug_tier == t)
            alpha = 220 if sel else 100
            btn = pygame.Surface((btn_w, bar_h - si(2)), pygame.SRCALPHA)
            btn.fill((*color, alpha))
            if sel:
                pygame.draw.rect(btn, (255, 255, 255, 255),
                                 btn.get_rect(), width=si(2))
            self.screen.blit(btn, (left, bar_y + si(1)))
            fs = max(8, si(11))
            font = self._font(fs)
            txt = font.render(str(t), True, (255, 255, 255) if sel else (200, 200, 200))
            self.screen.blit(txt, (left + (btn_w - txt.get_width()) // 2,
                                   bar_y + (bar_h - txt.get_height()) // 2))

        # "自动" 按钮
        auto_x = si(4) + len(TIERS) * (btn_w + gap) + gap
        auto_w = si(40)
        auto_btn = pygame.Surface((auto_w, bar_h - si(2)), pygame.SRCALPHA)
        auto_btn.fill((80, 80, 100, 180 if game.debug_tier is None else 100))
        if game.debug_tier is None:
            pygame.draw.rect(auto_btn, (255, 255, 255, 255),
                             auto_btn.get_rect(), width=si(2))
        self.screen.blit(auto_btn, (auto_x, bar_y + si(1)))
        afs = max(8, si(11))
        afont = self._font(afs)
        atxt = afont.render("自动", True, (255, 255, 255))
        self.screen.blit(atxt, (auto_x + (auto_w - atxt.get_width()) // 2,
                                 bar_y + (bar_h - atxt.get_height()) // 2))
        return bar_y + bar_h  # 返回选择器底部 Y

    def _draw_weight_editor(self, game, y_start: int):
        """掉落权重编辑栏。"""
        wt_y = y_start + si(3)
        wt_h = si(22)
        wt_bg = pygame.Surface((self.screen.get_width(), wt_h), pygame.SRCALPHA)
        wt_bg.fill((0, 0, 0, 100))
        self.screen.blit(wt_bg, (0, wt_y))

        wfs = max(8, si(11))
        wfont = self._font(wfs)
        lbl = wfont.render("权重:", True, (180, 180, 180))
        self.screen.blit(lbl, (si(4), wt_y + (wt_h - lbl.get_height()) // 2))

        max_d = get_max_drop()
        weights = game.debug_weights if game.debug_weights is not None else [1] * (max_d + 1)
        total_w = sum(weights) if sum(weights) > 0 else 1
        cell_x = si(52)
        cell_w = si(46)

        for t in range(max_d + 1):
            left = cell_x + t * (cell_w + si(4))
            w = weights[t] if t < len(weights) else 1
            pct = int(w / total_w * 100)
            color = TIERS[t]["color"]
            swatch = pygame.Surface((si(14), wt_h - si(4)), pygame.SRCALPHA)
            swatch.fill((*color, 200))
            self.screen.blit(swatch, (left, wt_y + si(2)))
            wtxt = wfont.render(f"T{t}:{pct}%", True, (255, 255, 255))
            self.screen.blit(wtxt, (left + si(16), wt_y + (wt_h - wtxt.get_height()) // 2))
            # +/- 按钮
            pm_w = si(12)
            pm_h = si(10)
            pbtn = pygame.Surface((pm_w, pm_h), pygame.SRCALPHA)
            pbtn.fill((60, 160, 60, 200))
            self.screen.blit(pbtn, (left + cell_w - pm_w * 2 - si(2), wt_y + si(2)))
            mbtn = pygame.Surface((pm_w, pm_h), pygame.SRCALPHA)
            mbtn.fill((200, 60, 60, 200))
            self.screen.blit(mbtn, (left + cell_w - pm_w, wt_y + si(2) + pm_h + si(1)))

        # 重置按钮
        rst_x = cell_x + (max_d + 1) * (cell_w + si(4)) + si(8)
        rst_w = si(36)
        rst_btn = pygame.Surface((rst_w, wt_h - si(4)), pygame.SRCALPHA)
        rst_btn.fill((100, 100, 120, 160))
        self.screen.blit(rst_btn, (rst_x, wt_y + si(2)))
        rst_txt = wfont.render("重置", True, TEXT_COLOR)
        self.screen.blit(rst_txt, (rst_x + (rst_w - rst_txt.get_width()) // 2,
                                    wt_y + (wt_h - rst_txt.get_height()) // 2))
        return wt_y + wt_h  # 返回权重栏底部 Y

    def _draw_tech_info(self, game, y_start: int):
        """技术信息：FPS/球数/分数/缩放。"""
        info_y = y_start + si(4)
        font = self._font(max(10, si(13)))
        lines = [
            f"FPS:{int(self.clock.get_fps())} 球:{len([i for i in game.items if i.alive])}",
            f"分:{game.score} 缩放:{get_scale():.3f}",
        ]
        for line in lines:
            s = font.render(line, True, (0, 0, 0))
            self.screen.blit(s, (si(7), info_y + 1))
            t = font.render(line, True, (120, 255, 120))
            self.screen.blit(t, (si(6), info_y))
            info_y += si(16)

    def _draw_debug(self, game):
        """调试模式（轻量）：等级选择器 + 权重编辑 + 技术信息。"""
        bar_bottom = self._draw_tier_selector(game)
        wt_bottom = self._draw_weight_editor(game, bar_bottom)
        self._draw_tech_info(game, wt_bottom)

    def _draw_game_over(self, game):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill(OVERLAY_COLOR)
        self.screen.blit(overlay, (0, 0))

        w = self.screen.get_width()
        h = self.screen.get_height()

        # Game Over
        gof = self._font(max(20, si(48)))
        go = gof.render("游戏结束", True, (255, 80, 80))
        cy = h // 2 - si(120)
        self.screen.blit(go, (w // 2 - go.get_width() // 2, cy))
        cy += si(55)

        # Final score
        ssf = self._font(max(16, si(32)))
        fs = ssf.render(f"分数：{game.score}", True, SCORE_COLOR)
        self.screen.blit(fs, (w // 2 - fs.get_width() // 2, cy))
        cy += si(35)

        # Debug indicator
        if game.debug_tainted:
            dbf = self._font(max(10, si(16)))
            db = dbf.render("（调试模式不计分）", True, (200, 140, 60))
            self.screen.blit(db, (w // 2 - db.get_width() // 2, cy))
            cy += si(22)

        # High score / New record
        hsf = self._font(max(14, si(28)))
        if not game.debug_tainted and game.score >= game.high_score and game.score > 0:
            hs = hsf.render("新纪录！", True, (255, 200, 50))
            self.screen.blit(hs, (w // 2 - hs.get_width() // 2, cy))
            cy += si(35)
        elif game.high_score > 0:
            hs = hsf.render(f"最高：{game.high_score}", True, TEXT_COLOR)
            self.screen.blit(hs, (w // 2 - hs.get_width() // 2, cy))
            cy += si(35)

        # Score history
        if game.score_history and len(game.score_history) > 1:
            hdrf = self._font(max(10, si(16)))
            hdr = hdrf.render("历史记录：", True, (180, 180, 200))
            self.screen.blit(hdr, (w // 2 - hdr.get_width() // 2, cy))
            cy += si(20)
            scf = self._font(max(9, si(14)))
            # Show up to 5 recent scores
            for s in game.score_history[:5]:
                sc = scf.render(f"  {s}", True, TEXT_COLOR)
                self.screen.blit(sc, (w // 2 - sc.get_width() // 2, cy))
                cy += si(18)

        # Restart
        cy += si(10)
        prf = self._font(max(12, si(22)))
        pr = prf.render("点击重新开始", True, TEXT_COLOR)
        self.screen.blit(pr, (w // 2 - pr.get_width() // 2, cy))
