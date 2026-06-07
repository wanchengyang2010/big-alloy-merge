"""Rendering — background, container, items, UI, effects, game-over."""

import os
import time
import pygame
import constants as _c

from constants import (
    VERSION,
    DROP_LINE_Y,
    BG_COLOR, CONTAINER_BG, CONTAINER_BORDER, DANGER_LINE_COLOR,
    TEXT_COLOR, SCORE_COLOR, PREVIEW_ALPHA, OVERLAY_COLOR,
    BUTTON_BAR_H, BUTTONS,
    s, si, get_scale, resource_path,
)
from data import TIERS, get_max_drop

ASSETS_DIR = resource_path("assets/images")


class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.images: dict[int, pygame.Surface | None] = {}
        self._font_path = None
        self._init_font()
        self._load_images()

    # ---- Font ----

    def _init_font(self):
        # Bundled font (for PyInstaller) + system fallbacks
        candidates = [
            resource_path("msyh.ttc"),
            resource_path("simhei.ttf"),
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
        ]
        for path in candidates:
            if os.path.isfile(path):
                try:
                    pygame.font.Font(path, 20)
                    self._font_path = path
                    return
                except Exception:
                    continue
        self._font_path = None

    def _font(self, size: int) -> pygame.font.Font:
        if self._font_path:
            return pygame.font.Font(self._font_path, size)
        return pygame.font.Font(None, size)

    # ---- Image loading ----

    def _load_images(self):
        self.images.clear()
        os.makedirs(ASSETS_DIR, exist_ok=True)
        for tier in range(len(TIERS)):
            filename = TIERS[tier].get("image", "")
            path = os.path.join(ASSETS_DIR, filename)
            img = None
            if filename and os.path.isfile(path):
                try:
                    raw = pygame.image.load(path).convert_alpha()
                    img = raw  # store original; scale at draw time
                except Exception:
                    img = None
            self.images[tier] = img

    def reload_images(self):
        """Call after window resize if images need re-scaling."""
        self._load_images()

    # ---- Mode Selection ----

    def draw_mode_selection(self):
        """Render the mode selection screen."""
        self.screen.fill(BG_COLOR)

        w, h = self.screen.get_size()
        scale = get_scale()
        title_font = self._font(si(36))
        card_font = self._font(si(20))
        desc_font = self._font(si(14))

        # Title
        title = title_font.render("选择模式", True, SCORE_COLOR)
        self.screen.blit(title, ((w - title.get_width()) // 2, si(150)))

        modes = [
            ("a", "2222 模式", "17 元素完整版 · 待开发", (100, 100, 100)),
            ("b", "大西瓜模式", "11 元素经典版 · 纯碰撞合成", (60, 200, 100)),
            ("c", "调试模式", "需要密码才能进入", (200, 140, 60)),
            ("d", "演示模式", "AI 自动游玩 · 观看通关过程", (180, 120, 220)),
        ]

        card_w = si(400)
        card_h = si(80)
        start_y = si(300)
        gap = si(20)

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
                lock_text = lock_font.render("🔒", True, (120, 120, 120))
                self.screen.blit(lock_text, (cx + card_w - si(40), cy + si(20)))

        # Footer
        footer = desc_font.render("点击卡片选择模式 · 亦可按键盘 b / c · 按 d 观看演示", True, (140, 140, 160))
        self.screen.blit(footer, ((w - footer.get_width()) // 2, h - si(60)))

        pygame.display.flip()

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

    # yk.png background (loaded once, cached)
    _splash_bg = None

    def draw_splash(self):
        """启动闪屏：yk.png 背景 + 名称 + 版本 + 发布者。"""
        w, h = self.screen.get_size()

        # 加载背景图（缓存）
        if Renderer._splash_bg is None:
            yk_path = resource_path("assets/yk.png")
            try:
                raw = pygame.image.load(yk_path).convert_alpha()
                # 缩放至窗口大小（保持比例，留黑边）
                iw, ih = raw.get_size()
                scale = min(w / iw, h / ih)
                nw, nh = int(iw * scale), int(ih * scale)
                Renderer._splash_bg = pygame.transform.smoothscale(raw, (nw, nh))
            except Exception:
                Renderer._splash_bg = False  # 标记加载失败

        # 黑色背景
        self.screen.fill((0, 0, 0))

        # 背景图居中
        if Renderer._splash_bg and Renderer._splash_bg is not False:
            bg = Renderer._splash_bg
            bw, bh = bg.get_size()
            self.screen.blit(bg, ((w - bw) // 2, (h - bh) // 2))

        # 半透明遮罩（底部 55%）
        overlay = pygame.Surface((w, int(h * 0.55)), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 130))
        self.screen.blit(overlay, (0, int(h * 0.45)))

        # ---- 文字叠加 ----
        cx = w // 2
        title_y = int(h * 0.50)

        # 应用名
        title_font = self._font(si(38))
        title = title_font.render("合成大YK", True, (255, 215, 90))
        self.screen.blit(title, (cx - title.get_width() // 2, title_y))

        # 英文副标题
        sub_font = self._font(si(14))
        sub = sub_font.render("Big Alloy Merge", True, (200, 200, 220))
        self.screen.blit(sub, (cx - sub.get_width() // 2, title_y + si(44)))

        # 版本号
        ver_font = self._font(si(18))
        ver = ver_font.render(f"v{VERSION[1:]}", True, (255, 255, 255))
        self.screen.blit(ver, (cx - ver.get_width() // 2, title_y + si(72)))

        # 发布者
        pub_font = self._font(si(16))
        pub = pub_font.render("Trash Panda Q Opal", True, (180, 180, 200))
        self.screen.blit(pub, (cx - pub.get_width() // 2, title_y + si(100)))

        # 提示文字（闪烁）
        hint_font = self._font(si(15))
        hint = hint_font.render("点击任意位置开始游戏", True, (255, 255, 255, 180))
        self.screen.blit(hint, (cx - hint.get_width() // 2, int(h * 0.86)))

        pygame.display.flip()

    # ---- Frame ----

    def draw(self, game, debug_mode=False, demo_bot=None, drag_x=None):
        self.screen.fill(BG_COLOR)
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
            self._draw_debug(game)
        if game.game_over:
            self._draw_game_over(game)
        pygame.display.flip()
        self.clock.tick(60)

    # ---- Sections ----

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

        # Circular clip mask
        mask = pygame.Surface((d, d), pygame.SRCALPHA)
        mask.fill((0, 0, 0, 0))
        pygame.draw.circle(mask, (255, 255, 255, 255), (r, r), r)

        result = scaled.copy()
        result.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # Border
        bw = max(1, si(2))
        pygame.draw.circle(self.screen, CONTAINER_BORDER, (cx, cy), r, width=bw)

        self.screen.blit(result, (cx - r, cy - r))

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
        vt = vf.render(VERSION, True, (*TEXT_COLOR, 120))
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

    def _draw_debug(self, game):
        """调试模式：显示等级选择器 + 技术信息。"""
        bar_y = si(BUTTON_BAR_H) + si(4)
        bar_h = si(24)

        # 半透明背景
        bg = pygame.Surface((self.screen.get_width(), bar_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 120))
        self.screen.blit(bg, (0, bar_y))

        # 17 个等级按钮 (0-16)
        btn_w = si(28)
        gap = si(2)
        for t in range(len(TIERS)):
            left = si(4) + t * (btn_w + gap)
            # 按钮背景
            color = TIERS[t]["color"]
            sel = (game.debug_tier == t)
            alpha = 220 if sel else 100
            btn = pygame.Surface((btn_w, bar_h - si(2)), pygame.SRCALPHA)
            btn.fill((*color, alpha))
            if sel:
                pygame.draw.rect(btn, (255, 255, 255, 255),
                                 btn.get_rect(), width=si(2))
            self.screen.blit(btn, (left, bar_y + si(1)))
            # 编号
            fs = max(8, si(11))
            font = self._font(fs)
            txt = font.render(str(t), True, (255, 255, 255) if sel else (200, 200, 200))
            self.screen.blit(txt, (left + (btn_w - txt.get_width()) // 2,
                                   bar_y + (bar_h - txt.get_height()) // 2))

        # "自动" 按钮（退出锁定）
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

        # ---- 掉落概率编辑栏 ----
        wt_y = bar_y + bar_h + si(3)
        wt_h = si(22)
        wt_bg = pygame.Surface((self.screen.get_width(), wt_h), pygame.SRCALPHA)
        wt_bg.fill((0, 0, 0, 100))
        self.screen.blit(wt_bg, (0, wt_y))

        # 标签
        wfs = max(8, si(11))
        wfont = self._font(wfs)
        lbl = wfont.render("权重:", True, (180, 180, 180))
        self.screen.blit(lbl, (si(4), wt_y + (wt_h - lbl.get_height()) // 2))

        # 6 个掉落等级 + 权重值
        weights = game.debug_weights if game.debug_weights is not None else [1] * 6
        total_w = sum(weights)
        cell_x = si(52)
        cell_w = si(46)

        for t in range(get_max_drop() + 1):
            left = cell_x + t * (cell_w + si(4))
            w = weights[t]
            pct = int(w / total_w * 100) if total_w > 0 else 0
            # 等级色块
            color = TIERS[t]["color"]
            swatch = pygame.Surface((si(14), wt_h - si(4)), pygame.SRCALPHA)
            swatch.fill((*color, 200))
            self.screen.blit(swatch, (left, wt_y + si(2)))
            # 权重数字
            wtxt = wfont.render(f"T{t}:{pct}%", True, (255, 255, 255))
            self.screen.blit(wtxt, (left + si(16), wt_y + (wt_h - wtxt.get_height()) // 2))
            # +/- 按钮
            pm_w = si(12)
            pm_h = si(10)
            # +
            pbtn = pygame.Surface((pm_w, pm_h), pygame.SRCALPHA)
            pbtn.fill((60, 160, 60, 200))
            self.screen.blit(pbtn, (left + cell_w - pm_w * 2 - si(2), wt_y + si(2)))
            # -
            mbtn = pygame.Surface((pm_w, pm_h), pygame.SRCALPHA)
            mbtn.fill((200, 60, 60, 200))
            self.screen.blit(mbtn, (left + cell_w - pm_w, wt_y + si(2) + pm_h + si(1)))

        # 重置按钮
        rst_x = cell_x + 6 * (cell_w + si(4)) + si(8)
        rst_w = si(36)
        rst_btn = pygame.Surface((rst_w, wt_h - si(4)), pygame.SRCALPHA)
        rst_btn.fill((100, 100, 120, 160))
        self.screen.blit(rst_btn, (rst_x, wt_y + si(2)))
        rst_txt = wfont.render("重置", True, TEXT_COLOR)
        self.screen.blit(rst_txt, (rst_x + (rst_w - rst_txt.get_width()) // 2,
                                    wt_y + (wt_h - rst_txt.get_height()) // 2))

        # ---- 技术信息 ----
        info_y = wt_y + wt_h + si(4)
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
