"""v2.0.0.0 设置界面 — 模式参数编辑器。

布局：左侧模式列表 + 右侧三标签页参数编辑（数学模型/物理引擎/艺术框架）。
支持：tkinter文件浏览、图片自动处理、参数加减调节、文本编辑、新建/复制/删除/重命名。
"""

from __future__ import annotations

import os
import math as _math
import pygame
from constants import BG_COLOR, TEXT_COLOR, SCORE_COLOR, CONTAINER_BORDER, s, si
from image_processor import process_ball_image

# ── 常量和配置 ──────────────────────────────────────────────

PANEL_W_RATIO = 0.30       # 左侧模式列表面板占宽比
TAB_H = 36                  # 标签页高度（基值）
ROW_H = 32                  # 每行高度
FONT_SIZE = 13
SMALL_FONT = 11
TITLE_FONT = 20

# 参数步进配置：(字段名, 显示名, 步长, 最小值, 最大值, 小数位数)
MATH_PARAMS = [
    ("container_width",  "容器宽",    5,   200, 800, 0),
    ("overflow_line_y",  "溢出线Y",   5,    50, 500, 0),
    ("n_tiers",          "Tier数",    1,     2,  17, 0),
    ("max_drop",         "最大掉落",   1,     0,  16, 0),
    ("drop_line_y",      "掉落线Y",   2,    20, 300, 0),
]

PHYSICS_PARAMS = [
    ("gravity",          "重力 g",        50,    100, 5000, 0),
    ("initial_vy",       "初速 v₀",       50,      0, 5000, 0),
    ("damping",          "弹性 k",       0.05,    0.0, 1.0, 2),
    ("friction_ball",    "球摩擦 μ",      0.05,   0.0, 1.0, 2),
    ("friction_wall",    "壁摩擦 μ_w",    0.05,   0.0, 1.0, 2),
    ("air_resistance",   "空气阻力 μ_a",  0.01,   0.0, 0.5, 2),
    ("elasticity_wall",  "壁弹性 k_w",    0.05,   0.0, 1.0, 2),
    ("drop_delay",       "掉落冷却(s)",   0.05,  0.05, 3.0, 2),
    ("overflow_time",    "超线时间(s)",   0.1,    0.5, 10.0, 1),
    ("attract_force",    "磁力强度",      50,      0, 3000, 0),
    ("attract_range",    "磁力范围",       2,      0,  100, 0),
    ("angular_damping",  "旋转阻尼/s",    0.05,   0.5, 0.999, 2),
    ("wall_rotational_friction", "壁旋转摩擦", 0.05, 0.0, 0.95, 2),
]

ART_PARAMS = [
    ("background_overlay_alpha", "背景遮罩",  5,   0, 255, 0),
]

TIER_MATH_FIELDS = [
    ("radius",      "半径",  2,  5, 200, 0),
    ("points",      "分数",  1,  1, 9999, 0),
    ("drop_weight", "权重",  0.1, 0.0, 10.0, 1),
]

TIER_PHYSICS_FIELDS = [
    ("mass",        "质量",   5,   0, 5000, 0),
    ("friction",    "摩擦",   0.05, 0.0, 1.0, 2),
    ("elasticity",  "弹性",   0.05, 0.0, 1.0, 2),
]

TIER_ART_FIELDS = [
    ("message", "消息", None),
    ("image",   "图片", None),
]


# ── 帮助函数 ────────────────────────────────────────────────

def _browse_file(title="选择文件", filetypes=None):
    """打开系统文件浏览对话框，返回所选路径或空字符串。"""
    try:
        import tkinter.filedialog as fd
        from tkinter import Tk
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        path = fd.askopenfilename(title=title, filetypes=filetypes or [])
        root.destroy()
        return path if path else ""
    except Exception:
        return ""


def _text_input_dialog(renderer, screen, title: str, initial: str = "",
                       max_len: int = 50) -> str:
    """简易文本输入对话框。返回输入的字符串（空=取消）。"""
    font = renderer._font(si(18))
    small = renderer._font(si(13))
    text = initial
    while True:
        w, h = screen.get_size()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return initial
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return initial
                if event.key == pygame.K_RETURN:
                    return text
                if event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                elif event.unicode and len(text) < max_len:
                    text += event.unicode
        # 渲染
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        dw, dh = si(360), si(120)
        dx, dy = (w - dw) // 2, (h - dh) // 2
        dlg = pygame.Surface((dw, dh), pygame.SRCALPHA)
        dlg.fill((40, 42, 60, 240))
        pygame.draw.rect(dlg, (80, 85, 120, 255), dlg.get_rect(),
                         width=si(2), border_radius=si(6))
        screen.blit(dlg, (dx, dy))
        t = font.render(title, True, TEXT_COLOR)
        screen.blit(t, (dx + si(16), dy + si(12)))
        display = text + "_" if text else "___"
        inp = font.render(display, True, SCORE_COLOR)
        screen.blit(inp, (dx + si(20), dy + si(48)))
        hint = small.render("回车确认 · ESC取消", True, (140, 140, 160))
        screen.blit(hint, (dx + si(16), dy + si(82)))
        pygame.display.flip()
        pygame.time.wait(30)


def _number_edit(renderer, screen, title: str, value: float,
                 step: float, min_v: float, max_v: float,
                 decimals: int = 0) -> float:
    """数值微调对话框。返回新值。"""
    font = renderer._font(si(20))
    small = renderer._font(si(13))
    current = value
    while True:
        w, h = screen.get_size()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return value
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return value
                if event.key == pygame.K_RETURN:
                    return round(current, decimals)
                if event.key == pygame.K_LEFT:
                    current = max(min_v, current - step * 10)
                if event.key == pygame.K_RIGHT:
                    current = min(max_v, current + step * 10)
                if event.key == pygame.K_DOWN:
                    current = max(min_v, current - step)
                if event.key == pygame.K_UP:
                    current = min(max_v, current + step)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                dw, dh = si(300), si(130)
                dx, dy = (w - dw) // 2, (h - dh) // 2
                # — 按钮
                bw, bh = si(50), si(30)
                bx1 = dx + si(30)
                bx2 = dx + dw - si(80)
                by_center = dy + dh // 2 + si(5)
                if bx1 <= mx <= bx1 + bw and by_center - bh // 2 <= my <= by_center + bh // 2:
                    current = max(min_v, current - step)
                if bx2 <= mx <= bx2 + bw and by_center - bh // 2 <= my <= by_center + bh // 2:
                    current = min(max_v, current + step)

        # 渲染
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        dw, dh = si(300), si(130)
        dx, dy = (w - dw) // 2, (h - dh) // 2
        dlg = pygame.Surface((dw, dh), pygame.SRCALPHA)
        dlg.fill((40, 42, 60, 240))
        pygame.draw.rect(dlg, (80, 85, 120, 255), dlg.get_rect(),
                         width=si(2), border_radius=si(6))
        screen.blit(dlg, (dx, dy))
        t = font.render(title, True, TEXT_COLOR)
        screen.blit(t, (dx + si(16), dy + si(8)))
        fmt = f"{{:.{decimals}f}}"
        val = font.render(fmt.format(current), True, SCORE_COLOR)
        screen.blit(val, (dx + (dw - val.get_width()) // 2, dy + si(38)))
        # +/- 按钮
        bw, bh = si(50), si(30)
        bx1 = dx + si(30)
        bx2 = dx + dw - si(80)
        by_center = dy + dh // 2 + si(5)
        for bx, label in [(bx1, "－"), (bx2, "＋")]:
            btn = pygame.Surface((bw, bh), pygame.SRCALPHA)
            btn.fill((60, 60, 80, 180))
            pygame.draw.rect(btn, (120, 120, 150, 200), btn.get_rect(),
                             width=si(1), border_radius=si(4))
            screen.blit(btn, (bx, by_center - bh // 2))
            lb = small.render(label, True, TEXT_COLOR)
            screen.blit(lb, (bx + (bw - lb.get_width()) // 2, by_center - lb.get_height() // 2))
        hint = small.render("方向键微调 · 回车确认 · ESC取消", True, (140, 140, 160))
        screen.blit(hint, (dx + (dw - hint.get_width()) // 2, dy + dh - si(20)))
        pygame.display.flip()
        pygame.time.wait(30)


# ── 主设置界面 ──────────────────────────────────────────────

def run_settings_screen(renderer, screen, mode_manager):
    """设置界面主循环。

    renderer: Renderer 实例
    screen: pygame Surface
    mode_manager: ModeManager 单例
    """
    w, h = screen.get_size()
    panel_w = int(w * PANEL_W_RATIO)
    editor_x = panel_w + si(8)

    # 状态
    selected_id: str | None = mode_manager.active_id
    active_tab = 0  # 0=Math, 1=Physics, 2=Art
    scroll_offset = 0
    editing_text: tuple | None = None  # (field_key, ...) — 文本编辑状态
    hovered_tier: int | None = None

    font = renderer._font(si(FONT_SIZE))
    small_font = renderer._font(si(SMALL_FONT))
    title_font = renderer._font(si(TITLE_FONT))

    def _get_selected_mode():
        if selected_id is None:
            return None
        return mode_manager.get(selected_id)

    while True:
        modes = mode_manager.list_all()
        md = _get_selected_mode()
        is_builtin = md.builtin if md else True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                mode_manager.save()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    mode_manager.save()
                    return
                if editing_text:
                    # 文本编辑模式
                    if event.key == pygame.K_RETURN:
                        editing_text = None
                    elif event.key == pygame.K_BACKSPACE:
                        # 实际删除在 MOUSEBUTTONDOWN 时进入编辑
                        pass
                    continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                handled = False

                # ── 左上返回按钮 ──
                if si(8) <= mx <= si(76) and si(8) <= my <= si(36):
                    mode_manager.save()
                    return

                # ── 标签页切换 ──
                tab_y = si(50)
                for ti, tname in enumerate(["数学模型", "物理引擎", "艺术框架"]):
                    tx = editor_x + si(8) + ti * si(110)
                    tw = si(100)
                    if tx <= mx <= tx + tw and tab_y <= my <= tab_y + si(TAB_H):
                        active_tab = ti
                        scroll_offset = 0
                        handled = True
                        break
                if handled:
                    continue

                # ── 左侧模式列表 ──
                if md and mx < panel_w:
                    # 选择模式
                    list_y = si(100)
                    for i, m in enumerate(modes):
                        cy = list_y + i * si(ROW_H + 6)
                        if si(8) <= mx <= panel_w - si(8) and cy <= my <= cy + si(ROW_H):
                            if selected_id != m.id:
                                selected_id = m.id
                                scroll_offset = 0
                            handled = True
                            break
                    if handled:
                        continue

                    # 操作按钮
                    btn_y_base = list_y + len(modes) * si(ROW_H + 6) + si(12)
                    btn_w, btn_h = (panel_w - si(32)) // 3, si(28)
                    for bi, (label, action) in enumerate([
                        ("+新建", "new"), ("复制", "dup"), ("删除", "del"),
                    ]):
                        bx = si(12) + bi * (btn_w + si(4))
                        by = btn_y_base
                        if bx <= mx <= bx + btn_w and by <= my <= by + btn_h:
                            if action == "new":
                                name = _text_input_dialog(renderer, screen, "新建模式名称",
                                                          f"自定义{len(modes)}")
                                if name.strip():
                                    new_md = mode_manager.create(name.strip(), "lite")
                                    if new_md:
                                        selected_id = new_md.id
                            elif action == "dup" and md:
                                dup = mode_manager.duplicate(md.id)
                                if dup:
                                    selected_id = dup.id
                            elif action == "del" and md and not md.builtin:
                                mode_manager.delete(md.id)
                                selected_id = mode_manager.active_id
                            handled = True
                            break
                    if handled:
                        continue

                    # 重命名按钮
                    ren_y = btn_y_base + btn_h + si(6)
                    ren_w = panel_w - si(24)
                    if (md and not md.builtin and si(12) <= mx <= si(12) + ren_w
                            and ren_y <= my <= ren_y + si(26)):
                        new_name = _text_input_dialog(renderer, screen, "重命名模式", md.name)
                        if new_name.strip():
                            mode_manager.rename(md.id, new_name.strip())
                        handled = True
                    if handled:
                        continue

                # ── 右侧参数编辑 ──
                if md is None:
                    continue

                right_x = editor_x + si(8)
                right_w = w - right_x - si(12)
                content_y = si(50) + si(TAB_H) + si(8)

                # 模式级参数
                if active_tab == 0:
                    param_list = MATH_PARAMS
                    step_list = MATH_PARAMS
                elif active_tab == 1:
                    param_list = PHYSICS_PARAMS
                    step_list = PHYSICS_PARAMS
                else:
                    param_list = ART_PARAMS
                    step_list = ART_PARAMS

                # 检查是否点击了参数行
                py = content_y
                for field, label, step, min_v, max_v, dec in param_list:
                    row_y = py
                    if row_y <= my <= row_y + si(ROW_H) and right_x <= mx <= right_x + right_w:
                        cur = getattr(md, field, 0)
                        if isinstance(cur, bool):
                            setattr(md, field, not cur)
                        else:
                            new_val = _number_edit(renderer, screen, label, float(cur),
                                                    step, float(min_v), float(max_v), dec)
                            setattr(md, field, type(cur)(new_val))
                        mode_manager.save()
                        handled = True
                        break
                    py += si(ROW_H + 2)

                if handled:
                    continue

                # 旋转开关（物理标签页特有）
                if active_tab == 1:
                    rot_y = py + si(4)
                    if rot_y <= my <= rot_y + si(ROW_H) and right_x <= mx <= right_x + right_w:
                        md.rotation_enabled = not md.rotation_enabled
                        mode_manager.save()
                        continue

                # 初始序列编辑（数学标签页特有）
                if active_tab == 0:
                    seq_y = py + si(4)
                    if seq_y <= my <= seq_y + si(ROW_H) and right_x <= mx <= right_x + right_w:
                        seq_str = ",".join(str(x) for x in md.initial_sequence)
                        new_str = _text_input_dialog(renderer, screen, "初始序列(逗号分隔)", seq_str)
                        try:
                            new_seq = [int(x.strip()) for x in new_str.split(",") if x.strip()]
                            if new_seq:
                                md.initial_sequence = new_seq
                                mode_manager.save()
                        except ValueError:
                            pass
                        continue

                # 背景图、音效浏览（艺术标签页特有）
                if active_tab == 2:
                    art_y = py + si(4)
                    for afield, alabel in [("background_image", "背景图"),
                                            ("merge_sound", "合成音效"),
                                            ("victory_sound", "胜利音效")]:
                        if art_y <= my <= art_y + si(ROW_H) and right_x <= mx <= right_x + right_w:
                            cur = getattr(md, afield, "")
                            ft = None
                            if "sound" in afield:
                                ft = [("音频", "*.wav;*.mp3;*.ogg"), ("所有", "*.*")]
                            else:
                                ft = [("PNG图片", "*.png"), ("所有图片", "*.jpg;*.jpeg;*.png;*.bmp")]
                            path = _browse_file(f"选择{alabel}", ft)
                            if path:
                                # 复制到模式目录
                                import shutil
                                mode_dir = os.path.join(os.getcwd(), "modes", md.id)
                                os.makedirs(mode_dir, exist_ok=True)
                                fname = os.path.basename(path)
                                dest = os.path.join(mode_dir, fname)
                                try:
                                    shutil.copy2(path, dest)
                                    setattr(md, afield, fname)
                                except Exception:
                                    setattr(md, afield, fname)  # 即使复制失败也记录
                                mode_manager.save()
                            continue
                        art_y += si(ROW_H + 2)

                # ── Tier 参数 ──
                tier_header_y = max(content_y + len(param_list) * si(ROW_H + 2) + si(24),
                                    si(380))

                # 滚动区域
                tier_list_y = tier_header_y + si(20)
                tier_visible_h = h - tier_list_y - si(80)
                tiers_per_page = max(1, tier_visible_h // si(ROW_H + 2))

                # 滚动条
                if md and len(md.tiers) > tiers_per_page:
                    scroll_max = len(md.tiers) - tiers_per_page
                    scroll_bar_h = tier_visible_h
                    scroll_bar_x = right_x + right_w - si(12)
                    scroll_thumb_h = max(si(20), scroll_bar_h * tiers_per_page / len(md.tiers))
                    scroll_thumb_y = tier_list_y + (scroll_bar_h - scroll_thumb_h) * (
                        scroll_offset / scroll_max if scroll_max > 0 else 0)
                    if (scroll_bar_x <= mx <= scroll_bar_x + si(10)
                            and scroll_bar_h > 0):
                        # 点击滚动条
                        if my < scroll_thumb_y:
                            scroll_offset = max(0, scroll_offset - 3)
                        elif my > scroll_thumb_y + scroll_thumb_h:
                            scroll_offset = min(scroll_max, scroll_offset + 3)
                # 鼠标滚轮
                if event.button in (4, 5) and md:
                    if event.button == 4:  # 上滚
                        scroll_offset = max(0, scroll_offset - 1)
                    else:
                        scroll_offset = min(
                            max(0, len(md.tiers) - tiers_per_page), scroll_offset + 1)

                # Tier 点击
                if md:
                    for ti in range(scroll_offset, min(scroll_offset + tiers_per_page,
                                                        len(md.tiers))):
                        ty = tier_list_y + (ti - scroll_offset) * si(ROW_H + 2)
                        if ty <= my <= ty + si(ROW_H) and right_x <= mx <= right_x + right_w:
                            hovered_tier = ti

                            # 检查子字段点击
                            td = md.tiers[ti]
                            if active_tab == 0:
                                sub_fields = TIER_MATH_FIELDS
                            elif active_tab == 1:
                                sub_fields = TIER_PHYSICS_FIELDS
                            else:
                                sub_fields = TIER_ART_FIELDS

                            col_x = right_x + si(160)
                            for sf_name, sf_label, *rest in sub_fields:
                                col_w = si(100)
                                if rest:  # 数值字段
                                    step, minv, maxv, dec = rest
                                    # - 按钮
                                    if col_x <= mx <= col_x + si(18) and not is_builtin:
                                        cur = getattr(td, sf_name, 0)
                                        if cur is None:
                                            cur = 0
                                        setattr(td, sf_name, max(minv, cur - step))
                                        mode_manager.save()
                                        break
                                    # + 按钮
                                    if col_x + si(20) <= mx <= col_x + si(38) and not is_builtin:
                                        cur = getattr(td, sf_name, 0)
                                        if cur is None:
                                            cur = 0
                                        setattr(td, sf_name, min(maxv, cur + step))
                                        mode_manager.save()
                                        break
                                    # 值区域 — 点击编辑
                                    if col_x + si(40) <= mx <= col_x + col_w and not is_builtin:
                                        cur = getattr(td, sf_name, 0)
                                        if cur is None:
                                            cur = 0
                                        nv = _number_edit(renderer, screen,
                                                          f"T{ti} {td.name} {sf_label}",
                                                          float(cur), step, float(minv),
                                                          float(maxv), dec)
                                        setattr(td, sf_name,
                                                nv if dec > 0 else int(nv))
                                        mode_manager.save()
                                        break
                                else:  # 文本/图片字段
                                    if col_x <= mx <= col_x + col_w and not is_builtin:
                                        if sf_name == "image" and sf_label == "图片":
                                            # 浏览图片
                                            path = _browse_file(
                                                f"T{ti} {td.name} 图片",
                                                [("PNG", "*.png"),
                                                 ("所有图片",
                                                  "*.jpg;*.jpeg;*.png;*.bmp")])
                                            if path:
                                                result = process_ball_image(
                                                    path, md.id, ti)
                                                if result:
                                                    td.image = result
                                                    mode_manager.save()
                                        elif sf_name == "message":
                                            new_msg = _text_input_dialog(
                                                renderer, screen,
                                                f"T{ti} {td.name} 合成消息",
                                                td.message or "")
                                            if new_msg != (td.message or ""):
                                                td.message = new_msg
                                                mode_manager.save()
                                        else:  # image path string
                                            path = _browse_file(
                                                f"T{ti} {td.name} 图片",
                                                [("PNG", "*.png"),
                                                 ("所有图片",
                                                  "*.jpg;*.jpeg;*.png;*.bmp")])
                                            if path:
                                                result = process_ball_image(
                                                    path, md.id, ti)
                                                if result:
                                                    td.image = result
                                                    mode_manager.save()
                                        break
                                col_x += col_w + si(4)
                            break

        # ── 渲染 ──
        screen.fill(BG_COLOR)

        # 返回按钮
        pygame.draw.rect(screen, (60, 60, 80, 150),
                         (si(8), si(8), si(68), si(28)), border_radius=si(4))
        back_txt = small_font.render("← 返回", True, TEXT_COLOR)
        screen.blit(back_txt, (si(16), si(12)))

        # 标题
        title_txt = title_font.render("设置", True, SCORE_COLOR)
        screen.blit(title_txt, ((w - title_txt.get_width()) // 2, si(8)))

        # ── 左侧面板 ──
        panel_rect = pygame.Rect(0, si(50), panel_w, h - si(50))
        pygame.draw.rect(screen, (25, 27, 40), panel_rect)
        pygame.draw.line(screen, (60, 65, 90), (panel_w, si(50)), (panel_w, h), si(1))

        list_y = si(100)
        for i, m in enumerate(modes):
            cy = list_y + i * si(ROW_H + 6)
            is_sel = (m.id == selected_id)
            # 背景
            if is_sel:
                sel_bg = pygame.Surface((panel_w - si(16), si(ROW_H)), pygame.SRCALPHA)
                sel_bg.fill((60, 80, 120, 120))
                screen.blit(sel_bg, (si(8), cy))
            # 文本
            c = TEXT_COLOR if not m.locked else (120, 120, 120)
            if is_sel:
                c = SCORE_COLOR
            name_str = f"{'🔒 ' if m.locked else ''}{m.name}"
            if m.builtin:
                name_str += " · 内置"
            txt = font.render(name_str, True, c)
            screen.blit(txt, (si(12), cy + si(4)))
            # 编号
            num = small_font.render(str(i), True, (140, 140, 160))
            screen.blit(num, (panel_w - si(30), cy + si(6)))

        # 操作按钮
        btn_y_base = list_y + len(modes) * si(ROW_H + 6) + si(12)
        btn_w = (panel_w - si(32)) // 3
        btn_h = si(28)
        for bi, (label, _action) in enumerate([
            ("+新建", "new"), ("复制", "dup"), ("删除", "del"),
        ]):
            bx = si(12) + bi * (btn_w + si(4))
            by = btn_y_base
            disabled = (_action == "del" and (not md or md.builtin))
            alpha = 100 if disabled else 160
            btn = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
            btn.fill((60, 60, 80, alpha))
            pygame.draw.rect(btn, (120, 120, 150, alpha + 40), btn.get_rect(),
                             width=si(1), border_radius=si(4))
            screen.blit(btn, (bx, by))
            lb = small_font.render(label, True,
                                    TEXT_COLOR if not disabled else (120, 120, 120))
            screen.blit(lb, (bx + (btn_w - lb.get_width()) // 2,
                              by + (btn_h - lb.get_height()) // 2))

        # 重命名按钮
        if md and not md.builtin:
            ren_y = btn_y_base + btn_h + si(6)
            ren_w = panel_w - si(24)
            ren_btn = pygame.Surface((ren_w, si(26)), pygame.SRCALPHA)
            ren_btn.fill((60, 60, 80, 120))
            pygame.draw.rect(ren_btn, (120, 120, 150, 160), ren_btn.get_rect(),
                             width=si(1), border_radius=si(4))
            screen.blit(ren_btn, (si(12), ren_y))
            ren_txt = small_font.render("✏ 重命名", True, TEXT_COLOR)
            screen.blit(ren_txt, (si(20), ren_y + si(4)))

        # ── 右侧参数编辑 ──
        if md is None:
            pygame.display.flip()
            pygame.time.wait(30)
            continue

        right_x = editor_x + si(8)
        right_w = w - right_x - si(12)
        content_y = si(50) + si(TAB_H) + si(8)

        # 标签页
        tab_y = si(50)
        for ti, tname in enumerate(["数学模型", "物理引擎", "艺术框架"]):
            tx = right_x + ti * si(110)
            tw = si(100)
            is_active = (ti == active_tab)
            tab_bg = pygame.Surface((tw, si(TAB_H)), pygame.SRCALPHA)
            tab_bg.fill((60, 80, 120, 180) if is_active else (40, 42, 60, 100))
            pygame.draw.rect(tab_bg, (120, 140, 200, 255) if is_active else (80, 85, 110, 120),
                             tab_bg.get_rect(), width=si(1),
                             border_top_left_radius=si(4), border_top_right_radius=si(4))
            screen.blit(tab_bg, (tx, tab_y))
            tt = font.render(tname, True, SCORE_COLOR if is_active else (160, 160, 180))
            screen.blit(tt, (tx + (tw - tt.get_width()) // 2, tab_y + si(8)))

        # 参数行
        if active_tab == 0:
            param_list = MATH_PARAMS
        elif active_tab == 1:
            param_list = PHYSICS_PARAMS
        else:
            param_list = ART_PARAMS

        py = content_y
        for field, label, step, min_v, max_v, dec in param_list:
            row_y = py
            cur = getattr(md, field, 0)
            if isinstance(cur, bool):
                display = "✓ 开启" if cur else "✗ 关闭"
            else:
                fmt = f"{{:.{dec}f}}"
                display = fmt.format(cur)
            line = font.render(f"{label}: {display}", True, TEXT_COLOR)
            screen.blit(line, (right_x, row_y + si(2)))
            # 编辑提示
            hint = small_font.render("(点击编辑)", True, (120, 120, 140))
            screen.blit(hint, (right_x + line.get_width() + si(8), row_y + si(4)))
            py += si(ROW_H + 2)

        # 旋转开关（物理标签页）
        if active_tab == 1:
            rot_y = py + si(4)
            rot_val = "✓ 开启" if md.rotation_enabled else "✗ 关闭"
            rot_line = font.render(f"旋转物理: {rot_val}", True, TEXT_COLOR)
            screen.blit(rot_line, (right_x, rot_y + si(2)))
            hint = small_font.render("(点击切换)", True, (120, 120, 140))
            screen.blit(hint, (right_x + rot_line.get_width() + si(8), rot_y + si(4)))
            py = rot_y + si(ROW_H + 2)

        # 初始序列（数学标签页）
        if active_tab == 0:
            seq_y = py + si(4)
            seq_str = ",".join(str(x) for x in md.initial_sequence)
            seq_line = font.render(f"初始序列: [{seq_str}]", True, TEXT_COLOR)
            screen.blit(seq_line, (right_x, seq_y + si(2)))
            hint = small_font.render("(点击编辑)", True, (120, 120, 140))
            screen.blit(hint, (right_x + seq_line.get_width() + si(8), seq_y + si(4)))
            py = seq_y + si(ROW_H + 2)

        # 艺术特殊字段
        if active_tab == 2:
            art_y = py + si(4)
            for afield, alabel in [("background_image", "背景图"),
                                    ("merge_sound", "合成音效"),
                                    ("victory_sound", "胜利音效")]:
                cur = getattr(md, afield, "") or "(无)"
                art_line = font.render(f"{alabel}: {cur}", True, TEXT_COLOR)
                screen.blit(art_line, (right_x, art_y + si(2)))
                hint = small_font.render("(点击浏览)", True, (120, 120, 140))
                screen.blit(hint, (right_x + art_line.get_width() + si(8), art_y + si(4)))
                art_y += si(ROW_H + 2)
            py = art_y

        # ── Tier 参数 ──
        tier_header_y = max(py + si(12), si(380))
        divider_y = tier_header_y
        pygame.draw.line(screen, (60, 65, 90), (right_x, divider_y),
                         (right_x + right_w, divider_y), si(1))
        tier_label = font.render("▼ Tier 参数（滚动查看）", True, (180, 180, 200))
        screen.blit(tier_label, (right_x, tier_header_y + si(2)))

        tier_list_y = tier_header_y + si(22)
        tier_visible_h = h - tier_list_y - si(60)
        tiers_per_page = max(1, tier_visible_h // si(ROW_H + 2))

        if md:
            # 滚动条
            if len(md.tiers) > tiers_per_page:
                scroll_max = len(md.tiers) - tiers_per_page
                scroll_bar_h = tier_visible_h
                scroll_bar_x = right_x + right_w - si(12)
                scroll_thumb_h = max(si(20),
                                     int(scroll_bar_h * tiers_per_page / len(md.tiers)))
                scroll_thumb_y = tier_list_y + int(
                    (scroll_bar_h - scroll_thumb_h) * (
                        scroll_offset / scroll_max if scroll_max > 0 else 0))
                pygame.draw.rect(screen, (50, 55, 70),
                                 (scroll_bar_x, tier_list_y, si(8), scroll_bar_h))
                pygame.draw.rect(screen, (100, 110, 140),
                                 (scroll_bar_x, scroll_thumb_y, si(8), scroll_thumb_h),
                                 border_radius=si(3))

            # Tier 行
            for ti in range(scroll_offset, min(scroll_offset + tiers_per_page,
                                                len(md.tiers))):
                ty = tier_list_y + (ti - scroll_offset) * si(ROW_H + 2)
                td = md.tiers[ti]

                # 背景
                if ti == hovered_tier:
                    hl_bg = pygame.Surface((right_w, si(ROW_H)), pygame.SRCALPHA)
                    hl_bg.fill((60, 80, 120, 60))
                    screen.blit(hl_bg, (right_x, ty))

                # 编号+名称
                tier_name = font.render(f"T{ti} {td.name}", True, TEXT_COLOR)
                screen.blit(tier_name, (right_x, ty + si(2)))

                # 参数值
                if active_tab == 0:
                    sub_fields = TIER_MATH_FIELDS
                elif active_tab == 1:
                    sub_fields = TIER_PHYSICS_FIELDS
                else:
                    sub_fields = TIER_ART_FIELDS

                col_x = right_x + si(160)
                for sf_name, sf_label, *rest in sub_fields:
                    col_w = si(110)
                    if rest:  # 数值字段
                        step, minv, maxv, dec = rest
                        cur = getattr(td, sf_name, 0)
                        if cur is None:
                            cur_str = "默认"
                        else:
                            fmt = f"{{:.{dec}f}}"
                            cur_str = fmt.format(cur)
                        val_text = small_font.render(f"{sf_label}:{cur_str}", True,
                                                      (200, 200, 220))
                        screen.blit(val_text, (col_x, ty + si(4)))
                    else:  # 文本字段
                        if sf_name == "image":
                            cur = td.image or "(无)"
                        elif sf_name == "message":
                            cur = td.message[:12] + "…" if len(td.message) > 12 else (
                                td.message or "(无)")
                        else:
                            cur = getattr(td, sf_name, "") or "(无)"
                        val_text = small_font.render(f"{sf_label}:{cur}", True,
                                                      (180, 200, 220))
                        screen.blit(val_text, (col_x, ty + si(4)))
                    col_x += col_w + si(4)

                # 内置模式锁定提示
                if is_builtin:
                    lock_txt = small_font.render("🔒", True, (120, 120, 120))
                    screen.blit(lock_txt, (right_x + right_w - si(30), ty + si(4)))

        # ── 底部提示 ──
        hint_text = "点击参数编辑 · 方向键微调数值 · 内置模式不可修改 · ESC返回"
        hint = small_font.render(hint_text, True, (120, 120, 140))
        screen.blit(hint, ((w - hint.get_width()) // 2, h - si(20)))

        pygame.display.flip()
        pygame.time.wait(30)
