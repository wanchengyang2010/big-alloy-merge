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
    BUTTONS, BUTTON_BAR_H, s, si, get_user_data_dir,
)
from version import VERSION
from data import TIERS, get_max_drop, load_q_custom_tiers, save_q_custom_tiers
from game import Game, SAVEGAME_FILE, load_audio_settings, toggle_sound
from renderer import Renderer
from updater import check_update_simple, check_github_update
from autoplay import DemoBot  # 显式导入确保 PyInstaller 打包
from modes import mode_manager
from debug_panel import DebugPanel  # v2.0.4.0

def _get_debug_password() -> str:
    """读取调试密码。优先 合成大YK_Data/password.txt，否则默认 3919。"""
    try:
        pw_path = resource_path("password.txt")
        if os.path.isfile(pw_path):
            with open(pw_path, "r", encoding="utf-8") as f:
                pw = f.read().strip()
            if pw:
                return pw
    except Exception:
        pass
    return "3919"


DEBUG_PASSWORD = _get_debug_password()


def run_mode_selection(renderer: Renderer, screen: pygame.Surface,
                       has_save: bool = False,
                       saved_modes: list[tuple[str, str]] | None = None) -> tuple[str, bool]:
    """Show mode selection screen, return (mode_id, debug_enabled).
    v2.1.0.0: saved_modes = [(mode_id, mode_name), ...] 来自 Game.list_saves()。
    """
    if saved_modes is None:
        saved_modes = []
    saved_ids = {s[0] for s in saved_modes}
    password = ""
    password_error = False
    waiting_for_password = False
    pending_debug_mode = "debug"  # 记录是哪个调试模式触发了密码
    # 拖拽排序状态
    drag_idx: int | None = None      # 正在拖拽的卡片索引
    drag_offset_y: float = 0.0       # 鼠标与卡片顶部的偏移
    drag_y: float = 0.0              # 当前拖拽Y坐标

    while True:
        modes = mode_manager.list_all()  # 按 order 排序
        # 过滤：存档恢复卡片不在 list_all 中，单独处理
        w, h = screen.get_size()
        scale = get_scale()
        card_w = si(420)
        card_h = si(76)
        gap = si(14)
        # 齿轮按钮位置
        gear_x = w - si(50)
        gear_y = si(20)
        gear_sz = si(36)
        # v2.2.0.0: 声音按钮位置（齿轮左侧）
        sound_x = gear_x - si(50)
        sound_y = gear_y
        sound_sz = gear_sz

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return ("lite", False)

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
                            return (pending_debug_mode, True)
                        else:
                            password_error = True
                            password = ""
                    elif event.key == pygame.K_BACKSPACE:
                        password = password[:-1]
                    elif event.unicode and event.unicode.isdigit():
                        password += event.unicode
                        password_error = False
                    continue

                # 存档恢复快捷键
                if event.key == pygame.K_r and has_save:
                    return ("restore", False)

                # 数字键快速选择模式
                if event.unicode and event.unicode.isdigit():
                    idx = int(event.unicode)
                    playable = [m for m in modes if not m.locked]
                    if idx < len(modes) and not modes[idx].locked:
                        mode_manager.set_active(modes[idx].id)
                        return (modes[idx].id, False)

                # 兼容旧快捷键
                if event.key == pygame.K_a:
                    return ("full", False)
                if event.key == pygame.K_b:
                    return ("lite", False)
                elif event.key == pygame.K_c:
                    waiting_for_password = True
                    password = ""
                    password_error = False
                elif event.key == pygame.K_d:
                    return ("demo", False)
                elif event.key == pygame.K_q:
                    load_q_custom_tiers()
                    return ("qself", False)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                if waiting_for_password:
                    waiting_for_password = False
                    password = ""
                    password_error = False
                    continue

                # v2.2.0.0: 声音按钮 → 切换声音开关
                if (sound_x - sound_sz // 2 <= mx <= sound_x + sound_sz // 2
                        and sound_y - sound_sz // 2 <= my <= sound_y + sound_sz // 2):
                    from game import toggle_sound as _ts
                    _ts()
                    continue

                # 齿轮按钮 → 设置界面（P4实现）
                if (gear_x - gear_sz // 2 <= mx <= gear_x + gear_sz // 2
                        and gear_y - gear_sz // 2 <= my <= gear_y + gear_sz // 2):
                    from settings_ui import run_settings_screen
                    run_settings_screen(renderer, screen, mode_manager)
                    continue

                # 计算卡片区域
                cx = (w - card_w) // 2
                save_offset = 1 if has_save else 0
                start_y = si(280) + save_offset * (card_h + gap)

                # 恢复存档卡片
                if has_save:
                    ry = si(280)
                    if cx <= mx <= cx + card_w and ry <= my <= ry + card_h:
                        return ("restore", False)

                # 模式卡片点击
                for i, md in enumerate(modes):
                    cy = start_y + i * (card_h + gap)
                    if cx <= mx <= cx + card_w and cy <= my <= cy + card_h:
                        if md.locked:
                            continue  # 锁定模式不可选
                        # 点击卡片 → 开始拖拽（或直接选择）
                        drag_idx = i
                        drag_offset_y = my - cy
                        drag_y = float(cy)
                        break

                # 新建模式按钮
                new_y = start_y + len(modes) * (card_h + gap) + gap
                new_w = si(160)
                new_h = si(36)
                new_x = (w - new_w) // 2
                if (new_x <= mx <= new_x + new_w
                        and new_y <= my <= new_y + new_h):
                    _create_new_mode_dialog(renderer, screen, mode_manager)
                    continue

            elif event.type == pygame.MOUSEMOTION:
                if drag_idx is not None:
                    _, my = event.pos
                    drag_y = my - drag_offset_y

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if drag_idx is not None:
                    mx, my = event.pos
                    modes = mode_manager.list_all()
                    cx = (w - card_w) // 2
                    save_offset = 1 if has_save else 0
                    start_y = si(280) + save_offset * (card_h + gap)

                    # 判断松手位置，决定是否交换
                    for i in range(len(modes)):
                        cy = start_y + i * (card_h + gap)
                        if cy <= my <= cy + card_h and i != drag_idx:
                            # 交换顺序
                            id_list = [m.id for m in modes]
                            dragged = id_list.pop(drag_idx)
                            id_list.insert(i, dragged)
                            mode_manager.reorder(id_list)
                            break

                    # 如果没交换且拖拽距离很小 → 点击选择
                    if abs(drag_y - (start_y + drag_idx * (card_h + gap))) < si(10):
                        md = modes[drag_idx]
                        if not md.locked:
                            if md.id in ("debug", "full_debug"):
                                # 调试模式需要密码
                                waiting_for_password = True
                                pending_debug_mode = md.id
                                password = ""
                                password_error = False
                            else:
                                mode_manager.set_active(md.id)
                                return (md.id, False)

                    drag_idx = None

        if waiting_for_password:
            renderer.draw_password_dialog(password, password_error)
        else:
            renderer.draw_mode_selection_v2(modes, has_save=has_save,
                                            drag_idx=drag_idx, drag_y=drag_y,
                                            saved_ids=saved_ids)


def main():
    # v2.2.0.3: SDL 窗口居中（必须在 pygame.init() 之前）
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.init()

    # ---- 保存桌面分辨率（set_mode 前获取，避免 NOFRAME 窗口干扰）----
    desktop_sizes = pygame.display.get_desktop_sizes()
    if desktop_sizes:
        _DESKTOP_W, _DESKTOP_H = desktop_sizes[0]
    else:
        info = pygame.display.Info()
        _DESKTOP_W, _DESKTOP_H = info.current_w, info.current_h
    # 存为模块级变量供 _get_safe_window_size 使用
    globals()["_DESKTOP"] = (_DESKTOP_W, _DESKTOP_H)

    # ---- 窗口图标 ----
    _load_icon()
    pygame.display.set_caption("合成大YK — Big Alloy Merge")

    # ---- v2.2.0.2: 16:9 无边框闪屏窗（Word风格）----
    splash_w, splash_h = 960, 540  # 16:9
    screen = pygame.display.set_mode((splash_w, splash_h), pygame.NOFRAME)
    _update_scale(screen)
    renderer = Renderer(screen)

    # 1) 闪屏立即显示
    renderer.draw_splash(state="loading")
    # 2) 后台加载所有资源
    load_audio_settings()
    renderer._load_images()
    # 3) 就绪 → 等用户点击
    _wait_splash_click(renderer, screen)

    # ---- 切换为游戏窗口 ----
    init_w, init_h = _get_safe_window_size()
    screen = pygame.display.set_mode((init_w, init_h), pygame.RESIZABLE, vsync=1)
    _load_icon()
    pygame.display.set_caption("合成大YK — Big Alloy Merge")
    _update_scale(screen)
    renderer = Renderer(screen)
    renderer._load_images()  # 新 screen 需重新加载
    fullscreen = False

    # ---- v2.2.2.4: GitHub 自动检查更新 ----
    _update_notification = [None, None]  # [latest_version, download_url]

    def _on_github_result(has_update, latest_version, download_url):
        if has_update:
            _update_notification[0] = latest_version
            _update_notification[1] = download_url

    check_github_update(VERSION, _on_github_result)

    # ---- v2.1.0.0: 外层循环支持返回主界面 ----
    while True:
        # 检查 GitHub 更新通知（主线程安全渲染）
        if _update_notification[0] is not None:
            ver = _update_notification[0]
            url = _update_notification[1]
            _update_notification[0] = None
            _show_update_notification(renderer, screen, ver, url)

        # 存档检查（每轮刷新）
        saves = Game.list_saves()
        has_save = len(saves) > 0
        saved_ids = {s[0] for s in saves}

        # ---- 模式选择 ----
        mode_id, debug_allowed = run_mode_selection(
            renderer, screen, has_save=has_save, saved_modes=saves)

        # v2.3.0.0: 安装器预授权调试密码（debug_3919.ok 标记文件）
        if not debug_allowed:
            debug_allowed = _check_installer_debug_key()

        if mode_id == "quit":
            break

        is_demo = (mode_id == "demo")
        is_debug = (mode_id in ("debug", "full_debug"))

        if mode_id == "restore":
            state = Game.load_save_state()
            if state is None:
                mode_id = "lite"
                debug_allowed = False
                game = Game(mode_id=mode_id)
            else:
                saved_mode_id = state.get("mode_id") or state.get("mode", "lite")
                if saved_mode_id == "qself":
                    saved_mode_id = "lite"
                    load_q_custom_tiers()
                game = Game(mode_id=saved_mode_id)
                game.restore_from_save(state)
                debug_allowed = game.debug_allowed
                mode_id = saved_mode_id
                is_demo = (mode_id == "demo")
                is_debug = (mode_id in ("debug", "full_debug"))
        else:
            if mode_id == "qself":
                load_q_custom_tiers()
                mode_id = "lite"
            game = Game(mode_id=mode_id)
            game.debug_allowed = debug_allowed
            # v2.2.0.0: 开始背景音乐
            game._start_background_music()

        renderer.reload_images()

        # v2.1.0.0: 所有调试模式均创建实时参数面板
        debug_panel = None
        debug_mode = debug_allowed
        if is_debug:
            debug_panel = DebugPanel(game)
            debug_mode = True
            game.debug_tainted = True

        # ---- 演示模式 ----
        demo_bot = None
        if is_demo:
            demo_bot = DemoBot(game)

        # ---- 拖动状态 ----
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

        # ---- 游戏主循环 ----
        running = True
        return_to_menu = False  # v2.2.0.3: 区分菜单返回 vs 退出
        while running:
            dt = renderer.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game.save_to_file()
                    running = False

                elif event.type == pygame.VIDEORESIZE:
                    screen = pygame.display.get_surface()
                    _update_scale(screen)
                    game.rescale(get_scale())

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = pygame.mouse.get_pos()

                    # v2.0.4.0: 调试面板点击
                    if debug_panel is not None and debug_panel.visible:
                        w, h = screen.get_size()
                        if debug_panel.handle_click_at(mx, my, w, h,
                                                        screen=screen, renderer=renderer):
                            continue

                    action = _get_button_action(mx, my)
                    if action:
                        result = _handle_action(action, screen, fullscreen, game, debug_mode)
                        if action == "quit":
                            game.save_to_file()
                            running = False
                        elif action == "menu":
                            # v2.1.0.0: 返回主界面
                            game.save_to_file()
                            return_to_menu = True
                            running = False
                        elif action == "fullscreen":
                            fullscreen = result
                            _update_scale(screen)
                            game.rescale(get_scale())
                        elif action == "maximize":
                            _update_scale(screen)
                            game.rescale(get_scale())
                        elif action == "debug" and debug_allowed:
                            if debug_panel is not None:
                                debug_panel.toggle()
                            else:
                                debug_mode = not debug_mode
                                if debug_mode:
                                    game.debug_tainted = True
                    elif debug_allowed and debug_mode and _handle_debug_click(mx, my, game):
                        pass
                    elif _handle_sound_click(mx, my, screen):
                        pass
                    elif game.game_over:
                        game.restart()
                        if is_demo and demo_bot:
                            demo_bot = DemoBot(game)
                    elif not is_demo and game.current_tier is not None and game.drop_cooldown <= 0.0:
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

                elif event.type == pygame.MOUSEWHEEL:
                    if debug_panel is not None:
                        debug_panel.handle_scroll(event.y)

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        game.save_to_file()
                        running = False
                    elif event.key == pygame.K_F11:
                        fullscreen = not fullscreen
                        screen = _set_fullscreen(screen, fullscreen)
                        _update_scale(screen)
                        game.rescale(get_scale())
                    elif event.key == pygame.K_F3 and debug_allowed:
                        if debug_panel is not None:
                            debug_panel.toggle()
                        else:
                            debug_mode = not debug_mode
                            if debug_mode:
                                game.debug_tainted = True
                    elif event.key == pygame.K_r and game.game_over:
                        game.restart()

            # Demo bot
            if is_demo and demo_bot and not game.game_over and game.drop_cooldown <= 0.0:
                x = demo_bot.decide_drop_x()
                game.drop(x)

            game.update(dt)
            renderer.draw(game, debug_mode, demo_bot,
                         drag_x if dragging else None,
                         debug_panel=debug_panel)

        # 内层循环结束
        if return_to_menu:
            game.stop_music()
            continue  # 回到外层模式选择
        else:
            # 退出 / 关闭窗口 / ESC
            break

    pygame.quit()
    sys.exit()


def _wait_splash_click(renderer, screen):
    """v2.2.0.1: 闪屏已显示"加载完毕"，等待用户点击进入。"""
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
        renderer.draw_splash(state="ready")
        pygame.time.wait(30)


def _check_installer_debug_key() -> bool:
    """v2.3.0.0: 检查安装器写入的调试授权标记文件。
    同时检查安装目录和用户数据目录。
    """
    for d in (os.getcwd(), get_user_data_dir()):
        key_path = os.path.join(d, "debug_3919.ok")
        if os.path.isfile(key_path):
            try:
                with open(key_path, "r", encoding="utf-8") as fh:
                    content = fh.read().strip()
                if content == "3919":
                    return True
            except Exception:
                pass
    return False


def _load_icon():
    """加载窗口图标。优先 PNG（pygame 不支持 .ico），回退 .ico。"""
    from constants import resource_path
    # pygame.image.load 不支持 .ico 格式，优先用 PNG
    for name in ("icon.png", "theme.ico"):
        icon_path = resource_path(name)
        if os.path.isfile(icon_path):
            try:
                icon = pygame.image.load(icon_path)
                pygame.display.set_icon(icon)
                return
            except Exception:
                continue


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
            pygame.RESIZABLE, vsync=1,
        )
        _load_icon()
        pygame.display.set_caption("合成大YK — Big Alloy Merge")
    elif action == "minimize":
        pygame.display.iconify()
    elif action == "debug":
        pass  # debug toggle 由调用方处理
    return fullscreen


def _get_safe_window_size():
    """返回最大化窗口尺寸（保持 2:3 比例，仅留任务栏+装饰余量）。"""
    desktops = globals().get("_DESKTOP")
    if desktops:
        dw, dh = desktops
    else:
        info = pygame.display.Info()
        dw, dh = info.current_w, info.current_h

    # 极小余量：底部任务栏约 60px，左右各 20px
    usable_w = dw - 40
    usable_h = dh - 80

    # 保持 REF_WIDTH/REF_HEIGHT = 600/900 = 2:3 比例
    ratio = REF_WIDTH / REF_HEIGHT

    # 高度受限
    h_by_height = usable_h
    w_by_height = int(h_by_height * ratio)

    if w_by_height <= usable_w:
        return max(w_by_height, 400), max(h_by_height, 600)
    else:
        # 宽度受限
        w_by_width = usable_w
        h_by_width = int(w_by_width / ratio)
        return max(w_by_width, 400), max(h_by_width, 600)


def _set_fullscreen(screen, fullscreen):
    """切换全屏并返回新 screen surface。"""
    if fullscreen:
        desktops = globals().get("_DESKTOP")
        if desktops:
            dw, dh = desktops
        else:
            info = pygame.display.Info()
            dw, dh = info.current_w, info.current_h
        s = pygame.display.set_mode(
            (dw, dh),
            pygame.FULLSCREEN | pygame.SCALED, vsync=1,
        )
    else:
        safe_w, safe_h = _get_safe_window_size()
        s = pygame.display.set_mode(
            (safe_w, safe_h), pygame.RESIZABLE, vsync=1,
        )
    _load_icon()  # set_mode 会重置图标
    pygame.display.set_caption("合成大YK — Big Alloy Merge")
    return s


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
        rst_x = cell_x + (get_max_drop() + 1) * (cell_w + si(4)) + si(8)
        rst_w = si(36)
        if rst_x <= mx <= rst_x + rst_w:
            game.debug_weights = None  # 恢复默认
            return True
        return True  # 点击在权重栏内

    return False


def _handle_sound_click(mx, my, screen) -> bool:
    """v2.2.0.0: 检查是否点击了声音开关按钮。返回 True 表示已处理。"""
    w = screen.get_width()
    btn_sz = si(36)
    bx = w - btn_sz - si(10)
    by = si(30)
    if bx <= mx <= bx + btn_sz and by <= my <= by + btn_sz:
        from game import toggle_sound
        toggle_sound()
        return True
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


def _show_update_notification(renderer, screen, latest_version, download_url):
    """v2.2.2.4: 闪屏后在模式选择界面弹更新通知。
    显示新版本号 + 下载提示，8秒自动关闭或点击关闭。
    """
    import pygame
    font = renderer._font(si(18))
    small_font = renderer._font(si(13))
    start_time = pygame.time.get_ticks()
    timeout_ms = 8000

    while True:
        elapsed = pygame.time.get_ticks() - start_time
        if elapsed > timeout_ms:
            return

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                return  # 任意按键或点击关闭

        # 渲染通知覆盖层
        w, h = screen.get_size()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        nw, nh = si(360), si(160)
        nx, ny = (w - nw) // 2, (h - nh) // 2
        dlg = pygame.Surface((nw, nh), pygame.SRCALPHA)
        dlg.fill((30, 35, 50, 245))
        pygame.draw.rect(dlg, (100, 160, 255, 220),
                         dlg.get_rect(), width=si(2), border_radius=si(8))
        screen.blit(dlg, (nx, ny))

        # 标题
        title = font.render("🔄 发现新版本!", True, (255, 200, 100))
        screen.blit(title, (nx + si(20), ny + si(16)))

        # 版本号
        ver_text = font.render(f"最新版本: {latest_version}", True, (255, 255, 255))
        screen.blit(ver_text, (nx + si(20), ny + si(54)))

        # 下载提示
        hint = small_font.render("请前往 GitHub Releases 下载更新", True, (180, 200, 220))
        screen.blit(hint, (nx + si(20), ny + si(86)))

        # 关闭提示
        close = small_font.render("点击任意位置关闭 · 8秒后自动消失", True, (140, 140, 160))
        screen.blit(close, (nx + si(20), ny + si(118)))

        pygame.display.flip()
        pygame.time.wait(30)


def _create_new_mode_dialog(renderer, screen, mgr):
    """简易新建模式对话框：输入名称，从 lite 复制创建。"""
    import pygame
    name = ""
    font = renderer._font(si(18))
    small_font = renderer._font(si(13))
    while True:
        w, h = screen.get_size()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                if event.key == pygame.K_RETURN:
                    if name.strip():
                        mgr.create(name.strip(), "lite")
                        return
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif event.unicode and len(name) < 20:
                    name += event.unicode
        # 渲染对话框
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        dw, dh = si(340), si(120)
        dx, dy = (w - dw) // 2, (h - dh) // 2
        dlg = pygame.Surface((dw, dh), pygame.SRCALPHA)
        dlg.fill((40, 42, 60, 240))
        pygame.draw.rect(dlg, (80, 85, 120, 255), dlg.get_rect(), width=si(2), border_radius=si(6))
        screen.blit(dlg, (dx, dy))
        # 标题
        t = font.render("新建模式名称", True, (255, 255, 255))
        screen.blit(t, (dx + si(16), dy + si(12)))
        # 输入框
        display = name + "_" if name else "___"
        inp = font.render(display, True, (255, 215, 90))
        screen.blit(inp, (dx + si(20), dy + si(48)))
        # 提示
        hint = small_font.render("输入名称后回车确认 · ESC取消", True, (140, 140, 160))
        screen.blit(hint, (dx + si(16), dy + si(82)))
        pygame.display.flip()
        pygame.time.wait(30)


if __name__ == "__main__":
    main()
