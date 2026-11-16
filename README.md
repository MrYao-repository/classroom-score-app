<div align="center">

# 课堂积分系统 Pro

**一款为课堂即时反馈设计的桌面积分板 —— 6 人卡片、一键加减分、自动存档、深浅双主题**

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?logo=windows&logoColor=white)](#兼容性)
[![UI](https://img.shields.io/badge/UI-customtkinter-1F6FEB)](https://github.com/TomSchimansky/CustomTkinter)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/MrYao-repository/classroom-score-app/ci.yml?label=CI)](../../actions)
[![Release](https://img.shields.io/github/v/release/MrYao-repository/classroom-score-app?label=release)](../../releases)

</div>

---

## 简介

**课堂积分系统 Pro** 是一个单文件运行的 Windows 桌面小程序，面向中小学课堂的即时评价场景。老师上课时打开它，六个学生卡片一字排开，点名、加分、扣分、抽人、排名、导出，一步到位。

它不联网、不依赖数据库、不需要安装服务端：所有状态存在同目录一个 `student_data.json` 里，关掉再开自动续分。素材全部为本地 PNG，界面用 `customtkinter` 绘制，支持深浅双主题与高分屏。

## 界面预览

| 浅色主题 | 深色主题 |
| :---: | :---: |
| ![浅色主题](screenshots/main-light.png) | ![深色主题](screenshots/main-dark.png) |

左侧是 3×2 的学生卡片区，右侧是「加分分值 / 课堂工具 / 抽选展示 / 操作记录」四段式侧栏，顶部是自绘标题栏（主题、置顶、全清、迷你、最小化、关闭）。

## 功能特性

| 分类 | 功能 | 说明 |
| :--- | :--- | :--- |
| 计分 | **一键加分** | 卡片中央大按钮按当前分值加分，默认 `+1`，侧栏可切 `+1 / +2 / +5` |
| 计分 | **扣分与单人清零** | 每张卡片下方 `－1` 与「清零」，只影响该学生 |
| 计分 | **全局清零** | 顶部「全清」把所有分数归零，二次确认后执行 |
| 计分 | **撤销 / 重做** | 双栈实现，加减分、清零、改名等操作均可回退与重放 |
| 交互 | **双击改名** | 双击卡片上的姓名即可弹出输入框改名，实时写入存档 |
| 交互 | **分数反馈动画** | 加分时分数闪色 + 上浮 `+N` 气泡；不改字号，避免整卡抖动 |
| 课堂工具 | **随机点名** | 点名区高速滚动所有姓名，点「停止抽选」定人并显示头像 |
| 课堂工具 | **积分排行榜** | 独立窗口按分数降序排列，前三名用 🥇🥈🥉 标记 |
| 课堂工具 | **导出积分表** | 生成 `课堂积分表_YYYYMMDD_HHMMSS.csv`，UTF-8 with BOM，Excel 直接双击不乱码 |
| 表现力 | **里程碑庆祝** | 某学生分数每跨过 10 分整数节点，随机弹出奖牌/星星/奖杯/点赞贴纸 |
| 表现力 | **深浅双主题** | 一键切换，配色、背景图、按钮样式整体联动，选择持久化 |
| 窗口 | **窗口置顶** | 上课时压在其他窗口之上，状态持久化 |
| 窗口 | **迷你悬浮窗** | 收成 2×3 的小卡，只保留每行加分按钮，适合边讲边点 |
| 窗口 | **最小化收纳** | 最小化后缩成屏幕右下角一个浮动小按钮，点击还原 |
| 窗口 | **自绘标题栏** | 隐藏系统白条，自定义拖动区与最小化/关闭按钮，深色下不突兀 |
| 适配 | **启动分辨率自适应** | 按屏幕尺寸一次性计算窗口宽高并居中，主窗与迷你窗都会夹在屏幕边界内 |
| 适配 | **高 DPI 清晰渲染** | 启动时声明 DPI 感知，高分屏下文字与图标不发虚 |
| 记录 | **操作日志** | 右下角滚动记录「谁加了几分、谁被抽中、何时导出」，底部状态栏同步提示 |

## 环境要求

| 项目 | 要求 |
| :--- | :--- |
| 操作系统 | Windows 10（1809 及以上）或 Windows 11，64 位 |
| Python | 3.8 及以上（开发与实测版本为 3.15） |
| 分辨率 | 1280×720 及以上（窗口会按屏宽 90%、屏高 92% 自适应，宽高夹在 1260–1340 × 720–900 之间） |
| 显示缩放 | 100%–200% 均可，程序启动时自动适配 |
| 依赖库 | `customtkinter`、`Pillow` |

## 快速开始

### 1. 获取代码

```bash
git clone https://github.com/MrYao-repository/classroom-score-app.git
cd classroom-score-app
```

也可以直接在仓库页面点 `Code → Download ZIP` 解压。

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

`requirements.txt` 内容：

```text
customtkinter>=5.2.0
Pillow>=9.0.0
```

### 3. 运行

```bash
python 课堂积分系统.py
```

首次运行会自动生成 `student_data.json`（6 位「学生1」到「学生6」，分数全 0），双击卡片姓名即可改成真实名单。

> 直接双击 `.py` 文件通常只会被编辑器打开而不是运行。请用上面的命令，或使用打包好的 exe。

## 使用说明

| 操作 | 位置 | 效果 |
| :--- | :--- | :--- |
| 加分 | 卡片中央 `＋ N 分` | 按当前分值加分，触发闪色与气泡 |
| 扣分 | 卡片下方 `－1` | 该学生减 1 分，不会低于 0 |
| 单人清零 | 卡片下方「清零」 | 仅该学生归零 |
| 改分值 | 右侧「加分分值」的 `+1 / +2 / +5` | 切换加分步长，立即生效并持久化 |
| 改名 | 双击卡片上的姓名 | 弹出输入框，重名会被拒绝 |
| 随机点名 | 右侧「随机点名」 | 开始滚动，按钮变为「停止抽选」，再点一次定人 |
| 撤销 / 重做 | 右侧对应按钮 | 回退或重放最近一次计分类操作 |
| 排行榜 | 右侧「积分排行榜」 | 弹出降序榜单，前三名带奖牌 |
| 导出 | 右侧「导出积分表」 | 在程序目录生成带时间戳的 CSV 并提示路径 |
| 主题 | 顶部「主题」 | 浅色 ⇄ 深色，选择会记住 |
| 置顶 | 顶部「置顶」 | 窗口压在最上层，按钮文字变为「已置顶」 |
| 全清 | 顶部「全清」 | 所有分数归零 |
| 迷你 | 顶部「迷你」 | 进入 2×3 悬浮小卡，点「恢复」回主窗 |
| 拖动 | 顶部标题栏空白处 | 自定义拖动，无系统标题栏 |
| 最小化 / 关闭 | 顶部右侧两个圆钮 | 最小化收纳为浮动按钮 / 保存后退出 |

## 数据存档

程序把全部状态写在**运行目录下的 `student_data.json`**，每次计分、改名、切主题、开关置顶都会立即落盘。

```json
{
  "theme": "light",
  "always_on_top": false,
  "point_value": 1,
  "students": {
    "学生1": 0,
    "学生2": 0,
    "学生3": 0,
    "学生4": 0,
    "学生5": 0,
    "学生6": 0
  }
}
```

| 字段 | 类型 | 含义 |
| :--- | :--- | :--- |
| `theme` | string | `light` 或 `dark` |
| `always_on_top` | bool | 窗口是否置顶 |
| `point_value` | number | 加分步长，`1` / `2` / `5` |
| `students` | object | 姓名 → 积分，键的顺序即卡片顺序 |

> 文件损坏或缺失时会自动回退到默认 6 人名单，不会崩溃。想重置课堂，直接删掉该文件重启即可。

## 打包成 EXE

用 PyInstaller 打单文件，素材随包内嵌，拷给别人无需装 Python：

```bash
pip install pyinstaller
pyinstaller -F -w -n "课堂积分系统" --add-data "assets_proc;assets_proc" "课堂积分系统.py"
```

产物在 `dist\课堂积分系统.exe`（约 18 MB）。打包后程序通过 `sys._MEIPASS` 找到内嵌素材，而存档仍写在 **exe 同级目录**，所以升级 exe 不会丢分。

## 项目结构

```text
classroom-score-app/
├── 课堂积分系统.py              # 主程序，单文件实现全部逻辑
├── assets_proc/                # 全部视觉素材
│   ├── avatars/                # 6 张学生头像  student-01 ~ student-06
│   ├── bg/                     # 2 张背景     bg-light / bg-dark
│   ├── icons/                  # 10 枚按钮图标
│   └── stickers/               # 4 张庆祝贴纸  medal / star / thumb / trophy-big
├── screenshots/                # README 用界面截图
├── requirements.txt
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── LICENSE
└── .github/workflows/ci.yml    # 提交时自动做语法检查
```

## 兼容性

| 系统 / 场景 | 状态 | 备注 |
| :--- | :---: | :--- |
| Windows 11 24H2 | ✅ 已验证 | 深浅主题、迷你窗、导出均正常 |
| Windows 10 22H2 | ✅ 已验证 | 同上 |
| 3200×2000 / 200% 缩放 | ✅ 已验证 | 主窗夹到 1340×900 并居中 |
| 1920×1080 / 100% 缩放 | ✅ 支持 | 主窗约 1340×900，迷你窗贴合右下角 |
| macOS / Linux | ⚠️ 未测试 | 代码无平台绑定，但字体与 DPI 适配按 Windows 调优 |
| 多人班级 / 超过 6 人 | ⚠️ 受限 | 卡片区按 3 列 × 2 行布局，人数更多需要改 `build_cards` 的网格配置 |

## 下载

不想装 Python 的话，直接到 [Releases](../../releases) 下载最新的：

| 文件 | 平台 | 说明 |
| :--- | :--- | :--- |
| [`ClassroomScoreBoard-v1.0.0.exe`](../../releases/download/v1.0.0/ClassroomScoreBoard-v1.0.0.exe) | Windows 10 / 11 64 位 | 18.56 MB，双击即用，无需 Python |

> 首次运行会在 exe 同级目录生成 `student_data.json`。请把它放在可写目录（桌面、文档、D 盘均可），不要放进 `Program Files`；升级版本时保留该文件即可续分。

## 常见问题

<details>
<summary><b>双击 .py 没反应，直接打开了编辑器？</b></summary>

Windows 默认把 `.py` 关联到编辑器。请在终端执行 `python 课堂积分系统.py`，或改用 Release 里的 exe。
</details>

<details>
<summary><b>分数重启后没了？</b></summary>

存档是运行目录下的 `student_data.json`。打包成 exe 后请把它和 exe 放在同一个文件夹，别单独挪走 exe；也别把这个文件放进只读目录。
</details>

<details>
<summary><b>高分屏字发虚？</b></summary>

程序启动时会声明 DPI 感知。若仍觉得糊，检查系统「显示 → 缩放」是否为非整数倍（如 125%），可临时切到 100% 或 150% 对比。
</details>

<details>
<summary><b>想加学生、改人数？</b></summary>

双击姓名改名即可。加人需要编辑 `student_data.json` 的 `students` 里新增键值，同时调整 `build_cards` 中 `range` 的列行配置，否则卡片会挤在 3×2 网格外。
</details>

<details>
<summary><b>导出的 CSV 里中文乱码？</b></summary>

导出使用 `utf-8-sig`，Excel 双击应正常。若用记事本打开看到乱码，是编码识别问题，改用 Excel 或 VS Code 打开。
</details>

## 参与贡献

欢迎 Issue 与 PR。提交前请先读 [CONTRIBUTING.md](CONTRIBUTING.md)，安全相关问题请按 [SECURITY.md](SECURITY.md) 私下反馈，不要在公开 Issue 里贴敏感信息。

## 许可证

本项目基于 [MIT License](LICENSE) 发布，可自由用于教学、修改与二次分发，保留版权声明即可。

## English

**Classroom Score Board Pro** is a single-file Windows desktop app for real-time classroom assessment. Six student cards, one-click plus/minus scoring, undo/redo, random student picker, live leaderboard, CSV export, light/dark themes, always-on-top, a mini floating panel, and automatic persistence to a local `student_data.json`.

```bash
pip install -r requirements.txt
python 课堂积分系统.py
```

Built with Python + [`customtkinter`](https://github.com/TomSchimansky/CustomTkinter) + Pillow. Licensed under MIT. Prebuilt `.exe` is available under [Releases](../../releases).

---

<div align="center">
<sub>为每一节课的即时反馈而生 · Built for classroom feedback</sub>
</div>
