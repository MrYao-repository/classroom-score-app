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
from PIL import Image, ImageTk

# Pillow 新旧版本缩放别名兼容
LANCZOS = getattr(getattr(Image, "Resampling", None), "LANCZOS", Image.LANCZOS)

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
        "btn_sub_text": "#DC2626",
        "btn_clear": "#E5E7EB",
        "btn_clear_text": "#4B5563",
        "side_btn": "#FFFFFF",
        "side_btn_hover": "#EFF6FF",
        "side_btn_text": "#1F2937",
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
        "btn_sub_text": "#F87171",
        "btn_clear": "#2E3B52",
        "btn_clear_text": "#CBD5E1",
        "side_btn": "#263449",
        "side_btn_hover": "#30435F",
        "side_btn_text": "#E2E8F0",
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
            for k, v in DEFAULT_DATA.items():
                data.setdefault(k, v if not isinstance(v, dict) else v.copy())
            return data
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULT_DATA))

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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
        self.add_btns = {}
        self.icon_imgs = {}
        self.avatar_imgs = {}

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
    def ctk_icon(self, name, size=(26, 26)):
        key = (name, tuple(size))
        if key not in self.icon_imgs:
            im = Image.open(asset("icons", f"{name}.png")).convert("RGBA")
            self.icon_imgs[key] = ctk.CTkImage(light_image=im, dark_image=im, size=size)
        return self.icon_imgs[key]

    def ctk_avatar(self, idx, size=(64, 64)):
        key = (idx, tuple(size))
        if key not in self.avatar_imgs:
            im = Image.open(asset("avatars", f"student-{idx:02d}.png")).convert("RGBA")
            self.avatar_imgs[key] = ctk.CTkImage(light_image=im, dark_image=im, size=size)
        return self.avatar_imgs[key]

    # ---------- 界面搭建 ----------
    def build_ui(self):
        # 顶部标题栏（主窗口使用主题纯色背景，避免 tkinter 无法透明透出图片的问题）
        self.header = ctk.CTkFrame(self, height=82, corner_radius=0)
        self.header.pack(fill="x", side="top")
        self.header.pack_propagate(False)

        self.title_label = ctk.CTkLabel(
            self.header, text="📖 课堂积分系统 Pro",
            font=("微软雅黑", 24, "bold"), text_color="white"
        )
        self.title_label.place(x=34, rely=0.5, anchor="w")

        self.theme_btn = ctk.CTkButton(
            self.header, text="主题", image=self.ctk_icon("theme", (34, 34)),
            compound="left", width=126, height=42, corner_radius=21,
            font=("微软雅黑", 13, "bold"), command=self.toggle_theme
        )
        self.theme_btn.place(x=688, y=20)

        self.topmost_btn = ctk.CTkButton(
            self.header, text="置顶", image=self.ctk_icon("pin", (34, 34)),
            compound="left", width=116, height=42, corner_radius=21,
            font=("微软雅黑", 13, "bold"), command=self.toggle_topmost
        )
        self.topmost_btn.place(x=826, y=20)

        self.reset_all_btn = ctk.CTkButton(
            self.header, text="全清", image=self.ctk_icon("reset", (34, 34)),
            compound="left", width=112, height=42, corner_radius=21,
            font=("微软雅黑", 13, "bold"), command=self.reset_all
        )
        self.reset_all_btn.place(x=954, y=20)

        self.mini_btn = ctk.CTkButton(
            self.header, text="迷你", width=86, height=42, corner_radius=21,
            font=("微软雅黑", 13, "bold"), command=self.enter_mini
        )
        self.mini_btn.place(x=1074, y=20)

        # 自绘窗口控制：最小化 / 关闭（白色透明底图标）
        self.min_win_btn = ctk.CTkButton(
            self.header, text="", image=self.ctk_icon("minimize", (20, 20)),
            width=34, height=42, corner_radius=8, command=self.minimize_window
        )
        self.min_win_btn.place(x=1168, y=20)
        self.close_win_btn = ctk.CTkButton(
            self.header, text="", image=self.ctk_icon("close", (20, 20)),
            width=34, height=42, corner_radius=8, command=self.close_window
        )
        self.close_win_btn.place(x=1208, y=20)

        # 无边框模式下按住标题栏拖动主窗口
        self.header.bind("<Button-1>", self._main_drag_start)
        self.header.bind("<B1-Motion>", self._main_drag_motion)
        self.title_label.bind("<Button-1>", self._main_drag_start)
        self.title_label.bind("<B1-Motion>", self._main_drag_motion)

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
            card.bind("<Enter>", lambda e, n=name: self.card_hover(n, True))
            card.bind("<Leave>", lambda e, n=name: self.card_hover(n, False))

            avatar = ctk.CTkLabel(card, image=self.ctk_avatar(idx + 1), text="")
            avatar.pack(pady=(12, 2))

            name_label = ctk.CTkLabel(
                card, text=name, font=("微软雅黑", 17, "bold"), cursor="hand2"
            )
            name_label.pack(pady=(0, 2))
            name_label.bind("<Double-Button-1>", lambda e, n=name: self.rename_student(n))
            self.name_labels[name] = name_label

            score_label = ctk.CTkLabel(
                card, text=str(self.scores[name]), font=("微软雅黑", 38, "bold")
            )
            score_label.pack()
            self.score_labels[name] = score_label

            unit_label = ctk.CTkLabel(card, text="积分", font=("微软雅黑", 12))
            unit_label.pack(pady=(0, 6))

            add_btn = ctk.CTkButton(
                card, text=f"＋ {self.point_value} 分", width=150, height=40,
                corner_radius=20, font=("微软雅黑", 14, "bold"),
                command=lambda n=name: self.add_score(n)
            )
            add_btn.pack(pady=(0, 6))
            self.add_btns[name] = add_btn

            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(pady=(0, 12))
            sub_btn = ctk.CTkButton(
                btn_row, text="－1", width=72, height=30, corner_radius=15,
                font=("微软雅黑", 13, "bold"), command=lambda n=name: self.sub_score(n)
            )
            sub_btn.pack(side="left", padx=4)
            clear_btn = ctk.CTkButton(
                btn_row, text="清零", width=72, height=30, corner_radius=15,
                font=("微软雅黑", 13, "bold"), command=lambda n=name: self.clear_single(n)
            )
            clear_btn.pack(side="left", padx=4)

            for w in [avatar, name_label, score_label, unit_label, add_btn, btn_row]:
                w.bind("<Enter>", lambda e, n=name: self.card_hover(n, True))
                w.bind("<Leave>", lambda e, n=name: self.card_hover(n, False))

        for i in range(3):
            self.card_area.grid_columnconfigure(i, weight=1)
        for i in range(2):
            self.card_area.grid_rowconfigure(i, weight=1)

    def build_sidebar(self):
        self.side_panel = ctk.CTkFrame(self.body, width=370, corner_radius=18)
        self.side_panel.pack(side="right", fill="y")
        self.side_panel.pack_propagate(False)

        ctk.CTkLabel(self.side_panel, text="⚙ 加分分值", font=("微软雅黑", 15, "bold")
                     ).pack(pady=(18, 8), anchor="w", padx=20)
        vrow = ctk.CTkFrame(self.side_panel, fg_color="transparent")
        vrow.pack(padx=20, fill="x")
        self.value_btns = {}
        for val in (1, 2, 5):
            b = ctk.CTkButton(vrow, text=f"+{val}", width=72, height=34,
                              corner_radius=17, font=("微软雅黑", 14, "bold"),
                              command=lambda v=val: self.set_point_value(v))
            b.pack(side="left", padx=5)
            self.value_btns[val] = b

        ctk.CTkLabel(self.side_panel, text="🎯 课堂工具", font=("微软雅黑", 15, "bold")
                     ).pack(pady=(20, 8), anchor="w", padx=20)

        self.roll_btn = ctk.CTkButton(
            self.side_panel, text="随机点名", image=self.ctk_icon("dice", (48, 48)),
            compound="left", height=54, corner_radius=27, font=("微软雅黑", 16, "bold"),
            command=self.toggle_random_call)
        self.roll_btn.pack(padx=24, fill="x", pady=3)

        self.undo_btn = ctk.CTkButton(
            self.side_panel, text="撤销", image=self.ctk_icon("undo", (48, 48)),
            compound="left", height=54, corner_radius=27, font=("微软雅黑", 16, "bold"),
            command=self.undo_action)
        self.undo_btn.pack(padx=24, fill="x", pady=3)
        self.redo_btn = ctk.CTkButton(
            self.side_panel, text="重做", image=self.ctk_icon("redo", (48, 48)),
            compound="left", height=54, corner_radius=27, font=("微软雅黑", 16, "bold"),
            command=self.redo_action)
        self.redo_btn.pack(padx=24, fill="x", pady=3)

        self.rank_btn = ctk.CTkButton(
            self.side_panel, text="积分排行榜", image=self.ctk_icon("trophy", (48, 48)),
            compound="left", height=54, corner_radius=27, font=("微软雅黑", 16, "bold"),
            command=self.show_rank)
        self.rank_btn.pack(padx=24, fill="x", pady=3)

        self.export_btn = ctk.CTkButton(
            self.side_panel, text="导出积分表", image=self.ctk_icon("export", (48, 48)),
            compound="left", height=54, corner_radius=27, font=("微软雅黑", 16, "bold"),
            command=self.export_csv)
        self.export_btn.pack(padx=20, fill="x", pady=4)

        # 点名展示区
        self.roll_display = ctk.CTkFrame(self.side_panel, height=84, corner_radius=14)
        self.roll_display.pack(padx=20, pady=(10, 0), fill="x")
        self.roll_avatar = ctk.CTkLabel(self.roll_display, text="?", font=("微软雅黑", 26, "bold"))
        self.roll_avatar.place(relx=0.26, rely=0.5, anchor="center")
        self.roll_text = ctk.CTkLabel(self.roll_display, text="点击开始抽选",
                                      font=("微软雅黑", 18, "bold"))
        self.roll_text.place(relx=0.66, rely=0.5, anchor="center")

        ctk.CTkLabel(self.side_panel, text="📝 操作记录", font=("微软雅黑", 15, "bold")
                     ).pack(pady=(16, 6), anchor="w", padx=20)
        self.log_box = ctk.CTkTextbox(self.side_panel, height=170, corner_radius=12,
                                      font=("微软雅黑", 12), spacing2=3)
        self.log_box.pack(padx=20, pady=(0, 16), fill="both", expand=True)
        self.log_box.configure(state="disabled")

    # ---------- 主题应用 ----------
    def apply_theme(self):
        self.configure(fg_color=self.c["bg_canvas"])

        # 标题栏配色
        self.header.configure(fg_color=self.c["header_a"])

        self.theme_btn.configure(
            fg_color="#FFFFFF" if self.current_theme == "light" else "#2A3A55",
            hover_color="#E2E8F0" if self.current_theme == "light" else "#35486B",
            text_color=self.c["text_main"])
        self.topmost_btn.configure(
            fg_color=self.c["btn_primary"] if "btn_primary" in self.c else self.c["header_a"],
            hover_color=self.c["header_b"], text_color="white")
        self.reset_all_btn.configure(fg_color=self.c["btn_sub_text"],
                                     hover_color="#B91C1C", text_color="white")
        self.min_win_btn.configure(
            fg_color=self.c["header_a"], hover_color=self.c["header_b"],
            text_color="white")
        self.close_win_btn.configure(
            fg_color=self.c["header_a"], hover_color="#E5484D", text_color="white")

        self.side_panel.configure(fg_color=self.c["side_panel"])

        for name in self.scores:
            card = self.card_frames[name]
            card.configure(fg_color=self.c["card_bg"], border_color=self.c["card_border"])
            self.name_labels[name].configure(text_color=self.c["text_main"])
            self.score_labels[name].configure(text_color=self.c["score_color"])

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
        self.card_frames[name].configure(
            fg_color=self.c["card_hover"] if enter else self.c["card_bg"],
            border_color=self.c["score_color"] if enter else self.c["card_border"])

    # ---------- 分值 ----------
    def set_point_value(self, val):
        self.point_value = val
        self.all_data["point_value"] = val
        save_data(self.all_data)
        for name, b in self.add_btns.items():
            b.configure(text=f"＋ {val} 分")
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
                          command=lambda n=name: self.mini_add(n)
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
        old = self.scores[name]
        self.scores[name] += self.point_value
        self.push_undo({"type": "add", "name": name, "old": old, "new": self.scores[name]})
        self.refresh_score(name)
        if name in self.mini_score_labels and self.mini_score_labels[name].winfo_exists():
            self.mini_score_labels[name].configure(text=str(self.scores[name]))
        self.add_log(f"✅ {name} +{self.point_value} → {self.scores[name]} 分")

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
            self.redo_stack.append(entry)
        else:
            name = entry["name"]
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
            self.undo_stack.append(entry)
        else:
            name = entry["name"]
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
        if not self.is_rolling:
            return
        name = random.choice(list(self.scores.keys()))
        self.roll_text.configure(text=name)
        self.after(80, self.roll_students)

    def show_roll_avatar(self, name):
        if name in self.scores:
            idx = list(self.scores.keys()).index(name) + 1
            self.roll_avatar.configure(image=self.ctk_avatar(idx, size=(54, 54)), text="")

    # ---------- 改名 ----------
    def rename_student(self, old_name):
        dlg = ctk.CTkInputDialog(text=f"请输入「{old_name}」的新姓名：", title="修改姓名")
        new_name = dlg.get_input()
        if not new_name or new_name == old_name:
            return
        if new_name in self.scores:
            messagebox.showwarning("提示", "该姓名已存在")
            return
        self.scores[new_name] = self.scores.pop(old_name)
        self.all_data["students"] = self.scores
        for key in ("score_labels", "card_frames", "name_labels", "add_btns"):
            getattr(self, key)[new_name] = getattr(self, key).pop(old_name)
        self.name_labels[new_name].configure(text=new_name)
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
        self.after(220, lambda: label.configure(text_color=self.c["score_color"]))
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
        img = ctk.CTkImage(light_image=Image.open(asset("stickers", f"{sticker}.png")).convert("RGB"),
                           dark_image=Image.open(asset("stickers", f"{sticker}.png")).convert("RGB"),
                           size=(150, 150))
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
