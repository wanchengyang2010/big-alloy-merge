"""v2.0.0.0 图片自动处理 — 任意图片 → 1024×1024 RGBA PNG。

用于设置界面中浏览选择图片后自动规范化。
纯 pygame 实现，无需 PIL 依赖。
"""

import os
import pygame


def process_ball_image(source_path: str, mode_id: str, tier_index: int,
                       target_dir: str | None = None) -> str | None:
    """处理任意图片为 1024×1024 RGBA PNG，保存到模式目录。

    Args:
        source_path: 源图片路径
        mode_id: 模式 ID（用作子目录名）
        tier_index: tier 编号（用于文件命名）
        target_dir: 目标目录（默认 modes/{mode_id}/）

    Returns:
        成功时返回文件名（如 "tier_0.png"），失败返回 None。
    """
    if target_dir is None:
        target_dir = os.path.join(os.getcwd(), "modes", mode_id)

    try:
        # 加载图片
        img = pygame.image.load(source_path)
    except Exception:
        return None

    # 转换为 RGBA
    if img.get_bytesize() < 4 or img.get_masks() is None:
        img = img.convert_alpha()
    else:
        img = img.convert_alpha()

    w, h = img.get_size()
    if w <= 0 or h <= 0:
        return None

    # 缩放到 1024×1024（保持比例，居中裁剪 → 正方形）
    target_size = 1024
    # 计算缩放比例（以较大边为准，确保覆盖）
    scale_factor = target_size / max(w, h)
    new_w = int(w * scale_factor)
    new_h = int(h * scale_factor)
    try:
        scaled = pygame.transform.smoothscale(img, (new_w, new_h))
    except Exception:
        scaled = pygame.transform.scale(img, (new_w, new_h))

    # 居中裁剪为正方形
    result = pygame.Surface((target_size, target_size), pygame.SRCALPHA)
    result.fill((0, 0, 0, 0))
    offset_x = (new_w - target_size) // 2
    offset_y = (new_h - target_size) // 2
    # 只复制重叠区域
    src_rect = pygame.Rect(
        max(0, -offset_x), max(0, -offset_y),
        target_size, target_size,
    )
    dst_rect = pygame.Rect(
        max(0, offset_x), max(0, offset_y),
        target_size, target_size,
    )
    # 确保 rect 有效
    src_rect.w = min(src_rect.w, new_w - src_rect.x)
    src_rect.h = min(src_rect.h, new_h - src_rect.y)
    dst_rect.w = src_rect.w
    dst_rect.h = src_rect.h

    try:
        result.blit(scaled, dst_rect, src_rect)
    except Exception:
        # 回退：直接缩放（可能拉伸但不会出错）
        result = pygame.transform.smoothscale(img, (target_size, target_size))

    # 保存
    os.makedirs(target_dir, exist_ok=True)
    filename = f"tier_{tier_index}.png"
    dest = os.path.join(target_dir, filename)
    pygame.image.save(result, dest)

    return filename
