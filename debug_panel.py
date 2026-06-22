"""v2.0.4.0 游戏内实时参数调试面板。

完整调试模式专用：半透明覆盖层 + 三标签页（数学/物理/艺术）
所有 ModeDefinition 参数可实时 ± 调整，立即生效。
"""

from __future__ import annotations

import pygame
from constants import (
    BG_COLOR, TEXT_COLOR, SCORE_COLOR, TEXT_CYAN, s, si, get_scale,
)
from data import TIERS, get_max_drop

# ── 面板常量 ──
PANEL_WIDTH_RATIO = 0.38      # 面板占屏幕宽比
TAB_H = 32                     # 标签页高度（基值）
ROW_H = 28                     # 每行高度
FONT_SIZE = 12
SMALL_FONT = 10
TITLE_FONT = 16

# ── 各标签页参数定义 ──

MATH_PARAMS = [
    ("container_width",   "容器宽",      5,   150,  800,  0),
    ("container_left",    "容器左",      2,     0,  300,  0),
    ("container_top",     "容器顶",      2,     0,  300,  0),
    ("container_bottom",  "容器底",      5,   400, 1200,  0),
    ("drop_line_y",       "掉落线Y",     2,    20,  300,  0),
    ("overflow_line_y",   "溢出线Y",     2,    40,  500,  0),
    ("n_tiers",           "Tier数",      1,     2,   17,  0),
    ("max_drop",          "最大掉落",    1,     0,   16,  0),
    ("overflow_time",     "超线时间(s)", 0.1,  0.5, 10.0, 1),
    ("drop_delay",        "掉落冷却(s)", 0.05, 0.05, 3.0, 2),
]

PHYSICS_PARAMS = [
    ("gravity",           "重力 g",       50,    100,  5000,  0),
    ("initial_vy",        "初速 v₀",      50,      0,  5000,  0),
    ("damping",           "弹性 k",       0.05,   0.0,  1.0,  2),
    ("friction_ball",     "球摩擦 μ",     0.05,   0.0,  1.0,  2),
    ("friction_wall",     "壁摩擦 μ_w",   0.05,   0.0,  1.0,  2),
    ("air_resistance",    "空气阻力 μ_a", 0.01,   0.0,  0.5,  2),
    ("elasticity_wall",   "壁弹性 k_w",   0.05,   0.0,  1.0,  2),
    ("attract_force",     "磁力强度",     50,      0,  3000,  0),
    ("attract_range",     "磁力范围",      2,      0,   100,  0),
    ("angular_damping",   "旋转阻尼/s",   0.05,   0.5,  0.999,2),
    ("wall_rotational_friction", "壁旋转摩擦", 0.05, 0.0, 0.95, 2),
]

ART_PARAMS = [
    ("background_overlay_alpha", "背景遮罩",  5,   0, 255, 0),
]

# Tier 级参数字段
TIER_MATH_FIELDS = [
    ("radius",      "半径",  1,   3, 250, 0),
    ("drop_weight", "权重",  0.1, 0.0, 10.0, 1),
    ("points",      "分数",  1,   1, 999, 0),
]

TIER_PHYSICS_FIELDS = [
    ("mass",        "质量",    5,   0, 5000, 0),
    ("friction",    "摩擦",    0.05, 0.0, 1.0, 2),
    ("elasticity",  "弹性",    0.05, 0.0, 1.0, 2),
]

# v2.2.0.0: 艺术标签页 tier 参数（非数值型用特殊处理）
TIER_ART_FIELDS = [
    ("color_r",     "R",      1,   0,  255, 0),
    ("color_g",     "G",      1,   0,  255, 0),
    ("color_b",     "B",      1,   0,  255, 0),
    ("image",       "图片",  None, None, None, 0),   # 文本字段
    ("message",     "消息",  None, None, None, 0),   # 文本字段
    ("sound",       "音效",  None, None, None, 0),   # 文本字段
]


# ── v2.2.0.0: 数值输入弹窗 ──────────────────────────────

def _show_number_dialog(screen, renderer, title: str, current_val, is_int: bool = False):
    """弹出数值输入对话框，返回新值或 None（取消）。"""
    w, h = screen.get_size()
    font = renderer._font(si(14))
    small = renderer._font(si(12))

    # 对话框尺寸
    dlg_w = si(280)
    dlg_h = si(140)
    dlg_x = (w - dlg_w) // 2
    dlg_y = (h - dlg_h) // 2

    val_str = str(current_val)
    cursor_visible = True
    cursor_timer = 0.0
    clock = pygame.time.Clock()
    running = True

    while running:
        dt = clock.tick(60) / 1000.0

        # 光标闪烁
        cursor_timer += dt
        if cursor_timer > 0.5:
            cursor_timer -= 0.5
            cursor_visible = not cursor_visible

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    try:
                        v = int(val_str) if is_int else float(val_str)
                        return v
                    except ValueError:
                        pass
                elif event.key == pygame.K_ESCAPE:
                    return None
                elif event.key == pygame.K_BACKSPACE:
                    val_str = val_str[:-1]
                elif event.key == pygame.K_DELETE:
                    val_str = ""
                elif event.unicode:
                    ch = event.unicode
                    if ch in "-.0123456789":
                        val_str += ch
                    cursor_timer = 0.0
                    cursor_visible = True

        # 渲染
        # 半透明遮罩
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        # 对话框背景
        dlg = pygame.Surface((dlg_w, dlg_h), pygame.SRCALPHA)
        dlg.fill((35, 38, 55, 245))
        pygame.draw.rect(dlg, (80, 85, 120, 240), dlg.get_rect(),
                         width=si(2), border_radius=si(8))
        screen.blit(dlg, (dlg_x, dlg_y))

        # 标题
        title_surf = font.render(title, True, SCORE_COLOR)
        screen.blit(title_surf, (dlg_x + si(12), dlg_y + si(10)))

        # 输入框
        inp_x = dlg_x + si(12)
        inp_y = dlg_y + si(42)
        inp_w = dlg_w - si(24)
        inp_h = si(32)
        pygame.draw.rect(screen, (50, 55, 75, 220),
                         (inp_x, inp_y, inp_w, inp_h), border_radius=si(4))
        pygame.draw.rect(screen, (100, 110, 150, 240),
                         (inp_x, inp_y, inp_w, inp_h),
                         width=si(1), border_radius=si(4))

        # 输入值 + 光标
        display_text = val_str
        if cursor_visible:
            display_text += "|"
        val_surf = font.render(display_text, True, TEXT_COLOR)
        screen.blit(val_surf, (inp_x + si(8), inp_y + (inp_h - val_surf.get_height()) // 2))

        # 底部提示
        hint = small.render("回车=确认  ESC=取消  数字/.-=输入", True, (150, 150, 180))
        screen.blit(hint, (dlg_x + si(12), dlg_y + dlg_h - si(24)))

        pygame.display.flip()

    return None


class DebugPanel:
    """游戏内实时参数调试面板。"""

    def __init__(self, game):
        self.game = game
        self.visible = True       # 完整调试模式默认打开
        self.active_tab = 0       # 0=Math, 1=Physics, 2=Art
        self.scroll_offset = 0
        self._drag_scroll_thumb = False

    def toggle(self):
        self.visible = not self.visible

    # ── 渲染 ──

    def render(self, screen, renderer):
        """渲染调试面板覆盖层。"""
        if not self.visible:
            return

        w, h = screen.get_size()
        panel_w = int(w * PANEL_WIDTH_RATIO)
        px = w - panel_w  # 右侧面板
        py = 0

        font = renderer._font(si(FONT_SIZE))
        small = renderer._font(si(SMALL_FONT))
        tiny = renderer._font(max(7, si(8)))  # v2.2.0.0
        title_font = renderer._font(si(TITLE_FONT))

        game = self.game
        md = game.mode_def

        # ── 半透明背景 ──
        panel_bg = pygame.Surface((panel_w, h), pygame.SRCALPHA)
        panel_bg.fill((18, 20, 32, 230))
        screen.blit(panel_bg, (px, py))

        # 左边框
        pygame.draw.line(screen, (80, 85, 120, 200), (px, 0), (px, h), si(2))

        # ── 标题栏 ──
        title_y = si(6)
        title = title_font.render("调试面板", True, SCORE_COLOR)
        screen.blit(title, (px + si(8), title_y))

        # 关闭按钮
        close_x = px + panel_w - si(28)
        close_y = title_y
        close_btn = pygame.Surface((si(22), si(22)), pygame.SRCALPHA)
        close_btn.fill((200, 60, 60, 180))
        pygame.draw.rect(close_btn, (255, 100, 100, 220), close_btn.get_rect(),
                         width=si(1), border_radius=si(3))
        screen.blit(close_btn, (close_x, close_y))
        close_txt = small.render("✕", True, (255, 255, 255))
        screen.blit(close_txt, (close_x + (si(22) - close_txt.get_width()) // 2,
                                close_y + (si(22) - close_txt.get_height()) // 2))

        # ── 标签页 ──
        tab_y = si(34)
        tab_names = ["数学模型", "物理引擎", "艺术框架"]
        tab_w = (panel_w - si(20)) // 3
        for ti, tname in enumerate(tab_names):
            tx = px + si(8) + ti * tab_w
            tw = tab_w - si(4)
            is_active = (ti == self.active_tab)
            tab_bg_c = (60, 80, 120, 200) if is_active else (35, 38, 55, 140)
            tab_bd_c = (120, 140, 200, 255) if is_active else (70, 75, 95, 120)
            tab_bg = pygame.Surface((tw, si(TAB_H)), pygame.SRCALPHA)
            tab_bg.fill(tab_bg_c)
            pygame.draw.rect(tab_bg, tab_bd_c, tab_bg.get_rect(),
                             width=si(1), border_top_left_radius=si(4),
                             border_top_right_radius=si(4))
            screen.blit(tab_bg, (tx, tab_y))
            tt = font.render(tname, True, SCORE_COLOR if is_active else (170, 170, 190))
            screen.blit(tt, (tx + (tw - tt.get_width()) // 2,
                             tab_y + (si(TAB_H) - tt.get_height()) // 2))

        # ── 参数区域 ──
        content_y = tab_y + si(TAB_H) + si(4)
        content_h = h - content_y - si(56)  # 留底部信息栏

        # 选择参数列表
        if self.active_tab == 0:
            param_list = MATH_PARAMS
        elif self.active_tab == 1:
            param_list = PHYSICS_PARAMS
        else:
            param_list = ART_PARAMS

        # ── 计算总行数和滚动 ──
        n_mode_rows = len(param_list) + 2  # +2 for rotation toggle + initial_sequence
        if self.active_tab == 0:
            n_mode_rows += 0
        elif self.active_tab == 1:
            n_mode_rows += 0
        else:
            n_mode_rows += 4  # background_image, merge_sound, victory_sound, victory_music

        # Tier 子参数
        tier_start_row = n_mode_rows + 1  # +1 for divider
        tier_visible = max(0, len(md.tiers))
        total_rows = tier_start_row + tier_visible

        row_px_h = si(ROW_H + 2)
        visible_rows = max(1, content_h // row_px_h)
        max_scroll = max(0, total_rows - visible_rows)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

        # ── 裁剪区域 ──
        clip_rect = pygame.Rect(px, content_y, panel_w, content_h)
        screen.set_clip(clip_rect)

        row_y = content_y - self.scroll_offset * row_px_h

        # ── 绘制模式级参数 ──
        row_idx = 0
        for field, label, step, min_v, max_v, dec in param_list:
            cur = getattr(md, field, 0)
            self._draw_param_row(screen, font, small, px, panel_w, row_y,
                                 label, cur, field, step, min_v, max_v, dec)
            row_y += row_px_h
            row_idx += 1

        # 旋转开关（物理标签页）
        if self.active_tab == 1:
            rot_str = "✓ 开启" if md.rotation_enabled else "✗ 关闭"
            self._draw_bool_row(screen, font, px, panel_w, row_y,
                                "旋转物理", rot_str, "rotation_enabled")
            row_y += row_px_h
            row_idx += 1

        # 初始序列（数学标签页）
        if self.active_tab == 0:
            seq_str = ",".join(str(x) for x in md.initial_sequence[:8])
            if len(md.initial_sequence) > 8:
                seq_str += "…"
            self._draw_label_row(screen, font, px, panel_w, row_y,
                                 f"初始序列: [{seq_str}]")
            row_y += row_px_h
            row_idx += 1

        # 艺术特殊字段
        if self.active_tab == 2:
            for afield, alabel in [("background_image", "背景图"),
                                    ("merge_sound", "合成音效"),
                                    ("victory_sound", "胜利音效"),
                                    ("victory_music", "胜利音乐")]:
                cur = getattr(md, afield, "") or "(无)"
                self._draw_label_row(screen, small, px, panel_w, row_y,
                                     f"{alabel}: {cur}")
                row_y += row_px_h
                row_idx += 1

        # ── Tier 分隔线 ──
        row_y += si(2)
        pygame.draw.line(screen, (60, 65, 90, 180),
                         (px + si(6), row_y - si(1)),
                         (px + panel_w - si(6), row_y - si(1)), si(1))
        tier_label = small.render("▼ Tier 参数", True, (170, 170, 190))
        screen.blit(tier_label, (px + si(8), row_y))
        row_y += row_px_h

        # ── Tier 行 ──
        for ti in range(len(md.tiers)):
            td = md.tiers[ti]
            ty = row_y + ti * row_px_h

            # 背景高亮（偶数行）
            if ti % 2 == 0:
                hl = pygame.Surface((panel_w - si(8), row_px_h), pygame.SRCALPHA)
                hl.fill((40, 42, 55, 80))
                screen.blit(hl, (px + si(4), ty))

            # 名称 + 关键值
            name_str = f"T{ti} {td.name}"
            name_txt = small.render(name_str, True, TEXT_COLOR)
            screen.blit(name_txt, (px + si(8), ty + si(2)))

            # 选择子字段取决于标签页
            if self.active_tab == 0:
                sub_fields = TIER_MATH_FIELDS
            elif self.active_tab == 1:
                sub_fields = TIER_PHYSICS_FIELDS
            else:
                sub_fields = None  # 艺术标签页特殊处理

            if sub_fields is not None:
                # 数值子字段
                col_x = px + si(130)
                for sf_name, sf_label, s_step, s_min, s_max, s_dec in sub_fields:
                    cur = getattr(td, sf_name, 0)
                    if cur is None:
                        cur = 0
                    fmt = f"{{:.{s_dec}f}}"
                    val_str = fmt.format(cur)
                    # v2.2.0.0: 值文本可点击 → 弹出输入框
                    val_txt = small.render(f"{sf_label}:{val_str}", True, TEXT_CYAN)
                    screen.blit(val_txt, (col_x, ty + si(4)))
                    col_x += val_txt.get_width() + si(6)

                    # +/- 按钮
                    pm_w = si(14)
                    pm_h = si(11)
                    # +
                    p_y = ty + si(2)
                    p_btn = pygame.Surface((pm_w, pm_h), pygame.SRCALPHA)
                    p_btn.fill((50, 150, 50, 200))
                    screen.blit(p_btn, (col_x, p_y))
                    # -
                    m_y = ty + si(2) + pm_h + si(1)
                    m_btn = pygame.Surface((pm_w, pm_h), pygame.SRCALPHA)
                    m_btn.fill((200, 50, 50, 200))
                    screen.blit(m_btn, (col_x, m_y))
                    col_x += pm_w + si(6)

                    # v2.2.0.0: 全部应用按钮（仅物理标签页）
                    if self.active_tab == 1 and sf_name in ("mass", "friction", "elasticity"):
                        ab_w = si(16)
                        ab_h = si(11)
                        ab_btn = pygame.Surface((ab_w, ab_h), pygame.SRCALPHA)
                        ab_btn.fill((60, 120, 180, 200))
                        screen.blit(ab_btn, (col_x, p_y))
                        al_txt = tiny.render("全", True, (255, 255, 255))
                        screen.blit(al_txt, (col_x + (ab_w - al_txt.get_width()) // 2,
                                             p_y + (ab_h - al_txt.get_height()) // 2))
                        col_x += ab_w + si(4)
            else:
                # v2.2.0.0: 艺术标签页 — color RGB + image + message + sound
                col_x = px + si(130)
                # 颜色: R/G/B
                for ci, cname in enumerate(["R", "G", "B"]):
                    cv = td.color[ci]
                    c_txt = small.render(f"{cname}:{cv}", True, TEXT_CYAN)
                    screen.blit(c_txt, (col_x, ty + si(4)))
                    col_x += c_txt.get_width() + si(4)
                    # +/- 微按钮
                    pm_w2 = si(10)
                    pm_h2 = si(8)
                    p_btn2 = pygame.Surface((pm_w2, pm_h2), pygame.SRCALPHA)
                    p_btn2.fill((50, 150, 50, 200))
                    screen.blit(p_btn2, (col_x, ty + si(2)))
                    m_btn2 = pygame.Surface((pm_w2, pm_h2), pygame.SRCALPHA)
                    m_btn2.fill((200, 50, 50, 200))
                    screen.blit(m_btn2, (col_x, ty + si(2) + pm_h2 + si(1)))
                    col_x += pm_w2 + si(8)
                # 图片 / 消息 / 音效（文本显示）
                for tfield, tlabel in [("image", "图"), ("message", "消息"), ("sound", "音效")]:
                    tv = getattr(td, tfield, "") or "-"
                    if len(tv) > 8:
                        tv = tv[:7] + "…"
                    t_txt = tiny.render(f"{tlabel}:{tv}", True, (160, 160, 190))
                    screen.blit(t_txt, (col_x, ty + si(4)))
                    col_x += t_txt.get_width() + si(6)

        # ── 恢复裁剪 ──
        screen.set_clip(None)

        # ── 滚动条 ──
        if max_scroll > 0:
            bar_x = px + panel_w - si(10)
            bar_h = content_h
            bar_y = content_y
            thumb_h = max(si(20), int(bar_h * visible_rows / total_rows))
            thumb_y = bar_y + int((bar_h - thumb_h) * self.scroll_offset / max_scroll)
            pygame.draw.rect(screen, (50, 55, 70, 150),
                             (bar_x, bar_y, si(6), bar_h))
            pygame.draw.rect(screen, (110, 120, 150, 200),
                             (bar_x, thumb_y, si(6), thumb_h), border_radius=si(3))

        # ── 底部技术信息 ──
        info_y = h - si(52)
        info_bg = pygame.Surface((panel_w, si(52)), pygame.SRCALPHA)
        info_bg.fill((10, 12, 22, 210))
        screen.blit(info_bg, (px, info_y))
        pygame.draw.line(screen, (60, 65, 90, 180), (px, info_y),
                         (px + panel_w, info_y), si(1))

        lines = [
            f"FPS: {int(renderer.clock.get_fps())}  球: {len([i for i in game.items if i.alive])}",
            f"分数: {game.score}  缩放: {get_scale():.3f}",
            f"模式: {md.id}  掉落: 0~{get_max_drop()}",
        ]
        for li, line in enumerate(lines):
            t = small.render(line, True, (150, 255, 150))
            screen.blit(t, (px + si(8), info_y + si(4) + li * si(14)))

        # 调试模式警告
        if game.debug_tainted:
            warn = small.render("⚠ 调试已污染 — 分数不记录", True, (255, 180, 60))
            screen.blit(warn, (px + si(8), info_y + si(46)))

    # ── 参数行绘制辅助 ──

    def _draw_param_row(self, screen, font, small, px, panel_w, y,
                        label, value, field, step, min_v, max_v, dec):
        """绘制单行参数：[label]: [value]  [－] [+]"""
        fmt = f"{{:.{dec}f}}"
        val_str = fmt.format(value)
        line = font.render(f"{label}: {val_str}", True, TEXT_COLOR)
        screen.blit(line, (px + si(8), y + si(3)))

        # +/- 按钮
        btn_x = px + panel_w - si(56)
        btn_w = si(22)
        btn_h = si(13)
        gap = si(2)

        # + 按钮
        p_btn = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
        p_btn.fill((50, 150, 50, 200))
        pygame.draw.rect(p_btn, (100, 200, 100, 220), p_btn.get_rect(),
                         width=si(1), border_radius=si(2))
        screen.blit(p_btn, (btn_x, y + si(2)))
        p_txt = small.render("+", True, (255, 255, 255))
        screen.blit(p_txt, (btn_x + (btn_w - p_txt.get_width()) // 2,
                            y + si(2) + (btn_h - p_txt.get_height()) // 2))

        # - 按钮
        m_btn = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
        m_btn.fill((200, 50, 50, 200))
        pygame.draw.rect(m_btn, (255, 100, 100, 220), m_btn.get_rect(),
                         width=si(1), border_radius=si(2))
        screen.blit(m_btn, (btn_x + btn_w + gap, y + si(2)))
        m_txt = small.render("−", True, (255, 255, 255))
        screen.blit(m_txt, (btn_x + btn_w + gap + (btn_w - m_txt.get_width()) // 2,
                            y + si(2) + (btn_h - m_txt.get_height()) // 2))

    def _draw_bool_row(self, screen, font, px, panel_w, y, label, val_str, field):
        """绘制布尔开关行。"""
        line = font.render(f"{label}: {val_str}", True, TEXT_COLOR)
        screen.blit(line, (px + si(8), y + si(3)))
        # 切换按钮
        btn_x = px + panel_w - si(50)
        btn_w = si(44)
        btn_h = si(16)
        btn = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
        btn.fill((80, 80, 120, 200))
        pygame.draw.rect(btn, (140, 140, 180, 220), btn.get_rect(),
                         width=si(1), border_radius=si(3))
        screen.blit(btn, (btn_x, y + si(2)))
        tgl = font.render("切换", True, (255, 255, 255))
        screen.blit(tgl, (btn_x + (btn_w - tgl.get_width()) // 2,
                          y + si(2) + (btn_h - tgl.get_height()) // 2))

    def _draw_label_row(self, screen, font, px, panel_w, y, text):
        """纯文本行（不可编辑字段）。"""
        line = font.render(text, True, (160, 160, 180))
        screen.blit(line, (px + si(8), y + si(3)))

    # ── 点击处理 ──

    def handle_click(self, mx, my) -> bool:
        """处理鼠标点击。返回 True 表示点击已被消费。"""
        if not self.visible:
            return False

        w = self.game._scale * 600 / get_scale()  # approximate screen w
        # 获取实际屏幕尺寸
        return self._handle_click_impl(mx, my)

    def _handle_click_impl(self, mx, my) -> bool:
        """实际点击处理（需要知道屏幕尺寸）。"""
        game = self.game
        md = game.mode_def

        # 获取 screen 尺寸 — 从 renderer 不太方便，用 game 的 bounds 反推
        # 改用常量：面板在右侧 PANEL_WIDTH_RATIO 宽
        # 我们需要实际 screen 尺寸。这里通过 game.box_left/box_right 推算。
        # 但最可靠的是存储 screen ref。简化方案：由 main.py 传入 screen_w, screen_h。
        # 这里先实现骨架，实际尺寸由外部传入。
        return False  # 基类返回 False；实际处理在 main.py 中

    def handle_click_at(self, mx, my, screen_w, screen_h,
                        screen=None, renderer=None) -> bool:
        """处理点击（外部传入屏幕尺寸）。返回 True 表示已消费。
        v2.2.0.0: 可选 screen/renderer 用于数值输入弹窗。"""
        if not self.visible:
            return False

        panel_w = int(screen_w * PANEL_WIDTH_RATIO)
        px = screen_w - panel_w

        # 点击在面板外 → 不消费
        if mx < px:
            return False

        game = self.game
        md = game.mode_def
        font_sz = si(FONT_SIZE)

        # ── 关闭按钮 ──
        close_x = px + panel_w - si(28)
        close_y = si(6)
        if close_x <= mx <= close_x + si(22) and close_y <= my <= close_y + si(22):
            self.visible = False
            return True

        # ── 标签页切换 ──
        tab_y = si(34)
        tab_w = (panel_w - si(20)) // 3
        for ti in range(3):
            tx = px + si(8) + ti * tab_w
            tw = tab_w - si(4)
            if tx <= mx <= tx + tw and tab_y <= my <= tab_y + si(TAB_H):
                self.active_tab = ti
                self.scroll_offset = 0
                return True

        # ── 参数区域 ──
        content_y = tab_y + si(TAB_H) + si(4)
        content_h = screen_h - content_y - si(56)
        row_px_h = si(ROW_H + 2)

        if my < content_y or my > content_y + content_h:
            # 可能点击了底部信息区
            return mx >= px  # 在面板内但不操作

        # 计算点击的行索引
        rel_y = my - content_y
        clicked_row = self.scroll_offset + rel_y // row_px_h

        # ── 参数参数列表 ──
        if self.active_tab == 0:
            param_list = MATH_PARAMS
        elif self.active_tab == 1:
            param_list = PHYSICS_PARAMS
        else:
            param_list = ART_PARAMS

        n_mode_rows = len(param_list)
        row_idx = 0

        # 检查模式级参数行
        for field, label, step, min_v, max_v, dec in param_list:
            if clicked_row == row_idx:
                return self._adjust_param(md, field, step, min_v, max_v, dec,
                                          mx, px, panel_w,
                                          screen=screen, renderer=renderer)
            row_idx += 1

        # 旋转开关（物理标签页）
        if self.active_tab == 1:
            if clicked_row == row_idx:
                # 点击切换按钮
                btn_x = px + panel_w - si(50)
                btn_w = si(44)
                btn_h = si(16)
                row_y_abs = content_y + (row_idx - self.scroll_offset) * row_px_h
                if (btn_x <= mx <= btn_x + btn_w and
                        row_y_abs + si(2) <= my <= row_y_abs + si(2) + btn_h):
                    md.rotation_enabled = not md.rotation_enabled
                    game.sync_mode_def_to_runtime()
                    return True
            row_idx += 1

        # 初始序列（数学标签页，仅显示）
        if self.active_tab == 0:
            row_idx += 1  # display-only, click does nothing
            if clicked_row == row_idx - 1:
                return True  # 消费点击但不做操作

        # 艺术特殊字段（不可调，仅显示）
        if self.active_tab == 2:
            row_idx += 4  # background_image, merge_sound, victory_sound, victory_music

        # Tier 分隔线
        row_idx += 1  # divider
        row_idx += 1  # "▼ Tier 参数" 标签

        # Tier 行
        n_tiers = len(md.tiers)
        for ti in range(n_tiers):
            if clicked_row == row_idx:
                return self._adjust_tier(md, ti, mx, px, panel_w, row_idx,
                                         self.scroll_offset, content_y, row_px_h, game,
                                         screen=screen, renderer=renderer)
            row_idx += 1

        return mx >= px  # 在面板内消费点击

    def handle_scroll(self, y_delta: int) -> bool:
        """鼠标滚轮。返回 True 表示已消费。"""
        if not self.visible:
            return False
        self.scroll_offset = max(0, self.scroll_offset - y_delta)
        return True

    # ── 参数调整 ──

    def _adjust_param(self, mdl, field, step, min_v, max_v, dec, mx, px, panel_w,
                      screen=None, renderer=None) -> bool:
        """调整模式级数值参数。v2.2.0.0: 点击值文本弹出输入框。"""
        btn_x = px + panel_w - si(56)
        btn_w = si(22)
        val_x_start = px + si(8)
        val_x_end = btn_x - si(4)
        cur = getattr(mdl, field, 0)

        if mx >= btn_x and mx < btn_x + btn_w:
            # + 按钮
            new_val = min(max_v, cur + step)
        elif mx >= btn_x + btn_w + si(2) and mx < btn_x + btn_w * 2 + si(2):
            # - 按钮
            new_val = max(min_v, cur - step)
        elif val_x_start <= mx < val_x_end and screen is not None and renderer is not None:
            # v2.2.0.0: 点击值文本 → 弹出输入框
            is_int = (dec == 0)
            result = _show_number_dialog(screen, renderer, f"输入 {field}", cur, is_int)
            if result is not None:
                new_val = max(min_v, min(max_v, result))
            else:
                return True  # 取消
        else:
            return mx >= px  # 在参数行内但没点按钮，消费但不做操作

        if dec == 0:
            new_val = int(new_val)
        else:
            new_val = round(new_val, dec)

        setattr(mdl, field, type(cur)(new_val))
        self.game.sync_mode_def_to_runtime()
        return True

    def _adjust_tier(self, md, ti, mx, px, panel_w, row_idx,
                     scroll_offset, content_y, row_px_h, game,
                     screen=None, renderer=None) -> bool:
        """调整 Tier 级参数。v2.2.0.0: 支持艺术标签页 + 全应用 + 数值输入。"""
        td = md.tiers[ti]
        row_y_abs = content_y + (row_idx - scroll_offset) * row_px_h

        if self.active_tab == 0:
            sub_fields = TIER_MATH_FIELDS
        elif self.active_tab == 1:
            sub_fields = TIER_PHYSICS_FIELDS
        else:
            # 艺术标签页：color R/G/B + image/message/sound
            return self._adjust_tier_art(td, md, ti, mx, px, row_y_abs, screen, renderer)

        col_x = px + si(130)
        for sf_name, sf_label, s_step, s_min, s_max, s_dec in sub_fields:
            cur = getattr(td, sf_name, 0)
            if cur is None:
                cur = 0

            val_text_w = si(55)
            pm_w = si(14)
            pm_h = si(11)
            p_x = col_x + val_text_w
            p_y = row_y_abs + si(2)
            m_y = row_y_abs + si(2) + pm_h + si(1)
            ab_w = si(16) if self.active_tab == 1 and sf_name in ("mass", "friction", "elasticity") else 0

            # + 按钮
            if p_x <= mx <= p_x + pm_w and p_y <= my <= p_y + pm_h:
                new_val = min(s_max, cur + s_step)
                if s_dec == 0: new_val = int(new_val)
                else: new_val = round(new_val, s_dec)
                setattr(td, sf_name, type(cur)(new_val))
                self.game.sync_mode_def_to_runtime()
                return True
            # - 按钮
            if p_x <= mx <= p_x + pm_w and m_y <= my <= m_y + pm_h:
                new_val = max(s_min, cur - s_step)
                if s_dec == 0: new_val = int(new_val)
                else: new_val = round(new_val, s_dec)
                setattr(td, sf_name, type(cur)(new_val))
                self.game.sync_mode_def_to_runtime()
                return True
            # 全部应用按钮
            ab_x = p_x + pm_w + si(2)
            if ab_w > 0 and ab_x <= mx <= ab_x + ab_w and p_y <= my <= p_y + pm_h:
                val = cur if cur is not None else 0
                for t in md.tiers:
                    setattr(t, sf_name, type(val)(val))
                self.game.sync_mode_def_to_runtime()
                return True
            # 值文本 → 输入弹窗
            val_x_end = p_x - si(2)
            if col_x <= mx < val_x_end and screen is not None and renderer is not None:
                is_int = (s_dec == 0)
                result = _show_number_dialog(screen, renderer, f"T{ti} {sf_label}", cur, is_int)
                if result is not None:
                    new_val = max(s_min, min(s_max, result))
                    if s_dec == 0: new_val = int(new_val)
                    else: new_val = round(new_val, s_dec)
                    setattr(td, sf_name, type(cur)(new_val))
                    self.game.sync_mode_def_to_runtime()
                return True

            col_x += val_text_w + pm_w + si(6) + ab_w + (si(4) if ab_w > 0 else 0)

        return mx >= px

    def _adjust_tier_art(self, td, md, ti, mx, px, row_y_abs, screen, renderer) -> bool:
        """v2.2.0.0: 艺术标签页 tier 行编辑。"""
        col_x = px + si(130)
        pm_w2 = si(10)
        pm_h2 = si(8)

        # 颜色 R/G/B
        for ci in range(3):
            cv = td.color[ci]
            # +/- 微按钮
            p_x_r = col_x + si(28)
            if p_x_r <= mx <= p_x_r + pm_w2 and row_y_abs + si(2) <= my <= row_y_abs + si(2) + pm_h2:
                nc = list(td.color)
                nc[ci] = min(255, nc[ci] + 1)
                td.color = tuple(nc)
                self.game.sync_mode_def_to_runtime()
                return True
            m_x_r = p_x_r
            m_y_r = row_y_abs + si(2) + pm_h2 + si(1)
            if m_x_r <= mx <= m_x_r + pm_w2 and m_y_r <= my <= m_y_r + pm_h2:
                nc = list(td.color)
                nc[ci] = max(0, nc[ci] - 1)
                td.color = tuple(nc)
                self.game.sync_mode_def_to_runtime()
                return True
            # 值文本 → 输入
            if col_x <= mx < p_x_r and screen and renderer:
                result = _show_number_dialog(screen, renderer, f"T{ti} {'RGB'[ci]}", cv, True)
                if result is not None:
                    nc = list(td.color)
                    nc[ci] = max(0, min(255, result))
                    td.color = tuple(nc)
                    self.game.sync_mode_def_to_runtime()
                return True
            col_x += pm_w2 + si(32)

        # image / message / sound（文本字段，暂仅显示，点击待扩展）
        for tfield in ["image", "message", "sound"]:
            col_x += si(55)  # 估算文本宽度
        return mx >= px

    def _sync_tier_to_data(self, ti, td):
        """将 TierDef 变更同步到 data.TIERS 并更新 Item 半径。"""
        if ti < len(TIERS):
            TIERS[ti]["radius"] = td.radius
            TIERS[ti]["name"] = td.name
            TIERS[ti]["color"] = td.color
            TIERS[ti]["points"] = td.points
            TIERS[ti]["mass"] = td.mass
            TIERS[ti]["friction"] = td.friction
            TIERS[ti]["elasticity"] = td.elasticity
            TIERS[ti]["sound"] = getattr(td, "sound", "")
            TIERS[ti]["message"] = getattr(td, "message", "")
        # 重新计算所有球的半径
        scale = get_scale()
        for item in self.game.items:
            if item.alive and item.tier == ti:
                item.compute_radius(scale)
