# -*- coding: utf-8 -*-
"""
课堂积分系统 Pro —— 带卡通头像 / 图标 / 背景纹理 / 庆祝贴纸
运行前请确保已安装：customtkinter、Pillow
    pip install customtkinter pillow
数据自动保存到同目录 student_data.json，关闭再打开自动续分。
"""
import os
import sys
import json
import random
import csv
import time
from tkinter import messagebox

import customtkinter as ctk
from PIL import Image

# 高分屏 DPI 感知：进程启动时声明一次，主窗与迷你小窗的文字/图标都清晰不模糊
try:
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)      # Per-Monitor V2
    except Exception:
        ctypes.windll.user32.SetProcessDPIAware()            # 旧系统回退
except Exception:
    pass

# ===================== 资源路径（兼容打包 exe） =====================
def base_dir():
    """只读资源目录：开发时是脚本目录，打包后是 PyInstaller 临时解压目录。"""
    if getattr(sys, "_MEIPASS", None):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def app_dir():
    """可写数据目录：开发时是脚本目录，打包后是 exe 所在目录（持久保存数据）。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

RES = os.path.join(base_dir(), "assets_proc")

def asset(*parts):
    return os.path.join(RES, *parts)

# ===================== 双主题配色 =====================
THEME = {
    "light": {
        "bg_canvas": "#EDF1F7",
        "side_panel": "#EEF2F8",
        "card_bg": "#FFFFFF",
        "card_hover": "#F0F6FF",
        "card_border": "#E4EAF2",
        "text_main": "#1F2937",
        "text_gray": "#6B7280",
        "header_a": "#3B82F6",
        "header_b": "#60A5FA",
        "btn_add": "#F59E0B",
        "btn_add_hover": "#D97706",
        "btn_sub": "#FEE2E2",
        "btn_sub_hover": "#FECACA",
        "btn_sub_text": "#DC2626",
        "btn_clear": "#E5E7EB",
        "btn_clear_hover": "#D1D5DB",
        "btn_clear_text": "#4B5563",
        "side_btn": "#FFFFFF",
        "side_btn_hover": "#EFF6FF",
        "side_btn_text": "#1F2937",
        "section_title": "#1E40AF",
        "score_color": "#2563EB",
        "status_text": "#8A97A8",
        "log_bg": "#FFFFFF",
        "log_border": "#E5E7EB",
        "bg_img": "bg/bg-light.png",
    },
    "dark": {
        "bg_canvas": "#101A2E",
        "side_panel": "#1B2740",
        "card_bg": "#1E293B",
        "card_hover": "#2A3A55",
        "card_border": "#334155",
        "text_main": "#F1F5F9",
        "text_gray": "#94A3B8",
        "header_a": "#173A8F",
        "header_b": "#2563EB",
        "btn_add": "#F59E0B",
        "btn_add_hover": "#D97706",
        "btn_sub": "#3B2530",
        "btn_sub_hover": "#4E3040",
        "btn_sub_text": "#F87171",
        "btn_clear": "#2E3B52",
        "btn_clear_hover": "#3A4A66",
        "btn_clear_text": "#CBD5E1",
        "side_btn": "#263449",
        "side_btn_hover": "#30435F",
        "side_btn_text": "#E2E8F0",
        "section_title": "#93C5FD",
        "score_color": "#60A5FA",
        "status_text": "#7B8BA3",
        "log_bg": "#141F33",
        "log_border": "#334155",
        "bg_img": "bg/bg-dark.png",
    },
}

DATA_FILE = os.path.join(app_dir(), "student_data.json")

DEFAULT_DATA = {
    "theme": "light",
    "always_on_top": False,
    "point_value": 1,
    "students": {
        "学生1": 0, "学生2": 0, "学生3": 0,
        "学生4": 0, "学生5": 0, "学生6": 0,
    },
}

# ===================== 数据读写 =====================
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("存档根节点不是对象")
            for k, v in DEFAULT_DATA.items():
                data.setdefault(k, v if not isinstance(v, dict) else v.copy())
            if data["theme"] not in THEME:
                data["theme"] = DEFAULT_DATA["theme"]
            if data["point_value"] not in (1, 2, 5):
                data["point_value"] = DEFAULT_DATA["point_value"]
            if isinstance(data["students"], dict):
                data["students"] = {str(k): v for k, v in data["students"].items()
                                    if isinstance(v, (int, float))}
            else:
                data["students"] = {}
            if not data["students"]:
                data["students"] = DEFAULT_DATA["students"].copy()
            return data
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULT_DATA))

def save_data(data):
    """先写临时文件再原子替换，避免写入中断导致存档 JSON 损坏。"""
    tmp = DATA_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, DATA_FILE)
    except Exception:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass


# ===================== 主程序 =====================
class ScoreApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("课堂积分系统 Pro")
        # 打开时按当前屏幕分辨率一次性适配（不实时跟随）：限制在安全区间并居中
        sw0, sh0 = self.winfo_screenwidth(), self.winfo_screenheight()
        win_w = max(1260, min(1340, int(sw0 * 0.90)))
        win_h = max(720, min(900, int(sh0 * 0.92)))
        wx = max(0, (sw0 - win_w) // 2)
        wy = max(0, (sh0 - win_h) // 2 - 20)
        self.geometry(f"{win_w}x{win_h}+{wx}+{wy}")
        self.resizable(False, False)
        # 隐藏系统原生标题栏（顶部白色栏），改用自绘最小化/关闭按钮 + 自定义拖动
        self.overrideredirect(True)
        self.protocol("WM_DELETE_WINDOW", self.close_window)

        self.all_data = load_data()
        self.current_theme = self.all_data["theme"]
        self.scores = self.all_data["students"]
        self.point_value = self.all_data["point_value"]

        # 控件引用
        self.score_labels = {}
        self.card_frames = {}
        self.name_labels = {}
        self.unit_labels = {}
        self.add_btns = {}
        self.sub_btns = {}
        self.clear_btns = {}
        self.icon_imgs = {}
        self.avatar_imgs = {}
        # 姓名槽：回调捕获这个可变引用而非姓名字符串，改名时只需更新槽内容，
        # 已绑定到控件上的 lambda 便能自动拿到新姓名，避免闭包持有旧名崩溃。
        self.name_refs = {}

        # 撤销 / 重做 双栈
        self.undo_stack = []
        self.redo_stack = []

        self.is_rolling = False
        self.celebration_win = None
        self.milestone_fired = set()

        # 迷你悬浮窗
        self.mini_win = None
        self.mini_score_labels = {}
        # 最小化（收起）后的置顶恢复小按钮
        self.restore_float = None
        self._prev_topmost = False
        self._prev_geom = "1200x740"

        ctk.set_appearance_mode(self.current_theme)
        self.c = THEME[self.current_theme]
        self.attributes("-topmost", self.all_data["always_on_top"])

        self.build_ui()
        self.apply_theme()
        self.add_log("系统启动，历史数据已加载")

    # ---------- 图片加载 ----------
    def _load_image(self, *parts, size):
        """读取 PNG 并转 RGBA；素材缺失时回退为同尺寸透明图，避免整体崩溃。"""
        try:
            return Image.open(asset(*parts)).convert("RGBA")
        except Exception:
            return Image.new("RGBA", size, (0, 0, 0, 0))

    def ctk_icon(self, name, size=(26, 26)):
        key = (name, tuple(size))
        if key not in self.icon_imgs:
            im = self._load_image("icons", f"{name}.png", size=size)
            self.icon_imgs[key] = ctk.CTkImage(light_image=im, dark_image=im, size=size)
        return self.icon_imgs[key]

    def ctk_avatar(self, idx, size=(64, 64)):
        key = (idx, tuple(size))
        if key not in self.avatar_imgs:
            safe_idx = ((idx - 1) % 6) + 1  # 学生超过 6 人时循环复用头像
            im = self._load_image("avatars", f"student-{safe_idx:02d}.png", size=size)
            self.avatar_imgs[key] = ctk.CTkImage(light_image=im, dark_image=im, size=size)
        return self.avatar_imgs[key]

    # ---------- 界面搭建 ----------
    def build_ui(self):
        # 顶部标题栏（主窗口使用主题纯色背景，避免 tkinter 无法透明透出图片的问题）
        self.header = ctk.CTkFrame(self, height=82, corner_radius=0)
        self.header.pack(fill="x", side="top")
        self.header.pack_propagate(False)

        self.title_label = ctk.CTkLabel(
            self.header, text="课堂积分系统 Pro",
            font=("微软雅黑", 22, "bold"), text_color="white"
        )
        self.title_label.pack(side="left", padx=(30, 0))
        self.title_label.bind("<Button-1>", self._main_drag_start)
        self.title_label.bind("<B1-Motion>", self._main_drag_motion)

        # 右侧操作区：按钮自动排布，避免硬编码坐标在不同窗口宽度下错位
        header_right = ctk.CTkFrame(self.header, fg_color="transparent")
        header_right.pack(side="right", fill="y", padx=(0, 12))
        header_right.bind("<Button-1>", self._main_drag_start)
        header_right.bind("<B1-Motion>", self._main_drag_motion)

        self.theme_btn = ctk.CTkButton(
            header_right, text="主题", image=self.ctk_icon("theme", (32, 32)),
            compound="left", width=120, height=40, corner_radius=20,
            font=("微软雅黑", 13, "bold"), command=self.toggle_theme
        )
        self.theme_btn.pack(side="left", padx=4, pady=21)

        self.topmost_btn = ctk.CTkButton(
            header_right, text="置顶", image=self.ctk_icon("pin", (32, 32)),
            compound="left", width=112, height=40, corner_radius=20,
            font=("微软雅黑", 13, "bold"), command=self.toggle_topmost
        )
        self.topmost_btn.pack(side="left", padx=4, pady=21)

        self.reset_all_btn = ctk.CTkButton(
            header_right, text="全清", image=self.ctk_icon("reset", (32, 32)),
            compound="left", width=108, height=40, corner_radius=20,
            font=("微软雅黑", 13, "bold"), command=self.reset_all
        )
        self.reset_all_btn.pack(side="left", padx=4, pady=21)

        self.mini_btn = ctk.CTkButton(
            header_right, text="迷你", width=82, height=40, corner_radius=20,
            font=("微软雅黑", 13, "bold"), command=self.enter_mini
        )
        self.mini_btn.pack(side="left", padx=4, pady=21)

        # 窗口控制：减号（最小化）与叉号（关闭），使用极简白色图标
        self.min_win_btn = ctk.CTkButton(
            header_right, text="", image=self.ctk_icon("icon-minus", (22, 22)),
            width=34, height=40, corner_radius=8, command=self.minimize_window
        )
        self.min_win_btn.pack(side="left", padx=(10, 0), pady=21)
        self.close_win_btn = ctk.CTkButton(
            header_right, text="", image=self.ctk_icon("icon-close", (22, 22)),
            width=34, height=40, corner_radius=8, command=self.close_window
        )
        self.close_win_btn.pack(side="left", padx=(2, 0), pady=21)

        # 无边框模式下按住标题栏拖动主窗口
        self.header.bind("<Button-1>", self._main_drag_start)
        self.header.bind("<B1-Motion>", self._main_drag_motion)

        # 主体：左卡片 + 右侧栏
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=26, pady=(16, 8))

        self.card_area = ctk.CTkFrame(self.body, fg_color="transparent")
        self.card_area.pack(side="left", fill="both", expand=True, padx=(0, 18))

        self.build_cards()

        self.build_sidebar()

        # 底部状态栏
        self.status_bar = ctk.CTkLabel(
            self, text="", font=("微软雅黑", 12)
        )
        self.status_bar.pack(side="bottom", pady=(0, 10))

    def build_cards(self):
        students = list(self.scores.keys())
        for idx, name in enumerate(students):
            row, col = divmod(idx, 3)
            card = ctk.CTkFrame(self.card_area, corner_radius=22, border_width=1)
            card.grid(row=row, column=col, padx=12, pady=10, sticky="nsew")
            self.card_frames[name] = card
            # 每张卡片绑定一个稳定的姓名槽，所有回调经它间接取当前姓名
            ref = [name]
            self.name_refs[name] = ref
            card.bind("<Enter>", lambda e, r=ref: self.card_hover(r[0], True))
            card.bind("<Leave>", lambda e, r=ref: self.card_hover(r[0], False))

            avatar = ctk.CTkLabel(card, image=self.ctk_avatar(idx + 1), text="")
            avatar.pack(pady=(14, 4))

            name_label = ctk.CTkLabel(
                card, text=name, font=("微软雅黑", 18, "bold"), cursor="hand2"
            )
            name_label.pack(pady=(0, 2))
            name_label.bind("<Double-Button-1>", lambda e, r=ref: self.rename_student(r[0]))
            self.name_labels[name] = name_label

            score_label = ctk.CTkLabel(
                card, text=str(self.scores[name]), font=("微软雅黑", 42, "bold")
            )
            score_label.pack(pady=(2, 0))
            self.score_labels[name] = score_label

            unit_label = ctk.CTkLabel(card, text="积分", font=("微软雅黑", 11))
            unit_label.pack(pady=(0, 10))
            self.unit_labels[name] = unit_label

            add_btn = ctk.CTkButton(
                card, text=f"＋ {self.point_value}", width=156, height=42,
                corner_radius=21, font=("微软雅黑", 16, "bold"),
                command=lambda r=ref: self.add_score(r[0])
            )
            add_btn.pack(pady=(0, 8))
            self.add_btns[name] = add_btn

            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(pady=(0, 14))
            sub_btn = ctk.CTkButton(
                btn_row, text="－1", width=72, height=32, corner_radius=16,
                font=("微软雅黑", 13, "bold"), command=lambda r=ref: self.sub_score(r[0])
            )
            sub_btn.pack(side="left", padx=5)
            self.sub_btns[name] = sub_btn
            clear_btn = ctk.CTkButton(
                btn_row, text="清零", width=72, height=32, corner_radius=16,
                font=("微软雅黑", 13, "bold"), command=lambda r=ref: self.clear_single(r[0])
            )
            clear_btn.pack(side="left", padx=5)
            self.clear_btns[name] = clear_btn

            for w in [avatar, name_label, score_label, unit_label, add_btn, btn_row]:
                w.bind("<Enter>", lambda e, r=ref: self.card_hover(r[0], True))
                w.bind("<Leave>", lambda e, r=ref: self.card_hover(r[0], False))

        for i in range(3):
            self.card_area.grid_columnconfigure(i, weight=1)
        for i in range(2):
            self.card_area.grid_rowconfigure(i, weight=1)

    def _section_title(self, text):
        """分区标题：左侧一条竖向强调色 + 标题文字，强化视觉层次。"""
        row = ctk.CTkFrame(self.side_panel, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(18, 8))
        bar = ctk.CTkFrame(row, width=4, height=18, corner_radius=2, fg_color="#3B82F6")
        bar.pack(side="left", padx=(0, 9))
        bar.pack_propagate(False)
        label = ctk.CTkLabel(row, text=text, font=("微软雅黑", 15, "bold"), anchor="w")
        label.pack(side="left")
        self.section_bars.append(bar)
        self.section_labels.append(label)

    def build_sidebar(self):
        self.side_panel = ctk.CTkFrame(self.body, width=370, corner_radius=18)
        self.side_panel.pack(side="right", fill="y")
        self.side_panel.pack_propagate(False)
        self.section_bars = []
        self.section_labels = []

        self._section_title("加分分值")
        vrow = ctk.CTkFrame(self.side_panel, fg_color="transparent")
        vrow.pack(padx=20, fill="x")
        self.value_btns = {}
        for val in (1, 2, 5):
            b = ctk.CTkButton(vrow, text=f"+{val}", width=76, height=36,
                              corner_radius=18, font=("微软雅黑", 15, "bold"),
                              command=lambda v=val: self.set_point_value(v))
            b.pack(side="left", padx=5)
            self.value_btns[val] = b

        self._section_title("课堂工具")

        for attr, text, icon, cmd in (
            ("roll_btn", "随机点名", "dice", self.toggle_random_call),
            ("undo_btn", "撤销", "undo", self.undo_action),
            ("redo_btn", "重做", "redo", self.redo_action),
            ("rank_btn", "积分排行榜", "trophy", self.show_rank),
            ("export_btn", "导出积分表", "export", self.export_csv),
        ):
            b = ctk.CTkButton(
                self.side_panel, text=text, image=self.ctk_icon(icon, (44, 44)),
                compound="left", height=52, corner_radius=26,
                font=("微软雅黑", 15, "bold"), command=cmd)
            b.pack(padx=22, fill="x", pady=4)
            setattr(self, attr, b)

        # 点名展示区
        self.roll_display = ctk.CTkFrame(self.side_panel, height=84, corner_radius=14)
        self.roll_display.pack(padx=20, pady=(12, 0), fill="x")
        self.roll_display.pack_propagate(False)
        self.roll_avatar = ctk.CTkLabel(self.roll_display, text="?", font=("微软雅黑", 26, "bold"))
        self.roll_avatar.place(relx=0.24, rely=0.5, anchor="center")
        self.roll_text = ctk.CTkLabel(self.roll_display, text="点击开始抽选",
                                      font=("微软雅黑", 17, "bold"))
        self.roll_text.place(relx=0.64, rely=0.5, anchor="center")

        self._section_title("操作记录")
        self.log_box = ctk.CTkTextbox(self.side_panel, height=170, corner_radius=12,
                                      font=("微软雅黑", 12), spacing2=3)
        self.log_box.pack(padx=20, pady=(0, 16), fill="both", expand=True)
        self.log_box.configure(state="disabled")

    # ---------- 主题应用 ----------
    def apply_theme(self):
        self.configure(fg_color=self.c["bg_canvas"])

        # 标题栏配色
        self.header.configure(fg_color=self.c["header_a"])

        # 主题/置顶/迷你统一浅底深字，与蓝色标题栏形成清晰对比
        header_pill_fg = "#FFFFFF" if self.current_theme == "light" else "#2A3A55"
        header_pill_hover = "#E2E8F0" if self.current_theme == "light" else "#35486B"
        for btn in (self.theme_btn, self.topmost_btn, self.mini_btn):
            btn.configure(fg_color=header_pill_fg, hover_color=header_pill_hover,
                          text_color=self.c["text_main"])
        self.reset_all_btn.configure(fg_color=self.c["btn_sub_text"],
                                     hover_color="#B91C1C", text_color="white")
        self.min_win_btn.configure(
            fg_color=self.c["header_a"], hover_color=self.c["header_b"],
            text_color="white")
        self.close_win_btn.configure(
            fg_color=self.c["header_a"], hover_color="#E5484D", text_color="white")

        self.side_panel.configure(fg_color=self.c["side_panel"])
        for lbl in self.section_labels:
            lbl.configure(text_color=self.c["section_title"])
        for bar in self.section_bars:
            bar.configure(fg_color=self.c["section_title"])

        for name in self.scores:
            card = self.card_frames[name]
            card.configure(fg_color=self.c["card_bg"], border_color=self.c["card_border"])
            self.name_labels[name].configure(text_color=self.c["text_main"])
            self.score_labels[name].configure(text_color=self.c["score_color"])
            self.unit_labels[name].configure(text_color=self.c["text_gray"])
            self.add_btns[name].configure(
                fg_color=self.c["btn_add"], hover_color=self.c["btn_add_hover"],
                text_color="white")
            self.sub_btns[name].configure(
                fg_color=self.c["btn_sub"], hover_color=self.c["btn_sub_hover"],
                text_color=self.c["btn_sub_text"])
            self.clear_btns[name].configure(
                fg_color=self.c["btn_clear"], hover_color=self.c["btn_clear_hover"],
                text_color=self.c["btn_clear_text"])

        for b in (self.roll_btn, self.undo_btn, self.redo_btn, self.rank_btn, self.export_btn):
            b.configure(fg_color=self.c["side_btn"], hover_color=self.c["side_btn_hover"],
                        text_color=self.c["side_btn_text"])

        self.roll_display.configure(fg_color=self.c["card_bg"])
        self.roll_text.configure(text_color=self.c["text_main"])
        self.roll_avatar.configure(text_color=self.c["text_gray"])
        self.log_box.configure(fg_color=self.c["log_bg"], border_color=self.c["log_border"],
                               text_color=self.c["text_gray"])
        self.status_bar.configure(text_color=self.c["status_text"])

        self.update_value_btns()

    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.c = THEME[self.current_theme]
        ctk.set_appearance_mode(self.current_theme)
        self.all_data["theme"] = self.current_theme
        save_data(self.all_data)
        self.apply_theme()
        self.add_log(f"切换为{'深色' if self.current_theme == 'dark' else '浅色'}模式")

    # ---------- 卡片悬浮 ----------
    def card_hover(self, name, enter):
        if name not in self.card_frames:
            return
        self.card_frames[name].configure(
            fg_color=self.c["card_hover"] if enter else self.c["card_bg"],
            border_color=self.c["score_color"] if enter else self.c["card_border"])

    # ---------- 分值 ----------
    def set_point_value(self, val):
        self.point_value = val
        self.all_data["point_value"] = val
        save_data(self.all_data)
        for name, b in self.add_btns.items():
            b.configure(text=f"＋ {val}")
        self.update_value_btns()
        self.add_log(f"加分分值设为 +{val}")

    def update_value_btns(self):
        for val, b in self.value_btns.items():
            if val == self.point_value:
                b.configure(fg_color=self.c["btn_add"], hover_color=self.c["btn_add_hover"],
                           text_color="white")
            else:
                b.configure(fg_color=self.c["side_btn"], hover_color=self.c["side_btn_hover"],
                            text_color=self.c["text_gray"])

    # ---------- 积分操作 ----------
    def push_undo(self, entry):
        self.undo_stack.append(entry)
        self.redo_stack.clear()

    def refresh_score(self, name):
        self.score_labels[name].configure(text=str(self.scores[name]))
        self.all_data["students"] = self.scores
        save_data(self.all_data)

    def add_score(self, name):
        old = self.scores[name]
        self.scores[name] += self.point_value
        self.push_undo({"type": "add", "name": name, "old": old, "new": self.scores[name]})
        self.refresh_score(name)
        self.animate_score(name, up=True)
        self.add_log(f"✅ {name} +{self.point_value} → {self.scores[name]} 分")
        self.check_milestone(name)

    def sub_score(self, name):
        if self.scores[name] <= 0:
            self.add_log(f"⚠ {name} 已是 0 分，不能再减")
            return
        old = self.scores[name]
        self.scores[name] -= 1
        self.push_undo({"type": "sub", "name": name, "old": old, "new": self.scores[name]})
        self.refresh_score(name)
        self.animate_score(name, up=False)
        self.add_log(f"➖ {name} -1 → {self.scores[name]} 分")

    def clear_single(self, name):
        if not messagebox.askyesno("确认清零", f"确定清空「{name}」的积分吗？"):
            return
        old = self.scores[name]
        self.scores[name] = 0
        self.push_undo({"type": "clear", "name": name, "old": old, "new": 0})
        self.refresh_score(name)
        self.add_log(f"🗑 {name} 已清零")

    # ---------- 迷你悬浮模式：小卡片置顶、可拖动、只保留加分 ----------
    def enter_mini(self):
        if self.mini_win and self.mini_win.winfo_exists():
            return
        self._prev_topmost = bool(self.attributes("-topmost"))
        self._prev_geom = self.geometry()

        top = ctk.CTkToplevel(self)
        self.mini_win = top
        top.overrideredirect(True)
        top.attributes("-topmost", True)
        top.configure(fg_color=self.c["side_panel"])
        top.pack_propagate(False)

        bar = ctk.CTkFrame(top, height=32, corner_radius=10, fg_color=self.c["header_a"])
        bar.pack(fill="x", padx=2, pady=(2, 0))
        ctk.CTkLabel(bar, text="课堂积分 · 迷你",
                     font=("微软雅黑", 11, "bold"), text_color="white"
                     ).pack(side="left", padx=10)
        ctk.CTkButton(bar, text="恢复", width=54, height=22, corner_radius=11,
                       font=("微软雅黑", 11, "bold"), command=self.exit_mini
                       ).pack(side="right", padx=7, pady=5)
        bar.bind("<Button-1>", self._mini_drag_start)
        bar.bind("<B1-Motion>", self._mini_drag_motion)

        body = ctk.CTkFrame(top, fg_color="transparent")
        body.pack(fill="x", padx=8, pady=(6, 8))
        self.mini_score_labels = {}
        for idx, name in enumerate(self.scores.keys()):
            r, c = divmod(idx, 2)
            cell = ctk.CTkFrame(body, fg_color=self.c["card_bg"],
                                corner_radius=14, height=46, width=148)
            cell.grid(row=r, column=c, padx=5, pady=3, sticky="nsew")
            cell.pack_propagate(False)
            ctk.CTkLabel(cell, image=self.ctk_avatar(idx + 1, size=(34, 34)), text=""
                         ).pack(side="left", padx=(8, 3), pady=6)
            mid = ctk.CTkFrame(cell, fg_color="transparent")
            mid.pack(side="left", fill="both", expand=True)
            ctk.CTkLabel(mid, text=name, font=("微软雅黑", 11, "bold"),
                         text_color=self.c["text_main"]
                         ).pack(anchor="w")
            sc = ctk.CTkLabel(mid, text=str(self.scores[name]),
                              font=("微软雅黑", 15, "bold"),
                              text_color=self.c["score_color"])
            sc.pack(anchor="w")
            self.mini_score_labels[name] = sc
            ctk.CTkButton(cell, text=f"+{self.point_value}", width=42, height=22,
                          corner_radius=11, font=("微软雅黑", 11, "bold"),
                          fg_color=self.c["btn_add"], hover_color=self.c["btn_add_hover"],
                          command=lambda r=self.name_refs.get(name, [name]): self.mini_add(r[0])
                          ).pack(side="right", padx=7)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        sw = top.winfo_screenwidth()
        sh = top.winfo_screenheight()
        # 迷你窗打开时按屏幕尺寸适配：小屏自动缩小，且保证不超出屏幕边界
        if sh < 800:
            W, H = 300, 196
        else:
            W, H = 340, 218
        mx = max(8, sw - W - 20)
        my = max(8, sh - H - 80)
        top.geometry(f"{W}x{H}+{mx}+{my}")
        self.withdraw()

    def mini_add(self, name):
        if name not in self.scores:
            return
        old = self.scores[name]
        self.scores[name] += self.point_value
        self.push_undo({"type": "add", "name": name, "old": old, "new": self.scores[name]})
        self.refresh_score(name)
        if name in self.mini_score_labels and self.mini_score_labels[name].winfo_exists():
            self.mini_score_labels[name].configure(text=str(self.scores[name]))
        self.add_log(f"✅ {name} +{self.point_value} → {self.scores[name]} 分")
        self.check_milestone(name)

    def exit_mini(self):
        if self.mini_win and self.mini_win.winfo_exists():
            self.mini_win.destroy()
        self.mini_win = None
        self.mini_score_labels = {}
        self.deiconify()
        self.geometry(self._prev_geom)
        self.attributes("-topmost", self._prev_topmost)

    def _mini_drag_start(self, e):
        self._drag_x = e.x_root - self.mini_win.winfo_x()
        self._drag_y = e.y_root - self.mini_win.winfo_y()

    def _mini_drag_motion(self, e):
        self.mini_win.geometry(f"+{e.x_root - self._drag_x}+{e.y_root - self._drag_y}")

    # ---------- 无边框主窗：拖动 / 最小化 / 关闭 ----------
    def _main_drag_start(self, e):
        self._mx = e.x_root - self.winfo_x()
        self._my = e.y_root - self.winfo_y()

    def _main_drag_motion(self, e):
        self.geometry(f"+{e.x_root - self._mx}+{e.y_root - self._my}")

    def minimize_window(self):
        """收起主窗为一个置顶「恢复」小按钮，保证随时可唤出，绝不丢失。"""
        if self.restore_float and self.restore_float.winfo_exists():
            return
        self.withdraw()
        f = ctk.CTkToplevel(self)
        f.overrideredirect(True)
        f.attributes("-topmost", True)
        sw, sh = f.winfo_screenwidth(), f.winfo_screenheight()
        f.geometry(f"116x46+{sw - 132}+{sh - 118}")
        f.configure(fg_color=self.c["header_a"])
        ctk.CTkButton(
            f, text="⤢ 恢复", width=112, height=42, corner_radius=21,
            font=("微软雅黑", 13, "bold"),
            fg_color=self.c["header_a"], hover_color=self.c["header_b"],
            text_color="white", command=self.restore_from_min
        ).pack(padx=2, pady=2)
        self.restore_float = f

    def restore_from_min(self):
        if self.restore_float and self.restore_float.winfo_exists():
            self.restore_float.destroy()
        self.restore_float = None
        self.deiconify()

    def close_window(self):
        try:
            save_data(self.all_data)
        except Exception:
            pass
        self.destroy()

    def reset_all(self):
        if not messagebox.askyesno("确认重置", "确定清空所有学生的积分吗？（可撤销）"):
            return
        snapshot = self.scores.copy()
        for name in self.scores:
            self.scores[name] = 0
            self.score_labels[name].configure(text="0")
        self.push_undo({"type": "reset_all", "snapshot": snapshot})
        save_data(self.all_data)
        self.add_log("✅ 全部积分已重置")

    # ---------- 撤销 / 重做 ----------
    def undo_action(self):
        if not self.undo_stack:
            self.add_log("⚠ 暂无可撤销操作")
            return
        entry = self.undo_stack.pop()
        if entry["type"] == "reset_all":
            self.scores = entry["snapshot"].copy()
            for n, v in self.scores.items():
                self.score_labels[n].configure(text=str(v))
            self.all_data["students"] = self.scores
        elif entry["type"] == "rename":
            self._apply_rename(entry["new_name"], entry["old_name"])
        else:
            name = entry["name"]
            if name not in self.scores:
                self.add_log("⚠ 记录已失效，跳过该步撤销")
                save_data(self.all_data)
                return
            self.scores[name] = entry["old"]
            self.refresh_score(name)
        self.redo_stack.append(entry)
        save_data(self.all_data)
        self.add_log("↩ 已撤销上一步")

    def redo_action(self):
        if not self.redo_stack:
            self.add_log("⚠ 暂无可重做操作")
            return
        entry = self.redo_stack.pop()
        if entry["type"] == "reset_all":
            for name in self.scores:
                self.scores[name] = 0
                self.score_labels[name].configure(text="0")
            self.all_data["students"] = self.scores
        elif entry["type"] == "rename":
            self._apply_rename(entry["old_name"], entry["new_name"])
        else:
            name = entry["name"]
            if name not in self.scores:
                self.add_log("⚠ 记录已失效，跳过该步重做")
                save_data(self.all_data)
                return
            self.scores[name] = entry["new"]
            self.refresh_score(name)
        self.undo_stack.append(entry)
        save_data(self.all_data)
        self.add_log("↪ 已重做上一步")

    # ---------- 随机点名 ----------
    def toggle_random_call(self):
        if self.is_rolling:
            self.is_rolling = False
            self.roll_btn.configure(text="随机点名")
            name = self.roll_text.cget("text")
            self.show_roll_avatar(name)
            self.add_log(f"🎯 抽中：{name}")
        else:
            self.is_rolling = True
            self.roll_btn.configure(text="停止抽选")
            self.roll_students()

    def roll_students(self):
        if not self.is_rolling or not self.winfo_exists():
            return
        name = random.choice(list(self.scores.keys()))
        self.roll_text.configure(text=name)
        self.after(80, self.roll_students)

    def show_roll_avatar(self, name):
        if name in self.scores:
            idx = list(self.scores.keys()).index(name) + 1
            self.roll_avatar.configure(image=self.ctk_avatar(idx, size=(54, 54)), text="")

    # ---------- 改名 ----------
    def _migrate_name(self, old, new):
        """改名时同步各类历史引用，防止撤销/重做使用已失效的旧姓名。"""
        for stack in (self.undo_stack, self.redo_stack):
            for entry in stack:
                if entry.get("name") == old:
                    entry["name"] = new
                if entry.get("type") == "reset_all" and old in entry["snapshot"]:
                    entry["snapshot"] = {
                        new if k == old else k: v for k, v in entry["snapshot"].items()
                    }
        if old in self.milestone_fired:
            self.milestone_fired.discard(old)
            self.milestone_fired.add(new)

    def _apply_rename(self, old_name, new_name):
        # 用原顺序重建 students，避免 pop+赋值把改名学生挤到末尾、卡片重排
        self.scores = {new_name if k == old_name else k: v for k, v in self.scores.items()}
        self.all_data["students"] = self.scores
        for key in ("score_labels", "card_frames", "name_labels", "unit_labels",
                    "add_btns", "sub_btns", "clear_btns"):
            getattr(self, key)[new_name] = getattr(self, key).pop(old_name)
        if old_name in self.mini_score_labels:
            self.mini_score_labels[new_name] = self.mini_score_labels.pop(old_name)
        if old_name in self.name_refs:
            ref = self.name_refs.pop(old_name)
            ref[0] = new_name          # 关键：让已绑定的所有回调指向新姓名
            self.name_refs[new_name] = ref
        self.name_labels[new_name].configure(text=new_name)
        self._migrate_name(old_name, new_name)

    def rename_student(self, old_name):
        dlg = ctk.CTkInputDialog(text=f"请输入「{old_name}」的新姓名：", title="修改姓名")
        new_name = dlg.get_input()
        if not new_name or new_name == old_name:
            return
        if new_name in self.scores:
            messagebox.showwarning("提示", "该姓名已存在")
            return
        self._apply_rename(old_name, new_name)
        self.push_undo({"type": "rename", "old_name": old_name, "new_name": new_name})
        save_data(self.all_data)
        self.add_log(f"✏ 「{old_name}」改名为「{new_name}」")

    # ---------- 排行榜 ----------
    def show_rank(self):
        rank = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        win = ctk.CTkToplevel(self)
        win.title("积分排行榜")
        win.geometry("420x480")
        win.resizable(False, False)
        win.configure(fg_color=self.c["card_bg"])
        win.transient(self)
        ctk.CTkLabel(win, text="🏆 积分排行榜", font=("微软雅黑", 22, "bold"),
                     text_color=self.c["score_color"]).pack(pady=(22, 14))
        medals = ["🥇", "🥈", "🥉"]
        for i, (name, score) in enumerate(rank):
            row = ctk.CTkFrame(win, fg_color=self.c["card_hover"] if i % 2 == 0 else self.c["card_bg"],
                               corner_radius=12)
            row.pack(fill="x", padx=24, pady=5)
            ctk.CTkLabel(row, text=medals[i] if i < 3 else f"{i+1}",
                         font=("微软雅黑", 18, "bold"), width=48,
                         text_color=self.c["text_main"]).pack(side="left", padx=12, pady=10)
            ctk.CTkLabel(row, text=name, font=("微软雅黑", 16, "bold"),
                         text_color=self.c["text_main"]).pack(side="left", pady=10)
            ctk.CTkLabel(row, text=f"{score} 分", font=("微软雅黑", 16, "bold"),
                         text_color=self.c["btn_add"]).pack(side="right", padx=14, pady=10)

    # ---------- 导出 CSV ----------
    def export_csv(self):
        fn = os.path.join(app_dir(), f"课堂积分表_{time.strftime('%Y%m%d_%H%M%S')}.csv")
        rank = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        with open(fn, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["排名", "学生姓名", "积分"])
            for i, (name, score) in enumerate(rank, 1):
                w.writerow([i, name, score])
        self.add_log(f"📊 已导出：{os.path.basename(fn)}")
        messagebox.showinfo("导出成功", f"积分表已保存到：\n{fn}")

    # ---------- 置顶 ----------
    def toggle_topmost(self):
        state = not self.all_data["always_on_top"]
        self.all_data["always_on_top"] = state
        self.attributes("-topmost", state)
        save_data(self.all_data)
        self.topmost_btn.configure(text="已置顶" if state else "置顶")
        self.add_log(f"📌 窗口置顶：{'开启' if state else '关闭'}")

    # ---------- 分数脉冲动画（放大后回弹，稳定不依赖解析当前字号） ----------
    # ---------- 分数反馈：仅颜色闪烁 + 独立上浮气泡；不改字号、不触发布局重排，避免整卡抖动 ----------
    def animate_score(self, name, up=True):
        label = self.score_labels[name]
        flash = self.c["btn_add"] if up else self.c["btn_sub_text"]
        label.configure(text_color=flash)
        self.after(220, lambda: label.configure(text_color=self.c["score_color"])
                   if label.winfo_exists() else None)
        if not up:
            return
        card = self.card_frames[name]
        bx = max(card.winfo_width() // 2, 40)
        by = max(label.winfo_y() - 2, 6)
        bub = ctk.CTkLabel(card, text=f"+{self.point_value}",
                           font=("微软雅黑", 18, "bold"), text_color=flash,
                           fg_color="transparent")
        bub.place(x=bx, y=by, anchor="center")
        self._float_bubble(bub, bx, by, 0)

    def _float_bubble(self, bub, bx, by, step):
        if not bub.winfo_exists():
            return
        if step < 6:
            bub.place(x=bx, y=by - step * 5, anchor="center")
            self.after(28, lambda: self._float_bubble(bub, bx, by, step + 1))
        else:
            bub.destroy()

    # ---------- 里程碑庆祝 ----------
    def check_milestone(self, name):
        score = self.scores[name]
        if score > 0 and score % 10 == 0 and name not in self.milestone_fired:
            self.milestone_fired.add(name)
            self.show_celebration(name, score)
        elif score % 10 != 0:
            self.milestone_fired.discard(name)

    def show_celebration(self, name, score):
        if self.celebration_win and self.celebration_win.winfo_exists():
            self.celebration_win.destroy()
        win = ctk.CTkToplevel(self)
        self.celebration_win = win
        win.geometry("340x330")
        win.resizable(False, False)
        win.configure(fg_color="#FFF8EC")
        win.transient(self)
        sticker = random.choice(["medal", "star", "trophy-big", "thumb"])
        sticker_img = Image.open(asset("stickers", f"{sticker}.png")).convert("RGB")
        img = ctk.CTkImage(light_image=sticker_img, dark_image=sticker_img, size=(150, 150))
        ctk.CTkLabel(win, image=img, text="").pack(pady=(22, 6))
        ctk.CTkLabel(win, text=f"🎉 {name} 太棒了！", font=("微软雅黑", 20, "bold"),
                     text_color="#D97706").pack()
        ctk.CTkLabel(win, text=f"达成 {score} 分里程碑", font=("微软雅黑", 15),
                     text_color="#92400E").pack(pady=(4, 16))
        win.bind("<Button-1>", lambda e: win.destroy())
        win.after(2400, lambda: win.destroy() if win.winfo_exists() else None)

    # ---------- 日志 ----------
    def add_log(self, text):
        ts = time.strftime("%H:%M:%S")
        self.log_box.configure(state="normal")
        self.log_box.insert("0.0", f"[{ts}] {text}\n")
        self.log_box.configure(state="disabled")
        self.status_bar.configure(text=text)


if __name__ == "__main__":
    app = ScoreApp()
    app.mainloop()
