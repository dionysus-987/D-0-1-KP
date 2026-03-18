# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Optional, List
import threading

from models import DKPInstance, SolveResult
from parser_utils import parse_dkp_instances
from plot_panel import PlotPanel
from solver import sort_groups_by_third_ratio, solve_dkp_dp, build_result_text


class MainWindow:
    BG = "#f5f7fb"
    CARD_BG = "#ffffff"
    PANEL_BG = "#eef3f8"
    ACCENT = "#2f6fed"
    TEXT = "#1f2937"
    SUBTEXT = "#5b6472"
    BORDER = "#d7deea"
    SUCCESS = "#1f9d55"
    WARNING = "#d97706"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("D{0-1}KP 动态规划求解系统")
        self.root.geometry("1680x960")
        self.root.minsize(1280, 760)
        self.root.configure(bg=self.BG)

        self.instances: Dict[str, DKPInstance] = {}
        self.filtered_names: List[str] = []
        self.current_instance: Optional[DKPInstance] = None
        self.current_result: Optional[SolveResult] = None
        self.is_solving = False

        self.sorted_plot_var = tk.BooleanVar(value=False)
        self.sorted_solve_var = tk.BooleanVar(value=False)
        self.auto_plot_var = tk.BooleanVar(value=True)
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="就绪")
        self.summary_var = tk.StringVar(value="尚未求解")
        self.current_name_var = tk.StringVar(value="未选择实例")
        self.instance_count_var = tk.StringVar(value="实例数：0")

        self._setup_styles()
        self._build_ui()
        self._bind_events()

    # =========================
    # 基础样式
    # =========================
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            ".",
            font=("Microsoft YaHei", 10),
            background=self.BG,
            foreground=self.TEXT
        )

        style.configure(
            "App.TFrame",
            background=self.BG
        )

        style.configure(
            "Card.TFrame",
            background=self.CARD_BG,
            relief="flat"
        )

        style.configure(
            "Topbar.TFrame",
            background=self.CARD_BG
        )

        style.configure(
            "Title.TLabel",
            background=self.CARD_BG,
            foreground=self.TEXT,
            font=("Microsoft YaHei", 16, "bold")
        )

        style.configure(
            "Subtitle.TLabel",
            background=self.CARD_BG,
            foreground=self.SUBTEXT,
            font=("Microsoft YaHei", 10)
        )

        style.configure(
            "Section.TLabel",
            background=self.CARD_BG,
            foreground=self.TEXT,
            font=("Microsoft YaHei", 10, "bold")
        )

        style.configure(
            "Info.TLabel",
            background=self.CARD_BG,
            foreground=self.SUBTEXT,
            font=("Microsoft YaHei", 9)
        )

        style.configure(
            "Primary.TButton",
            padding=(12, 7),
            font=("Microsoft YaHei", 10, "bold")
        )

        style.configure(
            "Secondary.TButton",
            padding=(10, 6),
            font=("Microsoft YaHei", 10)
        )

        style.configure(
            "TButton",
            padding=(10, 6)
        )

        style.configure(
            "TCheckbutton",
            background=self.CARD_BG,
            foreground=self.TEXT
        )

        style.configure(
            "TNotebook",
            background=self.CARD_BG,
            borderwidth=0
        )

        style.configure(
            "TNotebook.Tab",
            padding=(14, 8),
            font=("Microsoft YaHei", 10)
        )

        style.configure(
            "Treeview",
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground=self.TEXT,
            rowheight=28,
            bordercolor=self.BORDER,
            lightcolor=self.BORDER,
            darkcolor=self.BORDER
        )
        style.configure(
            "Treeview.Heading",
            font=("Microsoft YaHei", 10, "bold"),
            background="#edf2f9",
            foreground=self.TEXT,
            relief="flat"
        )

        style.map(
            "Treeview",
            background=[("selected", "#dce8ff")],
            foreground=[("selected", self.TEXT)]
        )

        style.configure(
            "Status.TLabel",
            background=self.CARD_BG,
            foreground=self.SUBTEXT,
            font=("Microsoft YaHei", 9)
        )

    # =========================
    # UI 构建
    # =========================
    def _build_ui(self):
        self._build_top_header()
        self._build_toolbar()
        self._build_main_area()
        self._build_statusbar()

    def _build_top_header(self):
        wrapper = ttk.Frame(self.root, style="App.TFrame")
        wrapper.pack(fill=tk.X, padx=10, pady=(10, 6))

        card = tk.Frame(
            wrapper, bg=self.CARD_BG, bd=1, relief="solid",
            highlightthickness=0
        )
        card.pack(fill=tk.X)

        left = tk.Frame(card, bg=self.CARD_BG)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=16, pady=12)

        ttk.Label(left, text="D{0-1}KP 动态规划求解系统", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            left,
            text="实例管理、散点可视化、排序预览与动态规划求解",
            style="Subtitle.TLabel"
        ).pack(anchor="w", pady=(3, 0))

        right = tk.Frame(card, bg=self.CARD_BG)
        right.pack(side=tk.RIGHT, padx=16, pady=12)

        tk.Label(
            right,
            textvariable=self.current_name_var,
            bg=self.CARD_BG,
            fg=self.ACCENT,
            font=("Microsoft YaHei", 11, "bold")
        ).pack(anchor="e")

        tk.Label(
            right,
            textvariable=self.summary_var,
            bg=self.CARD_BG,
            fg=self.SUBTEXT,
            font=("Microsoft YaHei", 9)
        ).pack(anchor="e", pady=(4, 0))

    def _build_toolbar(self):
        wrapper = ttk.Frame(self.root, style="App.TFrame")
        wrapper.pack(fill=tk.X, padx=10, pady=(0, 8))

        bar = tk.Frame(wrapper, bg=self.CARD_BG, bd=1, relief="solid")
        bar.pack(fill=tk.X)

        left = tk.Frame(bar, bg=self.CARD_BG)
        left.pack(side=tk.LEFT, padx=12, pady=10)

        ttk.Button(left, text="打开数据", command=self.load_file, style="Primary.TButton").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(left, text="保存结果", command=self.save_result, style="Secondary.TButton").pack(side=tk.LEFT, padx=(0, 14))
        ttk.Button(left, text="绘制散点图", command=self.plot_current_instance, style="Secondary.TButton").pack(side=tk.LEFT, padx=4)
        self.btn_solve_top = ttk.Button(left, text="开始求解", command=self.solve_current_instance, style="Primary.TButton")
        self.btn_solve_top.pack(side=tk.LEFT, padx=4)

        right = tk.Frame(bar, bg=self.CARD_BG)
        right.pack(side=tk.RIGHT, padx=12, pady=10)

        ttk.Checkbutton(right, text="绘图按第三项比率排序", variable=self.sorted_plot_var).pack(side=tk.LEFT, padx=8)
        ttk.Checkbutton(right, text="求解前排序", variable=self.sorted_solve_var).pack(side=tk.LEFT, padx=8)
        ttk.Checkbutton(right, text="切换实例自动绘图", variable=self.auto_plot_var).pack(side=tk.LEFT, padx=8)

    def _build_main_area(self):
        outer = ttk.Frame(self.root, style="App.TFrame")
        outer.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        paned = ttk.Panedwindow(outer, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        self.left_panel = tk.Frame(paned, bg=self.BG)
        self.center_panel = tk.Frame(paned, bg=self.BG)
        self.right_panel = tk.Frame(paned, bg=self.BG)

        paned.add(self.left_panel, weight=22)
        paned.add(self.center_panel, weight=48)
        paned.add(self.right_panel, weight=30)

        self._build_left_panel()
        self._build_center_panel()
        self._build_right_panel()

    def _build_left_panel(self):
        self.left_panel.rowconfigure(1, weight=1)
        self.left_panel.rowconfigure(2, weight=0)
        self.left_panel.columnconfigure(0, weight=1)

        # 搜索卡片
        search_card = self._card(self.left_panel)
        search_card.grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=(0, 8))

        ttk.Label(search_card, text="实例导航", style="Section.TLabel").pack(anchor="w")
        ttk.Label(search_card, textvariable=self.instance_count_var, style="Info.TLabel").pack(anchor="w", pady=(2, 8))

        search_entry = tk.Entry(
            search_card,
            textvariable=self.search_var,
            relief="flat",
            bg="#f8fafc",
            fg=self.TEXT,
            insertbackground=self.TEXT,
            font=("Microsoft YaHei", 10)
        )
        search_entry.pack(fill=tk.X, ipady=6)
        self.search_entry = search_entry

        # 实例列表卡片
        list_card = self._card(self.left_panel)
        list_card.grid(row=1, column=0, sticky="nsew", padx=(0, 6), pady=(0, 8))
        list_card.rowconfigure(1, weight=1)
        list_card.columnconfigure(0, weight=1)

        ttk.Label(list_card, text="实例列表", style="Section.TLabel").grid(row=0, column=0, sticky="w")

        list_container = tk.Frame(list_card, bg=self.CARD_BG)
        list_container.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        list_container.rowconfigure(0, weight=1)
        list_container.columnconfigure(0, weight=1)

        self.instance_listbox = tk.Listbox(
            list_container,
            exportselection=False,
            font=("Segoe UI", 10),
            selectbackground=self.ACCENT,
            selectforeground="#ffffff",
            activestyle="none",
            relief="flat",
            bg="#fbfcfe",
            fg=self.TEXT,
            highlightthickness=0,
            bd=0
        )
        self.instance_listbox.grid(row=0, column=0, sticky="nsew")

        list_scroll = ttk.Scrollbar(list_container, orient="vertical", command=self.instance_listbox.yview)
        list_scroll.grid(row=0, column=1, sticky="ns")
        self.instance_listbox.config(yscrollcommand=list_scroll.set)

        # 基本信息卡片
        info_card = self._card(self.left_panel)
        info_card.grid(row=2, column=0, sticky="ew", padx=(0, 6))

        ttk.Label(info_card, text="实例信息", style="Section.TLabel").pack(anchor="w")

        self.info_text = tk.Text(
            info_card,
            height=7,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Consolas", 10),
            bg="#fbfcfe",
            fg=self.TEXT,
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=6,
            pady=6
        )
        self.info_text.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

    def _build_center_panel(self):
        self.center_panel.rowconfigure(0, weight=1)
        self.center_panel.columnconfigure(0, weight=1)

        card = self._card(self.center_panel)
        card.grid(row=0, column=0, sticky="nsew", padx=6)
        card.rowconfigure(1, weight=1)
        card.columnconfigure(0, weight=1)

        top = tk.Frame(card, bg=self.CARD_BG)
        top.grid(row=0, column=0, sticky="ew")

        ttk.Label(top, text="数据可视化", style="Section.TLabel").pack(side=tk.LEFT)
        ttk.Label(
            top,
            text="散点图分析区",
            style="Info.TLabel"
        ).pack(side=tk.LEFT, padx=(10, 0))

        plot_wrap = tk.Frame(card, bg=self.CARD_BG)
        plot_wrap.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        plot_wrap.rowconfigure(0, weight=1)
        plot_wrap.columnconfigure(0, weight=1)

        self.plot_panel = PlotPanel(plot_wrap)
        self.plot_panel.pack(fill=tk.BOTH, expand=True)

    def _build_right_panel(self):
        self.right_panel.rowconfigure(1, weight=1)
        self.right_panel.columnconfigure(0, weight=1)

        control_card = self._card(self.right_panel)
        control_card.grid(row=0, column=0, sticky="ew", padx=(6, 0), pady=(0, 8))
        control_card.columnconfigure(0, weight=1)
        control_card.columnconfigure(1, weight=1)

        ttk.Label(control_card, text="操作控制", style="Section.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")

        ttk.Button(
            control_card,
            text="显示排序预览",
            command=self.show_sorted_table,
            style="Secondary.TButton"
        ).grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=(10, 4))

        self.btn_solve = ttk.Button(
            control_card,
            text="开始求解",
            command=self.solve_current_instance,
            style="Primary.TButton"
        )
        self.btn_solve.grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=(10, 4))

        ttk.Button(
            control_card,
            text="保存结果",
            command=self.save_result,
            style="Secondary.TButton"
        ).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 4))

        summary_box = tk.Frame(control_card, bg="#f8fafc", bd=1, relief="solid")
        summary_box.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        tk.Label(
            summary_box,
            textvariable=self.summary_var,
            bg="#f8fafc",
            fg=self.SUBTEXT,
            font=("Microsoft YaHei", 9),
            anchor="w",
            justify="left",
            padx=10,
            pady=8
        ).pack(fill=tk.X)

        notebook_card = self._card(self.right_panel)
        notebook_card.grid(row=1, column=0, sticky="nsew", padx=(6, 0))
        notebook_card.rowconfigure(1, weight=1)
        notebook_card.columnconfigure(0, weight=1)

        ttk.Label(notebook_card, text="结果面板", style="Section.TLabel").grid(row=0, column=0, sticky="w")

        self.notebook = ttk.Notebook(notebook_card)
        self.notebook.grid(row=1, column=0, sticky="nsew", pady=(10, 0))

        self.sort_tab = tk.Frame(self.notebook, bg=self.CARD_BG)
        self.result_tab = tk.Frame(self.notebook, bg=self.CARD_BG)
        self.notebook.add(self.sort_tab, text="排序预览")
        self.notebook.add(self.result_tab, text="求解结果")

        self._build_sort_tab()
        self._build_result_tab()

    def _build_sort_tab(self):
        self.sort_tab.rowconfigure(0, weight=1)
        self.sort_tab.columnconfigure(0, weight=1)

        table_wrap = tk.Frame(self.sort_tab, bg=self.CARD_BG)
        table_wrap.grid(row=0, column=0, sticky="nsew")
        table_wrap.rowconfigure(0, weight=1)
        table_wrap.columnconfigure(0, weight=1)

        columns = ("idx", "gid", "w3", "p3", "ratio")
        self.sort_tree = ttk.Treeview(table_wrap, columns=columns, show="headings")

        headers = {
            "idx": "序号",
            "gid": "组号",
            "w3": "重量3",
            "p3": "价值3",
            "ratio": "价值/重量"
        }
        widths = {
            "idx": 60,
            "gid": 80,
            "w3": 90,
            "p3": 90,
            "ratio": 110
        }

        for col in columns:
            self.sort_tree.heading(col, text=headers[col])
            self.sort_tree.column(col, width=widths[col], anchor="center", stretch=True)

        self.sort_tree.grid(row=0, column=0, sticky="nsew")

        yscroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.sort_tree.yview)
        yscroll.grid(row=0, column=1, sticky="ns")
        self.sort_tree.config(yscrollcommand=yscroll.set)

    def _build_result_tab(self):
        self.result_tab.rowconfigure(0, weight=1)
        self.result_tab.columnconfigure(0, weight=1)

        result_wrap = tk.Frame(self.result_tab, bg=self.CARD_BG)
        result_wrap.grid(row=0, column=0, sticky="nsew")
        result_wrap.rowconfigure(0, weight=1)
        result_wrap.columnconfigure(0, weight=1)

        self.result_text = tk.Text(
            result_wrap,
            wrap=tk.NONE,
            state=tk.DISABLED,
            font=("Consolas", 10),
            bg="#fbfcfe",
            fg=self.TEXT,
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=8,
            pady=8
        )
        self.result_text.grid(row=0, column=0, sticky="nsew")

        yscroll = ttk.Scrollbar(result_wrap, orient="vertical", command=self.result_text.yview)
        yscroll.grid(row=0, column=1, sticky="ns")
        self.result_text.config(yscrollcommand=yscroll.set)

    def _build_statusbar(self):
        wrapper = ttk.Frame(self.root, style="App.TFrame")
        wrapper.pack(fill=tk.X, padx=10, pady=(0, 10))

        bar = tk.Frame(wrapper, bg=self.CARD_BG, bd=1, relief="solid")
        bar.pack(fill=tk.X)

        left = tk.Frame(bar, bg=self.CARD_BG)
        left.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=12, pady=8)

        ttk.Label(left, textvariable=self.status_var, style="Status.TLabel").pack(side=tk.LEFT)

        right = tk.Frame(bar, bg=self.CARD_BG)
        right.pack(side=tk.RIGHT, padx=12, pady=8)

        self.progress = ttk.Progressbar(right, mode="indeterminate", length=140)
        self.progress.pack(side=tk.RIGHT)

    # =========================
    # 交互绑定
    # =========================
    def _bind_events(self):
        self.root.bind("<Control-o>", lambda e: self.load_file())
        self.root.bind("<Control-s>", lambda e: self.save_result())
        self.root.bind("<F5>", lambda e: self.plot_current_instance())
        self.root.bind("<F6>", lambda e: self.solve_current_instance())

        self.instance_listbox.bind("<<ListboxSelect>>", self.on_instance_changed)
        self.instance_listbox.bind("<Double-Button-1>", lambda e: self.plot_current_instance())
        self.search_var.trace_add("write", lambda *args: self._filter_instance_list())

    # =========================
    # UI 小工具
    # =========================
    def _card(self, parent):
        frame = tk.Frame(parent, bg=self.CARD_BG, bd=1, relief="solid")
        frame.configure(highlightthickness=0)
        frame.pack_propagate(False)
        return self._pad_wrap(frame)

    def _pad_wrap(self, widget):
        outer = tk.Frame(widget.master, bg=self.BG)
        widget.pack(in_=outer, fill=tk.BOTH, expand=True, padx=0, pady=0)
        return outer

    def _inner_card_frame(self, card_outer):
        return card_outer.winfo_children()[0]

    def _set_text(self, text_widget: tk.Text, content: str):
        text_widget.config(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)
        text_widget.insert(tk.END, content)
        text_widget.config(state=tk.DISABLED)

    def _set_solving_state(self, solving: bool):
        self.is_solving = solving
        state = "disabled" if solving else "normal"

        self.btn_solve.config(state=state)
        self.btn_solve_top.config(state=state)
        self.instance_listbox.config(state=state)
        self.search_entry.config(state=state)

        if solving:
            self.root.config(cursor="watch")
            self.progress.start(10)
        else:
            self.root.config(cursor="")
            self.progress.stop()

    def _update_summary(self, text: str):
        self.summary_var.set(text)

    def _update_current_instance_label(self, name: str):
        self.current_name_var.set(name)

    def _filter_instance_list(self):
        keyword = self.search_var.get().strip().lower()
        all_names = list(self.instances.keys())

        if not keyword:
            self.filtered_names = all_names
        else:
            self.filtered_names = [name for name in all_names if keyword in name.lower()]

        current = None
        sel = self.instance_listbox.curselection()
        if sel:
            try:
                current = self.instance_listbox.get(sel[0])
            except Exception:
                current = None

        self.instance_listbox.delete(0, tk.END)
        for name in self.filtered_names:
            self.instance_listbox.insert(tk.END, name)

        self.instance_count_var.set(f"实例数：{len(self.filtered_names)} / {len(all_names)}")

        if current in self.filtered_names:
            idx = self.filtered_names.index(current)
            self.instance_listbox.selection_set(idx)
            self.instance_listbox.activate(idx)

    # =========================
    # 业务逻辑
    # =========================
    def load_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        try:
            self.status_var.set("正在解析数据文件...")
            self.root.update_idletasks()

            self.instances = parse_dkp_instances(file_path)
            self.search_var.set("")
            self.filtered_names = list(self.instances.keys())

            self.instance_listbox.delete(0, tk.END)
            for name in self.filtered_names:
                self.instance_listbox.insert(tk.END, name)

            self.instance_count_var.set(f"实例数：{len(self.filtered_names)}")
            self.current_instance = None
            self.current_result = None

            self._set_text(self.info_text, "")
            self._set_text(self.result_text, "")
            self._update_current_instance_label("未选择实例")
            self._update_summary("尚未求解")

            for item in self.sort_tree.get_children():
                self.sort_tree.delete(item)

            self.status_var.set(f"加载成功：{len(self.instances)} 个实例")

            if self.instance_listbox.size() > 0:
                self.instance_listbox.selection_set(0)
                self.instance_listbox.activate(0)
                self.on_instance_changed()

        except Exception as e:
            messagebox.showerror("错误", str(e))
            self.status_var.set("加载失败")

    def on_instance_changed(self, event=None):
        sel = self.instance_listbox.curselection()
        if not sel:
            return

        name = self.instance_listbox.get(sel[0])
        if name not in self.instances:
            return

        self.current_instance = self.instances[name]
        self.current_result = None
        inst = self.current_instance

        info = (
            f"名称：{inst.name}\n"
            f"维度：{inst.dimension}\n"
            f"组数：{inst.num_groups}\n"
            f"容量：{inst.capacity}\n"
            f"Profit/Weight Size：{len(inst.profits)}"
        )
        self._set_text(self.info_text, info)

        for item in self.sort_tree.get_children():
            self.sort_tree.delete(item)
        self._set_text(self.result_text, "")

        self._update_current_instance_label(f"当前实例：{name}")
        self._update_summary("已切换实例，尚未求解")
        self.status_var.set(f"当前实例：{name}")

        if self.auto_plot_var.get():
            self.plot_current_instance()

    def plot_current_instance(self):
        if not self.current_instance:
            messagebox.showwarning("提示", "请先选择实例")
            return

        try:
            self.plot_panel.plot_instance(
                self.current_instance,
                sorted_view=self.sorted_plot_var.get()
            )
            self.status_var.set(f"绘图完成：{self.current_instance.name}")
        except Exception as e:
            messagebox.showerror("绘图错误", str(e))
            self.status_var.set("绘图失败")

    def show_sorted_table(self):
        if not self.current_instance:
            messagebox.showwarning("提示", "请先选择实例")
            return

        for item in self.sort_tree.get_children():
            self.sort_tree.delete(item)

        groups = sort_groups_by_third_ratio(self.current_instance.groups)
        inserted = 0

        for i, g in enumerate(groups[:50], start=1):
            if len(g.items) > 2:
                item3 = g.items[2]
                self.sort_tree.insert(
                    "",
                    tk.END,
                    values=(i, g.group_id, item3.weight, item3.profit, f"{g.third_ratio:.4f}")
                )
                inserted += 1

        self.notebook.select(self.sort_tab)
        self.status_var.set(f"排序预览已更新，共显示 {inserted} 条")
        self._update_summary(f"已生成排序预览，显示 {inserted} 条记录")

    def solve_current_instance(self):
        if not self.current_instance:
            messagebox.showwarning("提示", "请先选择实例")
            return
        if self.is_solving:
            return

        self._set_solving_state(True)
        self.status_var.set("正在求解（DP）...")
        self._update_summary("正在执行动态规划求解...")

        def worker():
            res = None
            err = None
            try:
                res = solve_dkp_dp(
                    self.current_instance,
                    sort_before_solve=self.sorted_solve_var.get()
                )
            except Exception as e:
                err = str(e)

            self.root.after(0, lambda: self._on_solve_done(res, err))

        threading.Thread(target=worker, daemon=True).start()

    def _on_solve_done(self, result, error):
        self._set_solving_state(False)

        if error:
            messagebox.showerror("求解失败", error)
            self.status_var.set("求解失败")
            self._update_summary("求解失败")
            return

        self.current_result = result
        txt = build_result_text(self.current_instance, result)
        self._set_text(self.result_text, txt)
        self.notebook.select(self.result_tab)

        summary = f"最优值：{result.max_profit}    耗时：{result.elapsed_seconds:.4f}s"
        self.status_var.set(f"求解完成：{summary}")
        self._update_summary(summary)

    def save_result(self):
        if not self.current_result:
            messagebox.showwarning("提示", "无结果可保存")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")]
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(build_result_text(self.current_instance, self.current_result))
            messagebox.showinfo("成功", "结果已保存")
            self.status_var.set(f"结果已保存到：{path}")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))
            self.status_var.set("保存失败")


def main():
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()