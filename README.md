# 合成大YK (Big Alloy Merge)

[![GitHub](https://img.shields.io/badge/GitHub-big--alloy--merge-blue)](https://github.com/wanchengyang2010/big-alloy-merge/)

Suika 风格物理合成游戏 —— pygame-ce + Python 开发，触屏友好，daxigua 比例精确复刻。

## 鸣谢

物理参数与容器比例参考 **[yieio/daxigua](https://github.com/yieio/daxigua)**，感谢原作者的开源贡献。

## 快速开始

```bash
pip install pygame-ce
python main.py
```

**要求**：Python 3.14+ | pygame-ce 2.5.7+ | Windows 10/11（触屏可用）

## 玩法

同等级球碰撞合成 → 升级为下一级球。球堆叠超过红色虚线 → 游戏结束。

| 操作 | 方式 |
|------|------|
| 预览 | 鼠标悬停 |
| 掉落 | **容器内按住拖动，松手掉落**（触屏适配） |
| 重来 | R 键 或 🔄 按钮 |
| 全屏 | F11 或 ⬜ 按钮 |
| 退出 | ESC 或 ❌ 按钮 |

## 模式

| 模式 | 按键 | 元素 | 说明 |
|------|------|------|------|
| 大西瓜 | **B** | 11 | 主力模式，daxigua 物理复刻 |
| 调试 | **C** | 11 | 密码 `3919`，可调球/权重/参数 |
| 演示 | **D** | 11 | AI 自动游玩 |
| 2222 | A | 17 | 🔒 待开发 |

## 元素表

| 等级 | 名称 | 分数 |
|------|------|------|
| 0 | 家畜 🐱 | 28 |
| 1 | 猴子 🐒 | 36 |
| 2 | 考拉 🐨 | 45 |
| 3 | 疯狗 🐕 | 55 |
| 4 | 阳阳 🐏 | 66 |
| 5 | 马恕 🐎 | 78 |
| 6 | 雪豹 🏐 | 91 |
| 7 | 恐龙 🦖 | 105 |
| 8 | 狒狒 🙉 | 120 |
| 9 | 锐哥 🦌 | 136 |
| 10 | 钇钾 🪙 | 200 |

## 项目结构

```
├── main.py          # 入口、主循环、闪屏、拖动交互
├── game.py          # 状态管理、合成、计分、超线检测
├── physics.py       # 碰撞/重力/磁力、空间哈希网格
├── renderer.py      # 渲染：容器、球、UI、特效、调试面板
├── constants.py     # 缩放系统、双套物理参数
├── data.py          # 17+11 元素定义
├── item.py          # Item 数据类
├── autoplay.py      # AI bot + 批量模拟测试
├── tune_sweep.py    # 参数扫描调优
├── updater.py       # 异步 HTTP 更新检查
├── assets/
│   ├── yk.png       # 启动闪屏背景
│   └── images/      # 球图片 0.png~16.png (512×512)
└── Messages.txt     # 合成自定义消息
```

## 构建 exe

```bash
pip install pyinstaller
python -m PyInstaller --onefile --windowed --name "合成大YK" \
  --add-data "assets/yk.png;assets" \
  --add-data "assets/images;assets/images" \
  --add-data "icon.ico;." \
  --add-data "highscore.txt;." \
  --add-data "Messages.txt;." \
  --add-data "elements.txt;." \
  --version-file "version_info.txt" \
  --icon=icon.ico \
  main.py
```

输出 `dist/合成大YK.exe`（约 28MB），可独立拷到任何 Win10/11 触屏电脑运行。

## 版本发布

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.1.1 | 2026-06 | 自适应初始窗口，小屏电脑顶部按钮不再被裁切 |
| v1.0.1.0 | 2026-06 | 修复合成消息映射(代码层offset)，Messages.txt保留17条完整 |

发布文件夹：`releases/Big_Alloy_Merge_v_X_X_X_X/`

## 技术点

- 参考分辨率 600×900，窗口等比缩放
- 模块级常量访问（`import constants` + `constants.GRAVITY`）支持运行时覆写
- 超线检测用位置变化量（非速度），避免重力干扰
- 同等级球碰撞分离跳过 → 重叠合成
- 字体走系统路径（中文 Win10/11 自带微软雅黑）

## 版权

© 2026 Trash Panda Q Opal

## 肖像权声明

本游戏角色图片可能包含基于真实人物形象创作的内容。**如有侵犯您的肖像权或其他合法权益，请通过 GitHub Issues 联系我们，我们将在核实后第一时间删除。**
