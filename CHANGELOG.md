# 合成大YK 更新日志

> 版本格式 `v<major>.<minor>.<patch>.<build>`，详见 `version.py`

---

## v2.3.0.0 (2026-06-22)

### 🌊 长风破浪版 — 元素重组 + 动态掉落 + 物理优化 + UI 增强 + 安装器

- 🕴️ **西西替换嘟嘟**（tier 0）：新图片 + 合成提示 "xiiiiii"，音效沿用嘟嘟的 doo-doo
- ♾️ **春宇插入锐哥前**（tier 14）：新图片 + 合成提示 "闭嘴吧啊"，音效用雪豹的 snowball
- 🗑️ **删除雪豹**：恐龙→12、狒狒→13，后继元素顺移，平移元素音效/图片/消息均不变
- ⚡ **动态掉落系统**（full 模式）：合成 8 级解锁掉落 6 级、10 级解锁前 8 级，通用 N→N-2
- 📊 **掉落限频**：N-3 级每 5 球限 1 次、N-2 级每 8 球限 1 次，参数可自定义（constants.py）
- 🚀 **帧率翻倍**：FPS 120→480，所有窗口添加 vsync 防撕裂
- 🔄 **旋转减速**：ANGULAR_DAMPING 0.98→0.92，碰撞扭矩 2.0→1.0，壁耦合 0.03→0.015
- 📝 **掉落信息显示**：预览球上方显示 "{tier} {name}" + 合成提示消息
- 💿 **NSIS 安装器**：含全部资源（图片+音效+背景音乐）+ Python 源码，可选调试密码预授权
- 🔑 **用户数据迁移 %APPDATA%**：可写文件（存档/配置/最高分）不再需要管理员权限
- 🖼️ **图标+闪屏更新**：newicon.ico 窗口图标 + newflash.jfif 启动闪屏
- 🔧 **修复 _dynamic_drop 初始化顺序**：避免 AttributeError 崩溃

**修改文件：**
- `version.py`：v2.3.0.0 "长风破浪版"
- `constants.py`：FPS=480、vsync、ANGULAR_DAMPING=0.92、WALL_TORQUE_COUPLING=0.015、动态掉落参数、get_user_data_dir()
- `data.py`：TIERS_FULL/LITE 元素重组 + TIER_MERGE_SOUNDS 随元素平移 + %APPDATA% 持久化
- `modes.py`：DEFAULT_TIERS_FULL/LITE 同步 + ModeDefinition dynamic_drop_enabled + %APPDATA% 路径
- `game.py`：动态掉落系统 + %APPDATA% 用户数据 + 音效资源路径多源查找
- `physics.py`：碰撞扭矩乘数 2.0→1.0
- `renderer.py`：掉落预览球名称提示 + 闪屏 newflash.jfif
- `main.py`：vsync=1 全窗口 + _check_installer_debug_key() 安装器调试预授权
- `elements.txt` + `Messages.txt`：重写
- `assets/images/`：0.png(西西新图)、12.png(恐龙)、13.png(狒狒)、14.png(春宇新图)
- `installer.nsi`：NSIS 安装器脚本（含资源+源码）

**发布文件：**
- `Big_Alloy_Merge.exe` — 绿色免安装版
- `Big_Alloy_Merge_Setup.exe` — NSIS 安装包（桌面+开始菜单快捷，含源码+资源，可选调试密码）
- `Big_Alloy_Merge_Source.zip` — 纯 Python 源码

---

## v2.2.2.5 (2026-06-18)

### 🐛 死循环修复 + ⚡ 即时合成补全 + 🔄 GitHub 更新通知 + ⌨️ 快捷键补全

- 🐛 **修复 `_check_merges` 死循环**：误置的 `break` 导致 while 循环永不退出，游戏启动即卡死
- ⚡ **即时合成全面生效**：`circles_near()` 函数 + `circles_near` 调用正确集成到 `_check_merges`
- 🔄 **GitHub 更新通知线程安全**：后台检查 → 主线程渲染通知对话框，避免 pygame 线程冲突
- ⌨️ **补全 `a` 键快捷进入完整模式**
- 🔧 **物理主循环优化**：wall_clamp 移到碰撞后统一调用，`_resolve_collisions` 去冗余
- 📐 **`COLLISION_PASSES` 10→4**：碰撞迭代减60%

**修改文件：**
- `game.py`：`_check_merges` 死循环修复 + `circles_near` 集成 + `_resolve_collisions` 去冗余
- `physics.py`：新增 `circles_near()` 即时合成检测函数
- `constants.py`：`COLLISION_PASSES=4`，新增 `MERGE_TOLERANCE=3.0`
- `main.py`：GitHub 更新通知 + `a` 键快捷 + 线程安全修复
- `version.py`：v2.2.2.5
- `modes.py`：`_CURRENT_VERSION` v2.2.2.5

---

## v2.2.2.4 (2026-06-16) — ⚠️ 报废版本（_check_merges 死循环）

### 🔧 物理流畅 + ⚡ 即时合成 + 🔄 GitHub 自动更新

- 🔧 **壁摩擦彻底修复（分壁正压力 + 比例衰减）**：
  - 侧壁正压力 = m·g·0.03（3%自重），底壁正压力 = m·g·0.12（12%自重）
  - 比例摩擦：每帧最多减速 30%，绝不刹停（移除一刀切归零）
  - 壁摩擦系数 0.08→0.05
- ⚡ **即时合成（容错间距 3px）**：
  - 新增 `circles_near()` — 两球距离 ≤ 半径和+3px 即触发合成
  - `_check_merges()` 改用 `circles_near`，同等级靠近即合成
  - 链式反应保持（while True 迭代 + merge_cooldown=0）
- 🚀 **帧率优化**：
  - `COLLISION_PASSES` 10→4（碰撞迭代减60%）
  - `_resolve_collisions` 移除冗余 wall_clamp（主循环已调）
- 📐 **完整模式容器宽 550→540**
- 🔄 **GitHub Releases 自动更新**：
  - `updater.py` 新增 `check_github_update()` — 查 GitHub API `/releases/latest`
  - 解析 `tag_name` 比版本，找 Setup.exe 下载链接
  - 闪屏后弹更新通知（8秒超时或点击关闭）
- 🪟 **安装脚本版本同步**：installer.nsi + build_installer.py → v2.2.2.4

**修改文件：**
- `physics.py`：`wall_clamp()` 分壁正压力+比例摩擦；新增 `circles_near()`
- `constants.py`：FRICTION_WALL 0.05, COLLISION_PASSES 4, MERGE_TOLERANCE 3.0
- `game.py`：`_check_merges` 用 `circles_near`；`_resolve_collisions` 去冗余
- `modes.py`：full `container_width` 540, `_CURRENT_VERSION` v2.2.2.4
- `updater.py`：新增 `check_github_update()` GitHub API 适配
- `main.py`：闪屏后更新通知 `_show_update_notification()`
- `version.py`：v2.2.2.4
- `installer.nsi`：版本号同步
- `build_installer.py`：版本号同步

---

## v2.2.2.3 (2026-06-16)

### 🔧 物理引擎修复 + 🪟 正规 Windows 安装程序

- 🔧 **物理引擎修复（壁摩擦重写）**：
  - 壁碰撞不再归零法向速度 — 仅反弹压入方向（弹性 0.15），分离中不干预
  - 正压力统一用自重 `m·g`，不再用刚度公式（消除巨大虚拟正压力 → 粘壁根源）
  - 球间摩擦 0.95→0.20，壁摩擦 0.5→0.08（球不再粘滞）
  - 旋转阻尼 0.85→0.98，壁旋转摩擦 0.55→0.03（自然旋转保持）
  - 旋转扭矩耦合 0.08→0.03（壁面滑动 → 温柔自旋）
- 🪟 **正规 Windows 安装程序（NSIS）**：
  - 现代 GUI 安装向导（MUI2），全中文界面
  - 默认安装到 `%ProgramFiles%\合成大YK`，可选自定义目录
  - 自动创建桌面快捷方式 + 开始菜单程序组（含卸载入口）
  - 用户数据写入 `%LOCALAPPDATA%\合成大YK`（高分/存档/modes），无需管理员权限
  - 注册「添加/删除程序」— 系统设置中可卸载
  - 安装器嵌入版本号/发布者/图标元数据
  - 新增 `installer.nsi`（NSIS 脚本）、`build_installer.py`（一键构建）、`LICENSE.txt`（MIT）
- 📐 **版本号 v2.2.2.2 → v2.2.2.3**

**修改文件：**
- `physics.py`：`wall_clamp()` 完全重写（不再粘壁）
- `constants.py`：降低 FRICTION / FRICTION_WALL / ANGULAR_DAMPING / WALL_ROTATIONAL_FRICTION / WALL_TORQUE_COUPLING
- `modes.py`：更新所有模式工厂默认摩擦参数 + `_CURRENT_VERSION` 升级
- `version.py`：v2.2.2.3
- `installer.nsi`：**新文件** — NSIS MUI2 安装脚本
- `build_installer.py`：**新文件** — 安装包构建脚本
- `LICENSE.txt`：**新文件** — MIT 许可证

---

## v2.1.0.0 (2026-06-13)

### 🏠 返回主界面 + 分模式存档 + 轻量调试面板

- 🏠 **返回主界面按钮**：按钮栏新增「🏠菜单」，保存进度后返回模式选择
- 💾 **分模式独立存档**：`savegame_{mode_id}.json`，每个模式互不影响
  - `Game.list_saves()` 列出所有存档
  - `Game.load_save_state(mode_id)` 按模式加载
  - 模式选择界面 💾 标记有存档的模式
  - 旧版 `savegame.json` 自动兼容迁移
- 🎛️ **轻量调试模式也支持实时面板**：`debug` 模式（12元素）同样可用 F3 打开参数面板
- 📐 **完整模式参数调整**：容器宽 550、溢出线 179、摩擦 0.30
- 🔄 **外层循环**：`main()` 重构为「模式选择 → 游戏 → 菜单返回 → 模式选择」循环

---

## v2.0.4.1 (2026-06-13)

### 🐛 Bug 修复

- 🎛️ **调试面板渲染修复**：面板从 `main.py` 独立 flip 改为集成到 `renderer.draw()` 内（flip 之前渲染），解决面板不显示问题
- 🔧 **物理子步长**：`game.update()` 新增 `_compute_substeps()`，根据最小球半径动态计算子步数。完整模式 5 子步/帧（120fps），小球不再隧穿大球
- 📐 **颤抖减轻**：子步长使碰撞检测更频繁，球堆密集时大幅减少颤抖穿模

---

## v2.0.4.0 (2026-06-13)

### 🔓 完整模式解锁 + 游戏内实时参数调试面板

- 🔓 **完整模式（17元素）解锁**：物理参数对齐轻量模式（同难度），17 元素全链 0→16 可合成至钇钾
- 🛠️ **完整调试模式**：新建 `full_debug` 模式，密码 3919，17 元素 + 实时参数面板
- 🎛️ **游戏内实时参数调试面板**（`debug_panel.py`）：
  - 半透明右侧覆盖层，三标签页（数学模型 / 物理引擎 / 艺术框架）
  - 所有模式参数可实时 ± 调整，立即生效（`sync_mode_def_to_runtime()`）
  - Tier 级参数（半径/权重/质量/摩擦/弹性）逐球可调
  - 滚动支持 + 底部技术信息（FPS/球数/分数/模式）
  - F3 或 🐛 按钮切换面板可见性
  - 轻量调试模式（`debug`）保持不变，不受影响

**修改文件：**
- `modes.py`：`_make_full_mode()` 解锁 + lite 级物理，新增 `_make_full_debug_mode()`
- `game.py`：新增 `sync_mode_def_to_runtime()` + `_full_debug` 标志 + `debug_panel_open` 状态
- `debug_panel.py`：**新文件** — `DebugPanel` 类（渲染 + 点击 + 滚动 + 参数同步）
- `main.py`：`debug_panel` 集成（创建/点击/滚动/切换/密码流）
- `renderer.py`：完整调试模式跳过旧版调试栏
- `version.py`：v2.0.3.0 → v2.0.4.0

---

## v2.0.3.0 (2026-06-12)

### 🎵 胜利音乐 + 暂停控制

- 🔊 **胜利音乐**：合成终极球（钇钾）时播放 L'Internationale（`pygame.mixer.music` 流式播放）
- ⏯️ **音乐暂停按钮**：右上角 `ring.png` 图标按钮，可暂停/恢复音乐
- ⚙ **设置图标**：模式选择界面齿轮按钮改用 `settings.png` 图标

---

## v2.0.2.0 (2026-06-12)

### 🎯 12元素 + 统一编号 + 难度大幅提高

**球表重构（v2.0.2.0 核心改动）：**
- 轻量模式从 11 元素扩展到 **12 元素**（编号 5~16，与全模式统一）
- **新增 5 号球「灰鼠 🐁」**：r=18, pts=21, 图片 5.png
- **全体数学物理参数顺次平移**：
  - 5 号(灰鼠) ← 旧 6 号(家畜)参数
  - 6 号(家畜) ← 旧 7 号(猴子)参数
  - ...
  - 15 号(锐哥) ← 旧 16 号(钇钾)参数
- **16 号(钇钾) 全新扩大**：r=168（旧144）、pts=280（旧200）、mass=1680

**难度调整：**
| 参数 | v2.0.1.1 | v2.0.2.0 | 说明 |
|------|----------|----------|------|
| container_width | 460 | **480** | 略宽容纳更大球 |
| overflow_line_y | 130 | **135** | 溢线降低 |
| friction_wall | 0.5 | **0.5** | 保持 |
| n_tiers | 11 | **12** | 新增灰鼠 |
| max_drop | 4 | **5** | 6 种掉落 (灰鼠~阳阳) |

**调试模式入口恢复：**
- 新增内置「调试模式」卡片（密码 3919 进入）
- 使用新 12 元素参数，功能不变

**统一编号 5~16：** 轻量与全模式球编号不再差异，方便开发描述。

---

## v2.0.1.1 (2026-06-12)

### ⚖️ 游戏难度提升 + 新图标

**容器参数调整（轻量模式）：**
| 参数 | v2.0.1.0 | v2.0.1.1 | 说明 |
|------|----------|----------|------|
| container_width | 490 | **460** | 容器更窄，堆叠更难 |
| overflow_line_y | 145 | **130** | 溢出线更低，更易结束 |
| friction_wall | 0.3 | **0.5** | 壁摩擦加大 |
| wall_rotational_friction | 0.40 | **0.55** | 壁旋转摩擦同步加大 |

- 🎨 **新图标**：`newicon.ico` 替换应用图标

---

## v2.0.1.0 (2026-06-12)

### 🌀 旋转物理大修 + 新视觉资产

**旋转物理引擎修正（v2.0 旋转过于剧烈）：**
- 🔧 **dt无关角速度衰减**：`ω *= damping ** dt`，每秒保留 damping 比例，帧率无关
- 🧱 **壁面旋转摩擦**（新增 `wall_rotational_friction=0.40`）：球触壁时现有旋转被抑制40%
- 📐 **线速度→扭矩耦合大幅降低**：`WALL_TORQUE_COUPLING=0.08`（旧隐式1.0→降12.5倍）
- 触壁仅在线速度>1.0时产生微弱扭矩，避免高速掉落时疯狂旋转
- 低阈值0.001直接归零，消除微旋转残留

**新增 Mode 级物理参数：**
| 参数 | 默认 | 说明 |
|------|------|------|
| `angular_damping` | 0.85 | 每秒角速度保留系数（0.85=每秒衰减15%） |
| `wall_rotational_friction` | 0.40 | 壁面旋转摩擦（触壁时抑制现有旋转的比例） |

**视觉资产更新：**
- 🎨 **新图标**：`theme.ico` 替换为 `pictures/new.ico`
- 🖼️ **新背景**：`assets/theme.png` 替换为全新背景图

---

## v2.0.0.0 (2026-06-12)

### 🏗️ 全方位模式自定义化

三大理论框架深度集成：LambertLiuTheory(数学) + JaneFlyThought(物理) + BurningIsm(艺术)。

**模式系统：**
- `modes.json` 持久化所有模式参数，ModeManager 统一管理
- 内置模式：轻量(0) / 完整(1,🔒) / 演示(2)
- 无限自定义模式：从现有模式复制创建，独立参数集
- 拖动卡片排序，编号自动更新
- 齿轮⚙设置入口（P4 完整实现）

**LambertLiuTheory 数学模型：**
- 容器宽/高/溢出线、每球半径、掉落概率权重
- Tier数量 n、初始固定序列 c、最大掉落范围
- 所有尺寸参数以容器宽度为基准，等比例缩放

**JaneFlyThought 物理引擎 v2：**
- 🌀 **旋转物理**：碰撞切向摩擦→扭矩→角速度→旋转渲染
- 🧱 **壁摩擦** μ_w=0.3：触壁沿壁面减速+扭矩
- 每球独立质量/摩擦/弹性（可逐Tier覆盖）
- 角速度自然衰减（ANGULAR_DAMPING=0.98）

**BurningIsm 艺术框架：**
- 🖼️ **背景图**：theme.png + 上方45%暗色渐变遮罩
- 🔊 **音效系统**：合成音效 + 胜利音效（pygame.mixer）
- 📷 **图片处理**：`image_processor.py` — 任意图片→1024×1024 RGBA PNG
- 设界面对话框：浏览图片+自动规范化

**轻量模式调整：**
| 参数 | v1.1 | v2.0 | 说明 |
|------|------|------|------|
| container_width | 507 | **490** | 略窄 |
| overflow_line_y | 155 | **145** | 略低 |
| friction_wall | 0 | **0.3** | 壁摩擦 |
| background | 无 | **theme.png** | 背景图 |
| rotation | 无 | **开启** | 旋转 |

**迁移：**
- 旧 `q_custom.json` → 自动创建 "Q自我（已迁移）" 自定义模式
- 旧存档兼容（`mode` → `mode_id`）

---

## v1.1.0.2 (2026-06)

### 🐛 穿模重叠 + 抖动修复
- **穿模核心修复**：同等级球在冷却期内正常碰撞分离，不再穿透重叠
- 碰撞分离过度修正 20%（`overlap × 1.2`），确保完全分离
- `COLLISION_PASSES`: 5 → **10**，堆叠场景收敛更充分
- **睡眠机制**：球静止 0.3s 后深度休眠（速度归零），被碰撞唤醒
- 低速休眠阈值 0.5 → **2.0 px/帧**
- 触墙直接速度归零 + 累计睡眠
- **质量平衡**：`mass = r²` → `mass = r×10`，比例 1:64 → 1:8

---

## v1.1.0.1 (2026-06)

### 🚀 JaneFlyThought2 物理引擎（当前默认）

| 参数 | JFT1 (旧) | JFT2 (新) |
|------|-----------|-----------|
| 重力 | 900 | **1800** |
| 弹性 | 0.1 | **0.0 (刚性)** |
| 摩擦 | 1.0 (无) | **0.95 (球间接触)** |
| 初速 | 800 | **1600** |
| 冷却 | 0.5s | **0.25s** |
| 质量 | 无 | **mass = r²** |

- 真空环境（无空气阻力），重力独立加速
- 刚性碰撞（完全非弹性，沿法线粘合）
- 球间库伦接触摩擦（切向冲量，减少滑动）
- 边缘超限修复（每次碰撞迭代后墙约束）
- 120FPS + 低速休眠（<0.5px/帧归零，消除抖动）
- JFT1 模型保留向后兼容

### 🎨 Q自我模式
- 按 **q** 键进入，自定义球图/名称/合成提示词
- 配置持久化到 `q_custom.json`
- 自定义 PNG 放 exe 同目录，JSON 引用文件名
- 图片缺失自动降级为彩色圆圈

### 💾 自动恢复
- 退出时（❌/ESC/关窗）自动保存到 `savegame.json`
- 演示模式不保存，已合终极球不保存
- 下次启动模式选择顶部显示 💾 恢复卡片
- 按 **r** 或点击恢复，存档自动删除

### 🎉 合成终极球庆祝特效
- 合成钇钾 → 全屏 `theme.png` + 滚动文字 10 秒
- "你合成了大YK!" / "打倒YK反动统治!!!"
- 游戏不暂停，可继续操作

### 🔧 其他改进
- 闪屏：打开即显示 → 加载中 → 点击开始
- 窗口图标改为 `theme.ico`
- 物理文档 `PHYSICS.md` + 用户指南 `USER_GUIDE.md`
- 详细发布说明 `releases/RELEASE_v1.1.0.1.md`

---

## v1.0.1.1 (2026-06)
- 自适应初始窗口尺寸，小屏电脑顶部按钮不再被裁切
- GitHub Release 发布

## v1.0.1.0 (2026-06)
- 修复合成消息映射（代码层 offset）
- Messages.txt 保留 17 条完整
- GitHub Release 发布

## v1.0.0.2 (2026-06)
- 修复 lite 模式合成消息映射（Messages.txt 重编号 00-10）

## v1.0.0.1 (2026-06)
- 锁定全模式（待开发）
- 发布文件夹 `Big_Alloy_Merge_v_1_0_0_1`

## v1.0.0.0 (2026-06)
- 启动闪屏（yk.png）
- exe 元数据（Trash Panda Q Opal）
- 正式发布

## v0.5.1.0 (2026-06)
- 拖动松手掉落（触摸屏支持）
- 单球加载（冷却后生成）

## v0.5.0.2 (2026-06)
- 演示模式（AI 可视化）
- daxigua 容器/球/物理比例复刻

## v0.5.0.0 (2026-06)
- 模式选择界面
- 11 元素模式
- 合成消息
- 独立 exe

## v0.4.0.0
- 基础功能完成
