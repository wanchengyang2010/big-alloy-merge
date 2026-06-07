"""Big Alloy Merge (合成大YK) — Suika-style physics merge game.

17 tiers of items. Drop same items → merge into next tier.
Only first 6 tiers spawn randomly. Stack past red line → game over.
Resizable window — content scales proportionally.
F11 = toggle fullscreen  |  ESC = quit
"""

import sys
import os
import pygame

from constants import (
    REF_WIDTH, REF_HEIGHT, INIT_WIDTH, INIT_HEIGHT,
    set_scale, get_scale, FPS, UPDATE_URL,
    BUTTONS, BUTTON_BAR_H, s, si,
)
from version import VERSION
from data import TIERS, get_max_drop
from game import Game
from renderer import Renderer
from updater import check_update_simple
from autoplay import DemoBot  # 显式导入确保 PyInstaller 打包

DEBUG_PASSWORD = "3919"


def run_mode_selection(renderer: Renderer, screen: pygame.Surface) -> tuple[str, bool]:
    """Show mode selection screen, return (mode, debug_enabled).
    Blocks until user selects a mode.
    """
    password = ""
    password_error = False
    waiting_for_password = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return ("full", False)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if waiting_for_password:
                        waiting_for_password = False
                        password = ""
                        password_error = False
                    continue

                if waiting_for_password:
                    if event.key == pygame.K_RETURN:
                        if password == DEBUG_PASSWORD:
                            return ("full", True)
                        else:
                            password_error = True
                            password = ""
                    elif event.key == pygame.K_BACKSPACE:
                        password = password[:-1]
                    elif event.unicode and event.unicode.isdigit():
                        password += event.unicode
                        password_error = False
                    continue

                # Mode selection via keyboard
                # if event.key == pygame.K_a:
                #     return ("full", False)  # 全模式待开发
                if event.key == pygame.K_b:
                    return ("lite", False)
                elif event.key == pygame.K_c:
                    waiting_for_password = True
                    password = ""
                    password_error = False
                elif event.key == pygame.K_d:
                    return ("demo", False)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                w, h = screen.get_size()
                scale = get_scale()
                card_w = si(400)
                card_h = si(80)
                start_y = si(300)
                gap = si(20)
                cx = (w - card_w) // 2

                if waiting_for_password:
                    # Click outside dialog or on ESC equivalent → cancel
                    waiting_for_password = False
                    password = ""
                    password_error = False
                    continue

                for i in range(4):
                    cy = start_y + i * (card_h + gap)
                    if cx <= mx <= cx + card_w and cy <= my <= cy + card_h:
                        if i == 0:  # a: full mode — 待开发
                            pass
                        elif i == 1:  # b: lite mode
                            return ("lite", False)
                        elif i == 2:  # c: debug
                            waiting_for_password = True
                            password = ""
                            password_error = False
                        elif i == 3:  # d: demo mode
                            return ("demo", False)

        if waiting_for_password:
            renderer.draw_password_dialog(password, password_error)
        else:
            renderer.draw_mode_selection()


def main():
    pygame.init()

    # ---- 窗口图标 ----
    _load_icon()

    pygame.display.set_caption("合成大YK — Big Alloy Merge")

    flags = pygame.RESIZABLE
    screen = pygame.display.set_mode((INIT_WIDTH, INIT_HEIGHT), flags)
    fullscreen = False

    _update_scale(screen)
    renderer = Renderer(screen)

    # ---- 启动闪屏 ----
    _run_splash(renderer, screen)

    # ---- 模式选择 ----
    mode, debug_allowed = run_mode_selection(renderer, screen)
    is_demo = (mode == "demo")
    if mode == "full":
        mode = "lite"  # 全模式待开发，强制转大西瓜模式
    if is_demo:
        mode = "lite"  # demo uses lite mode
    game = Game(mode=mode)
    game.debug_allowed = debug_allowed
    debug_mode = debug_allowed  # 仅密码验证通过后才启用调试
    renderer.reload_images()  # reload after TIERS switched by Game mode

    # ---- 演示模式 ----
    demo_bot = None
    if is_demo:
        demo_bot = DemoBot(game)
        # demo uses physics-based DROP_DELAY (free-fall time ≈ 0.96s)

    # ---- 拖动状态（触摸屏支持）----
    dragging = False
    drag_x = 0

    # ---- 异步检查更新 ----
    game.update_available = False
    game.update_info = None

    def _on_update_result(has_update, latest_version, download_url):
        if has_update:
            game.update_available = True
            game.update_info = (latest_version, download_url)

    if UPDATE_URL:
        check_update_simple(UPDATE_URL, VERSION, _on_update_result)

    # ---- 主循环 ----
    running = True
    while running:
        dt = renderer.clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.get_surface()
                _update_scale(screen)
                game.rescale(get_scale())

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                action = _get_button_action(mx, my)
                if action:
                    result = _handle_action(action, screen, fullscreen, game, debug_mode)
                    if action == "quit":
                        running = False
                    elif action == "fullscreen":
                        fullscreen = result
                        _update_scale(screen)
                        game.rescale(get_scale())
                    elif action == "maximize":
                        _update_scale(screen)
                        game.rescale(get_scale())
                    elif action == "debug" and debug_allowed:
                        debug_mode = not debug_mode
                        if debug_mode:
                            game.debug_tainted = True
                elif debug_allowed and debug_mode and _handle_debug_click(mx, my, game):
                    pass  # 调试面板点击已处理
                elif game.game_over:
                    game.restart()
                    if is_demo and demo_bot:
                        demo_bot = DemoBot(game)
                elif not is_demo and game.current_tier is not None and game.drop_cooldown <= 0.0:
                    # 容器内按下 → 开始拖动
                    if _in_container(mx, my, game):
                        dragging = True
                        drag_x = mx

            elif event.type == pygame.MOUSEMOTION:
                if dragging:
                    drag_x, _ = event.pos

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if dragging and not is_demo:
                    game.drop(drag_x)
                    dragging = False
                elif dragging:
                    dragging = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    screen = _set_fullscreen(screen, fullscreen)
                    _update_scale(screen)
                    game.rescale(get_scale())
                elif event.key == pygame.K_F3 and debug_allowed:
                    debug_mode = not debug_mode
                    if debug_mode:
                        game.debug_tainted = True
                elif event.key == pygame.K_r and game.game_over:
                    game.restart()

        # Demo bot auto-drop
        if is_demo and demo_bot and not game.game_over and game.drop_cooldown <= 0.0:
            x = demo_bot.decide_drop_x()
            game.drop(x)

        game.update(dt)
        renderer.draw(game, debug_mode, demo_bot,
                     drag_x if dragging else None)

    pygame.quit()
    sys.exit()


def _run_splash(renderer, screen):
    """显示启动闪屏，点击或 4 秒后进入模式选择。"""
    start = pygame.time.get_ticks()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                return  # 任意按键进入
        if pygame.time.get_ticks() - start > 4000:
            return
        renderer.draw_splash()
        pygame.time.wait(30)


def _load_icon():
    """加载窗口图标 icon.ico（缺失则跳过）。"""
    from constants import resource_path
    icon_path = resource_path("icon.ico")
    if os.path.isfile(icon_path):
        try:
            icon = pygame.image.load(icon_path)
            pygame.display.set_icon(icon)
        except Exception:
            pass  # 图标加载失败不阻塞游戏


def _get_button_action(mx, my):
    """检查鼠标点击是否命中按钮，返回 action 或 None。"""
    by = si(2)
    bh = si(BUTTON_BAR_H)
    if my < by or my > by + bh:
        return None
    for bx, bw, _label, action in BUTTONS:
        left = si(bx)
        right = left + si(bw)
        if left <= mx <= right:
            return action
    return None


def _handle_action(action, screen, fullscreen, game, debug_mode):
    """执行按钮动作。返回新的 fullscreen 状态。"""
    if action == "restart":
        game.restart()
    elif action == "fullscreen":
        fullscreen = not fullscreen
        _set_fullscreen(screen, fullscreen)
    elif action == "maximize":
        info = pygame.display.Info()
        # 使用桌面工作区大小（不覆盖任务栏）
        pygame.display.set_mode(
            (info.current_w - 40, info.current_h - 80),
            pygame.RESIZABLE,
        )
    elif action == "minimize":
        pygame.display.iconify()
    elif action == "debug":
        pass  # debug toggle 由调用方处理
    return fullscreen


def _set_fullscreen(screen, fullscreen):
    """切换全屏并返回新 screen surface。"""
    if fullscreen:
        info = pygame.display.Info()
        return pygame.display.set_mode(
            (info.current_w, info.current_h),
            pygame.FULLSCREEN | pygame.SCALED,
        )
    else:
        return pygame.display.set_mode(
            (INIT_WIDTH, INIT_HEIGHT), pygame.RESIZABLE,
        )


def _handle_debug_click(mx, my, game) -> bool:
    """处理调试面板点击：等级选择器 + 权重编辑。返回 True 表示已处理。"""
    bar_h = si(BUTTON_BAR_H)
    tier_bar_y = bar_h + si(4)
    tier_bar_h = si(24)

    # ---- 等级选择器 ----
    if tier_bar_y <= my <= tier_bar_y + tier_bar_h:
        btn_w = si(28)
        gap = si(2)
        for t in range(len(TIERS)):
            left = si(4) + t * (btn_w + gap)
            if left <= mx <= left + btn_w:
                game.debug_tier = t
                return True
        # "自动" 按钮
        auto_x = si(4) + len(TIERS) * (btn_w + gap) + gap
        auto_w = si(40)
        if auto_x <= mx <= auto_x + auto_w:
            game.debug_tier = None
            return True
        return True  # 点击在等级选择栏内但未命中按钮，不向下传递

    # ---- 权重编辑栏 ----
    wt_y = tier_bar_y + tier_bar_h + si(3)
    wt_h = si(22)
    if wt_y <= my <= wt_y + wt_h:
        cell_x = si(52)
        cell_w = si(46)
        # 确保 debug_weights 已初始化
        if game.debug_weights is None:
            game.debug_weights = [1] * (get_max_drop() + 1)
        for t in range(get_max_drop() + 1):
            left = cell_x + t * (cell_w + si(4))
            pm_w = si(12)
            pm_h = si(10)
            # + 按钮
            if (left + cell_w - pm_w * 2 - si(2) <= mx <= left + cell_w - pm_w - si(2)
                    and wt_y + si(2) <= my <= wt_y + si(2) + pm_h):
                game.debug_weights[t] = min(10, game.debug_weights[t] + 1)
                return True
            # - 按钮
            if (left + cell_w - pm_w <= mx <= left + cell_w
                    and wt_y + si(2) + pm_h + si(1) <= my <= wt_y + si(2) + pm_h * 2 + si(1)):
                game.debug_weights[t] = max(0, game.debug_weights[t] - 1)
                return True
        # 重置按钮
        rst_x = cell_x + 6 * (cell_w + si(4)) + si(8)
        rst_w = si(36)
        if rst_x <= mx <= rst_x + rst_w:
            game.debug_weights = None  # 恢复默认
            return True
        return True  # 点击在权重栏内

    return False


def _update_scale(screen: pygame.Surface):
    w, h = screen.get_size()
    scale = min(w / REF_WIDTH, h / REF_HEIGHT)
    set_scale(scale)


def _in_container(mx: float, my: float, game: Game) -> bool:
    """检查点击是否在游戏容器内（按钮栏下方）。"""
    bar_bottom = si(2 + BUTTON_BAR_H)  # 按钮栏底部
    if my < bar_bottom:
        return False
    if my > game.box_bottom:
        return False
    if mx < game.box_left or mx > game.box_right:
        return False
    return True


if __name__ == "__main__":
    main()
