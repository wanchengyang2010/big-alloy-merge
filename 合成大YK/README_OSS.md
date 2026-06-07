# 合成大YK (Big Alloy Merge)

Suika 风格物理合成游戏。基于 pygame-ce + Python 开发。

## 鸣谢

本游戏物理参数与容器比例参考 [yieio/daxigua](https://github.com/yieio/daxigua)，感谢原作者的开源贡献。

## 版权

Copyright (c) 2026 Trash Panda Q Opal。保留所有权利。

## 肖像权声明

本游戏中使用的角色图片可能包含基于真实人物形象创作的内容。我们已尽力确保所有素材的使用符合相关法律法规。

**如有侵犯您的肖像权或其他合法权益，请立即联系我们，我们将在核实后第一时间删除相关内容。**

联系方式：通过 GitHub Issues 提交删除请求。

## 运行

```bash
pip install pygame-ce
python main.py
```

## 操作

| 操作 | 方式 |
|------|------|
| 启动闪屏 | 自动显示，点击或4秒后进入模式选择 |
| 模式选择 | b=大西瓜 / c=调试(需密码3919) / d=演示(AI) |
| 移动预览 | 鼠标悬停预览；容器内按住拖动松手掉落（触屏） |
| 全屏切换 | F11 或 ⬜全屏按钮 |
| 重新开始 | R 或 🔄重来按钮 |
| 退出 | ESC 或 ❌退出按钮 |

## 游戏模式

| 模式 | 按键 | 元素数 | 说明 |
|------|------|--------|------|
| 2222 模式 | a | 17 | 🔒 待开发 |
| 大西瓜模式 | b | 11 | 当前唯一可用 |
| 调试模式 | c | 11 | 需密码 3919 |
| 演示模式 | d | 11 | AI 自动游玩 |

## 元素表（11元素 — 大西瓜模式）

| 编号 | 名称 | 半径 | 掉落 | 分数 |
|------|------|------|------|------|
| 0 | 家畜 🐱 | 18 | ✓ | 28 |
| 1 | 猴子 🐒 | 28 | ✓ | 36 |
| 2 | 考拉 🐨 | 38 | ✓ | 45 |
| 3 | 疯狗 🐕 | 42 | ✓ | 55 |
| 4 | 阳阳 🐏 | 54 | ✓ | 66 |
| 5 | 马恕 🐎 | 64 | 合成 | 78 |
| 6 | 雪豹 🏐 | 68 | 合成 | 91 |
| 7 | 恐龙 🦖 | 91 | 合成 | 105 |
| 8 | 狒狒 🙉 | 108 | 合成 | 120 |
| 9 | 锐哥 🦌 | 108 | 合成 | 136 |
| 10 | 钇钾 🪙 | 144 | 合成(最终) | 200 |

## 项目结构

```
合成大YK/
├── main.py           # 入口，主循环，闪屏，模式选择，拖动交互
├── constants.py      # 常量：缩放系统，物理参数，按钮定义
├── data.py           # 元素定义（17+11）
├── version.py        # 版本号
├── item.py           # Item 类
├── game.py           # Game 类：物理覆写，合成，计分，超线检测
├── physics.py        # 碰撞检测/分离，重力，磁力，空间网格
├── renderer.py       # 渲染：闪屏，容器，球，按钮，调试面板，特效
├── updater.py        # 异步 HTTP 检查更新
├── autoplay.py       # AI bot（SmartBot/DumbBot/DemoBot）+ 批量模拟
├── tune_sweep.py     # 参数扫描调优
├── elements.txt      # 元素名称
├── Messages.txt      # 合成自定义消息
├── icon.ico          # 窗口图标
├── version_info.txt  # Windows 版本信息（PyInstaller）
├── yk.png            # 启动闪屏背景
├── assets/
│   └── images/       # 球图片 0.png~16.png (512×512 PNG RGBA)
└── README_OSS.md     # 本文件
```

## 技术栈

- Python 3.14+
- pygame-ce 2.5.7
- 物理引擎：纯 Python（重力、碰撞分离、磁力吸引、空间哈希网格）
- 缩放系统：参考分辨率 600×900，自适应窗口大小

## 构建

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

## 版本

当前版本：v1.0.1.0

版本格式：`v<major>.<minor>.<patch>.<build>`
- major (+1.0.0.0)：用户明确要求
- minor (+0.1.0.0)：大功能更新
- patch (+0.0.1.0)：小功能增补
- build (+0.0.0.1)：小 bug 修复

## 发布者

Trash Panda Q Opal

---

**⚠️ 肖像权声明：如有侵犯肖像权，请联系删除。**
