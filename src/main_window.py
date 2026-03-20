# -*- coding: utf-8 -*-
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, List, Optional

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from models import DKPInstance, InstanceExperimentResult
from parser_utils import parse_dkp_instances
from plot_panel import PlotPanel

from algorithms.dp_solver import DPSolver, sort_groups_by_third_ratio
from algorithms.greedy_ratio import GreedyRatioSolver
from algorithms.greedy_third_ratio import GreedyThirdRatioSolver

from experiment.runner import ExperimentRunner
from experiment.exporter import (
    export_results_to_csv,
    export_results_to_txt,
    build_experiment_text,
)


class MainWindow:
    BG = "#f5f7fb"
    CARD_BG = "#ffffff"
    INPUT_BG = "#fbfcfe"
    TEXT = "#1f2937"
    SUBTEXT = "#5b6472"
    BORDER = "#d7deea"
    ACCENT = "#2f6fed"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("D{0-1}KP 算法比较实验系统")
        self.root.geometry("1780x980")
        self.root.minsize(1380, 780)
        self.root.configure(bg=self.BG)

        self.instances: Dict[str, DKPInstance] = {}
        self.filtered_names: List[str] = []
        self.current_instance: Optional[DKPInstance] = None

        self.current_file_path: str = ""
        self.is_running = False

        # 当前实验结果
        self.current_instance_experiment: Optional[InstanceExperimentResult] = None
        self.last_experiment_results: List[InstanceExperimentResult] = []

        # UI 状态
        self.sorted_plot_var = tk.BooleanVar(value=False)
        self.auto_plot_var = tk.BooleanVar(value=True)

        self.alg_dp_var = tk.BooleanVar(value=True)
        self.alg_dp_sorted_var = tk.BooleanVar(value=True)
        self.alg_greedy_ratio_var = tk.BooleanVar(value=True)
        self.alg_greedy_third_var = tk.BooleanVar(value=True)

        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="就绪")
        self.summary_var = tk.StringVar(value="尚未运行实验")
        self.current_name_var = tk.StringVar(value="未选择实例")
        self.instance_count_var = tk.StringVar(value="实例数：0")
        self.loaded_file_var = tk.StringVar(value="未加载文件")

        self._setup_styles()
        self._build_ui()
        self._bind_events()

    # =========================
    # 样式
    # =========================
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("xpnative")

        style.configure(
            ".",
            font=("Microsoft YaHei", 10),
            background=self.BG,
            foreground=self.TEXT
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
        style.configure("TButton", padding=(10, 6))

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

    # =========================
    # 通用组件
    # =========================
    def _create_card(self, parent):
        return tk.Frame(
            parent,
            bg=self.CARD_BG,
            bd=1,
            relief="solid",
            highlightthickness=0
        )

    def _section_title(self, parent, text):
        return tk.Label(
            parent,
            text=text,
            bg=self.CARD_BG,
            fg=self.TEXT,
            font=("Microsoft YaHei", 10, "bold")
        )

    def _section_info(self, parent, textvariable=None, text=None):
        return tk.Label(
            parent,
            text=text if text is not None else "",
            textvariable=textvariable,
            bg=self.CARD_BG,
            fg=self.SUBTEXT,
            font=("Microsoft YaHei", 9)
        )

    def _set_text(self, text_widget: tk.Text, content: str):
        text_widget.config(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)
        text_widget.insert(tk.END, content)
        text_widget.config(state=tk.DISABLED)

    # =========================
    # UI 构建
    # =========================
    def _build_ui(self):
        self._build_top_header()
        self._build_toolbar()
        self._build_main_area()
        self._build_statusbar()

    def _build_top_header(self):
        wrapper = tk.Frame(self.root, bg=self.BG)
        wrapper.pack(fill=tk.X, padx=10, pady=(10, 6))

        card = self._create_card(wrapper)
        card.pack(fill=tk.X)

        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=0)

        left = tk.Frame(card, bg=self.CARD_BG)
        left.grid(row=0, column=0, sticky="w", padx=16, pady=12)

        title = tk.Label(
            left,
            text="D{0-1}KP 算法比较实验系统",
            bg=self.CARD_BG,
            fg=self.TEXT,
            font=("Microsoft YaHei", 16, "bold")
        )
        title.pack(anchor="w")

        subtitle = tk.Label(
            left,
            text="实例管理、散点可视化、单实例比较、批量实验、CSV/TXT 导出",
            bg=self.CARD_BG,
            fg=self.SUBTEXT,
            font=("Microsoft YaHei", 10)
        )
        subtitle.pack(anchor="w", pady=(3, 0))

        right = tk.Frame(card, bg=self.CARD_BG)
        right.grid(row=0, column=1, sticky="e", padx=16, pady=12)

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
            font=("Microsoft YaHei", 9),
            justify="right"
        ).pack(anchor="e", pady=(4, 0))

    def _build_toolbar(self):
        wrapper = tk.Frame(self.root, bg=self.BG)
        wrapper.pack(fill=tk.X, padx=10, pady=(0, 8))

        bar = self._create_card(wrapper)
        bar.pack(fill=tk.X)

        left = tk.Frame(bar, bg=self.CARD_BG)
        left.pack(side=tk.LEFT, padx=12, pady=10)

        ttk.Button(
            left, text="打开数据", command=self.load_file, style="Primary.TButton"
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(
            left, text="运行当前实例", command=self.run_current_instance_experiment, style="Primary.TButton"
        ).pack(side=tk.LEFT, padx=4)

        ttk.Button(
            left, text="批量实验(全部实例)", command=self.run_batch_experiment, style="Primary.TButton"
        ).pack(side=tk.LEFT, padx=4)

        ttk.Button(
            left, text="导出 CSV", command=self.export_csv, style="Secondary.TButton"
        ).pack(side=tk.LEFT, padx=(12, 4))

        ttk.Button(
            left, text="导出 TXT", command=self.export_txt, style="Secondary.TButton"
        ).pack(side=tk.LEFT, padx=4)

        ttk.Button(
            left, text="绘制散点图", command=self.plot_current_instance, style="Secondary.TButton"
        ).pack(side=tk.LEFT, padx=(12, 4))

        ttk.Button(
            left, text="排序预览", command=self.show_sorted_table, style="Secondary.TButton"
        ).pack(side=tk.LEFT, padx=4)

        right = tk.Frame(bar, bg=self.CARD_BG)
        right.pack(side=tk.RIGHT, padx=12, pady=10)

        ttk.Checkbutton(
            right, text="绘图按第三项比率排序", variable=self.sorted_plot_var
        ).pack(side=tk.LEFT, padx=8)

        ttk.Checkbutton(
            right, text="切换实例自动绘图", variable=self.auto_plot_var
        ).pack(side=tk.LEFT, padx=8)

    def _build_main_area(self):
        outer = tk.Frame(self.root, bg=self.BG)
        outer.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        paned = ttk.Panedwindow(outer, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        self.left_panel = tk.Frame(paned, bg=self.BG)
        self.center_panel = tk.Frame(paned, bg=self.BG)
        self.right_panel = tk.Frame(paned, bg=self.BG)

        paned.add(self.left_panel, weight=22)
        paned.add(self.center_panel, weight=40)
        paned.add(self.right_panel, weight=38)

        self._build_left_panel()
        self._build_center_panel()
        self._build_right_panel()

    def _build_left_panel(self):
        self.left_panel.rowconfigure(2, weight=1)
        self.left_panel.columnconfigure(0, weight=1)

        # 文件信息
        file_card = self._create_card(self.left_panel)
        file_card.grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=(0, 8))
        file_card.columnconfigure(0, weight=1)

        self._section_title(file_card, "数据文件").grid(
            row=0, column=0, sticky="w", padx=12, pady=(12, 2)
        )
        self._section_info(file_card, textvariable=self.loaded_file_var).grid(
            row=1, column=0, sticky="w", padx=12, pady=(0, 10)
        )

        # 搜索
        search_card = self._create_card(self.left_panel)
        search_card.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=(0, 8))
        search_card.columnconfigure(0, weight=1)

        self._section_title(search_card, "实例导航").grid(
            row=0, column=0, sticky="w", padx=12, pady=(12, 2)
        )
        self._section_info(search_card, textvariable=self.instance_count_var).grid(
            row=1, column=0, sticky="w", padx=12, pady=(0, 8)
        )

        self.search_entry = tk.Entry(
            search_card,
            textvariable=self.search_var,
            relief="flat",
            bg=self.INPUT_BG,
            fg=self.TEXT,
            insertbackground=self.TEXT,
            font=("Microsoft YaHei", 10)
        )
        self.search_entry.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12), ipady=6)

        # 实例列表
        list_card = self._create_card(self.left_panel)
        list_card.grid(row=2, column=0, sticky="nsew", padx=(0, 6), pady=(0, 8))
        list_card.rowconfigure(1, weight=1)
        list_card.columnconfigure(0, weight=1)

        self._section_title(list_card, "实例列表").grid(
            row=0, column=0, sticky="w", padx=12, pady=(12, 0)
        )

        list_container = tk.Frame(list_card, bg=self.CARD_BG)
        list_container.grid(row=1, column=0, sticky="nsew", padx=12, pady=(8, 12))
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
            bg=self.INPUT_BG,
            fg=self.TEXT,
            highlightthickness=0,
            bd=0
        )
        self.instance_listbox.grid(row=0, column=0, sticky="nsew")

        list_scroll = ttk.Scrollbar(
            list_container, orient="vertical", command=self.instance_listbox.yview
        )
        list_scroll.grid(row=0, column=1, sticky="ns")
        self.instance_listbox.config(yscrollcommand=list_scroll.set)

        # 实例信息
        info_card = self._create_card(self.left_panel)
        info_card.grid(row=3, column=0, sticky="ew", padx=(0, 6))
        info_card.rowconfigure(1, weight=1)
        info_card.columnconfigure(0, weight=1)

        self._section_title(info_card, "实例信息").grid(
            row=0, column=0, sticky="w", padx=12, pady=(12, 0)
        )

        self.info_text = tk.Text(
            info_card,
            height=8,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Consolas", 10),
            bg=self.INPUT_BG,
            fg=self.TEXT,
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=6,
            pady=6
        )
        self.info_text.grid(row=1, column=0, sticky="nsew", padx=12, pady=(8, 12))

    def _build_center_panel(self):
        self.center_panel.rowconfigure(0, weight=0)
        self.center_panel.rowconfigure(1, weight=1)
        self.center_panel.columnconfigure(0, weight=1)

        # 算法选择
        alg_card = self._create_card(self.center_panel)
        alg_card.grid(row=0, column=0, sticky="ew", padx=6, pady=(0, 8))
        alg_card.columnconfigure(0, weight=1)

        self._section_title(alg_card, "算法选择").grid(
            row=0, column=0, sticky="w", padx=12, pady=(12, 4)
        )
        self._section_info(alg_card, text="勾选后参与当前实例运行和批量实验").grid(
            row=1, column=0, sticky="w", padx=12, pady=(0, 8)
        )

        options = tk.Frame(alg_card, bg=self.CARD_BG)
        options.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))

        ttk.Checkbutton(options, text="DP", variable=self.alg_dp_var).pack(side=tk.LEFT, padx=8)
        ttk.Checkbutton(options, text="DP + Sorted", variable=self.alg_dp_sorted_var).pack(side=tk.LEFT, padx=8)
        ttk.Checkbutton(options, text="GreedyRatio", variable=self.alg_greedy_ratio_var).pack(side=tk.LEFT, padx=8)
        ttk.Checkbutton(options, text="GreedyThirdRatio", variable=self.alg_greedy_third_var).pack(side=tk.LEFT, padx=8)

        # 左侧图形 notebook
        plot_card = self._create_card(self.center_panel)
        plot_card.grid(row=1, column=0, sticky="nsew", padx=6)
        plot_card.rowconfigure(1, weight=1)
        plot_card.columnconfigure(0, weight=1)

        top = tk.Frame(plot_card, bg=self.CARD_BG)
        top.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 0))

        self._section_title(top, "可视化").pack(side=tk.LEFT)
        self._section_info(top, text="实例散点图 / 算法比较图").pack(side=tk.LEFT, padx=(10, 0))

        self.visual_notebook = ttk.Notebook(plot_card)
        self.visual_notebook.grid(row=1, column=0, sticky="nsew", padx=12, pady=(10, 12))

        self.scatter_tab = tk.Frame(self.visual_notebook, bg=self.CARD_BG)
        self.compare_plot_tab = tk.Frame(self.visual_notebook, bg=self.CARD_BG)
        self.visual_notebook.add(self.scatter_tab, text="散点图")
        self.visual_notebook.add(self.compare_plot_tab, text="对比图")

        self.scatter_tab.rowconfigure(0, weight=1)
        self.scatter_tab.columnconfigure(0, weight=1)
        self.compare_plot_tab.rowconfigure(0, weight=1)
        self.compare_plot_tab.columnconfigure(0, weight=1)

        plot_wrap = tk.Frame(self.scatter_tab, bg=self.CARD_BG)
        plot_wrap.grid(row=0, column=0, sticky="nsew")
        plot_wrap.rowconfigure(0, weight=1)
        plot_wrap.columnconfigure(0, weight=1)

        self.plot_panel = PlotPanel(plot_wrap)
        self.plot_panel.pack(fill=tk.BOTH, expand=True)

        self.compare_figure = Figure(figsize=(6, 5), tight_layout=True)
        self.compare_ax = self.compare_figure.add_subplot(111)
        self.compare_canvas = FigureCanvasTkAgg(self.compare_figure, master=self.compare_plot_tab)
        self.compare_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self._clear_compare_plot()

    def _build_right_panel(self):
        self.right_panel.rowconfigure(1, weight=1)
        self.right_panel.columnconfigure(0, weight=1)

        control_card = self._create_card(self.right_panel)
        control_card.grid(row=0, column=0, sticky="ew", padx=(6, 0), pady=(0, 8))
        control_card.columnconfigure(0, weight=1)
        control_card.columnconfigure(1, weight=1)

        self._section_title(control_card, "实验控制").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(12, 0)
        )

        ttk.Button(
            control_card,
            text="运行当前实例",
            command=self.run_current_instance_experiment,
            style="Primary.TButton"
        ).grid(row=1, column=0, sticky="ew", padx=(12, 6), pady=(10, 4))

        ttk.Button(
            control_card,
            text="批量实验(全部实例)",
            command=self.run_batch_experiment,
            style="Primary.TButton"
        ).grid(row=1, column=1, sticky="ew", padx=(6, 12), pady=(10, 4))

        ttk.Button(
            control_card,
            text="导出 CSV",
            command=self.export_csv,
            style="Secondary.TButton"
        ).grid(row=2, column=0, sticky="ew", padx=(12, 6), pady=(4, 4))

        ttk.Button(
            control_card,
            text="导出 TXT",
            command=self.export_txt,
            style="Secondary.TButton"
        ).grid(row=2, column=1, sticky="ew", padx=(6, 12), pady=(4, 4))

        summary_box = tk.Frame(control_card, bg="#f8fafc", bd=1, relief="solid")
        summary_box.grid(row=3, column=0, columnspan=2, sticky="ew", padx=12, pady=(8, 12))

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

        notebook_card = self._create_card(self.right_panel)
        notebook_card.grid(row=1, column=0, sticky="nsew", padx=(6, 0))
        notebook_card.rowconfigure(1, weight=1)
        notebook_card.columnconfigure(0, weight=1)

        self._section_title(notebook_card, "结果面板").grid(
            row=0, column=0, sticky="w", padx=12, pady=(12, 0)
        )

        self.notebook = ttk.Notebook(notebook_card)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=12, pady=(10, 12))

        self.sort_tab = tk.Frame(self.notebook, bg=self.CARD_BG)
        self.table_tab = tk.Frame(self.notebook, bg=self.CARD_BG)
        self.result_tab = tk.Frame(self.notebook, bg=self.CARD_BG)

        self.notebook.add(self.sort_tab, text="排序预览")
        self.notebook.add(self.table_tab, text="结果表格")
        self.notebook.add(self.result_tab, text="结果文本")

        self._build_sort_tab()
        self._build_table_tab()
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

    def _build_table_tab(self):
        self.table_tab.rowconfigure(0, weight=1)
        self.table_tab.columnconfigure(0, weight=1)

        wrap = tk.Frame(self.table_tab, bg=self.CARD_BG)
        wrap.grid(row=0, column=0, sticky="nsew")
        wrap.rowconfigure(0, weight=1)
        wrap.columnconfigure(0, weight=1)

        columns = (
            "instance",
            "algorithm",
            "value",
            "weight",
            "time",
            "gap",
            "optimal",
            "success",
        )
        self.result_tree = ttk.Treeview(wrap, columns=columns, show="headings")

        headers = {
            "instance": "实例",
            "algorithm": "算法",
            "value": "value",
            "weight": "weight",
            "time": "time(s)",
            "gap": "gap",
            "optimal": "optimal",
            "success": "success",
        }
        widths = {
            "instance": 110,
            "algorithm": 140,
            "value": 90,
            "weight": 90,
            "time": 100,
            "gap": 90,
            "optimal": 80,
            "success": 80,
        }

        for col in columns:
            self.result_tree.heading(col, text=headers[col])
            self.result_tree.column(col, width=widths[col], anchor="center", stretch=True)

        self.result_tree.grid(row=0, column=0, sticky="nsew")

        yscroll = ttk.Scrollbar(wrap, orient="vertical", command=self.result_tree.yview)
        yscroll.grid(row=0, column=1, sticky="ns")
        self.result_tree.config(yscrollcommand=yscroll.set)

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
            bg=self.INPUT_BG,
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
        wrapper = tk.Frame(self.root, bg=self.BG)
        wrapper.pack(fill=tk.X, padx=10, pady=(0, 10))

        bar = self._create_card(wrapper)
        bar.pack(fill=tk.X)

        left = tk.Frame(bar, bg=self.CARD_BG)
        left.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=12, pady=8)

        tk.Label(
            left,
            textvariable=self.status_var,
            bg=self.CARD_BG,
            fg=self.SUBTEXT,
            font=("Microsoft YaHei", 9)
        ).pack(side=tk.LEFT)

        right = tk.Frame(bar, bg=self.CARD_BG)
        right.pack(side=tk.RIGHT, padx=12, pady=8)

        self.progress = ttk.Progressbar(right, mode="indeterminate", length=160)
        self.progress.pack(side=tk.RIGHT)

    # =========================
    # 事件绑定
    # =========================
    def _bind_events(self):
        self.root.bind("<Control-o>", lambda e: self.load_file())
        self.root.bind("<Control-e>", lambda e: self.run_current_instance_experiment())
        self.root.bind("<Control-b>", lambda e: self.run_batch_experiment())
        self.root.bind("<Control-1>", lambda e: self.export_csv())
        self.root.bind("<Control-2>", lambda e: self.export_txt())
        self.root.bind("<F5>", lambda e: self.plot_current_instance())

        self.instance_listbox.bind("<<ListboxSelect>>", self.on_instance_changed)
        self.instance_listbox.bind("<Double-Button-1>", lambda e: self.run_current_instance_experiment())
        self.search_var.trace_add("write", lambda *args: self._filter_instance_list())

    # =========================
    # 状态管理
    # =========================
    def _set_running_state(self, running: bool):
        self.is_running = running
        state = "disabled" if running else "normal"

        self.instance_listbox.config(state=state)
        self.search_entry.config(state=state)

        if running:
            self.root.config(cursor="watch")
            self.progress.start(10)
        else:
            self.root.config(cursor="")
            self.progress.stop()

    def _update_summary(self, text: str):
        self.summary_var.set(text)

    def _clear_compare_plot(self):
        self.compare_ax.clear()
        self.compare_ax.set_title("算法对比图")
        self.compare_ax.set_xlabel("Algorithm")
        self.compare_ax.set_ylabel("Value")
        self.compare_ax.grid(True, linestyle="--", alpha=0.4)
        self.compare_canvas.draw()

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
    # 核心业务
    # =========================
    def _get_selected_solvers(self):
        solvers = []

        if self.alg_dp_var.get():
            solvers.append(DPSolver(sort_before_solve=False))
        if self.alg_dp_sorted_var.get():
            solvers.append(DPSolver(sort_before_solve=True))
        if self.alg_greedy_ratio_var.get():
            solvers.append(GreedyRatioSolver())
        if self.alg_greedy_third_var.get():
            solvers.append(GreedyThirdRatioSolver())

        return solvers

    def _ensure_solvers_selected(self) -> bool:
        if self._get_selected_solvers():
            return True
        messagebox.showwarning("提示", "请至少勾选一个算法")
        return False

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
            self.current_file_path = file_path
            self.loaded_file_var.set(os.path.basename(file_path))

            self.search_var.set("")
            self.filtered_names = list(self.instances.keys())

            self.instance_listbox.delete(0, tk.END)
            for name in self.filtered_names:
                self.instance_listbox.insert(tk.END, name)

            self.instance_count_var.set(f"实例数：{len(self.filtered_names)}")
            self.current_instance = None
            self.current_instance_experiment = None
            self.last_experiment_results = []

            self._set_text(self.info_text, "")
            self._set_text(self.result_text, "")
            self.current_name_var.set("未选择实例")
            self._update_summary("文件已加载，尚未运行实验")

            for item in self.sort_tree.get_children():
                self.sort_tree.delete(item)
            for item in self.result_tree.get_children():
                self.result_tree.delete(item)

            self._clear_compare_plot()

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
        inst = self.current_instance
        self.current_instance_experiment = None

        info = (
            f"名称：{inst.name}\n"
            f"维度：{inst.dimension}\n"
            f"组数：{inst.num_groups}\n"
            f"容量：{inst.capacity}\n"
            f"Profit 数量：{len(inst.profits)}\n"
            f"Weight 数量：{len(inst.weights)}"
        )
        self._set_text(self.info_text, info)

        for item in self.sort_tree.get_children():
            self.sort_tree.delete(item)
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        self._set_text(self.result_text, "")
        self._clear_compare_plot()

        self.current_name_var.set(f"当前实例：{name}")
        self._update_summary("已切换实例，尚未运行实验")
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
            self.visual_notebook.select(self.scatter_tab)
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

        for i, g in enumerate(groups[:100], start=1):
            if len(g.items) > 2:
                item3 = g.items[2]
                self.sort_tree.insert(
                    "",
                    tk.END,
                    values=(i, g.group_id, item3.weight, item3.profit, f"{g.third_ratio:.6f}")
                )
                inserted += 1

        self.notebook.select(self.sort_tab)
        self.status_var.set(f"排序预览已更新，共显示 {inserted} 条")
        self._update_summary(f"已生成排序预览，显示 {inserted} 条记录")

    def run_current_instance_experiment(self):
        if not self.current_instance:
            messagebox.showwarning("提示", "请先选择实例")
            return
        if self.is_running:
            return
        if not self._ensure_solvers_selected():
            return

        self._set_running_state(True)
        self.status_var.set("正在运行当前实例实验...")
        self._update_summary("正在执行当前实例多算法比较...")

        instance = self.current_instance
        solvers = self._get_selected_solvers()

        def worker():
            exp_result = None
            err = None
            try:
                runner = ExperimentRunner(solvers)
                exp_result = runner.run_instance(instance)
            except Exception as e:
                err = str(e)

            self.root.after(0, lambda: self._on_single_experiment_done(exp_result, err))

        threading.Thread(target=worker, daemon=True).start()

    def _on_single_experiment_done(self, exp_result: Optional[InstanceExperimentResult], error: Optional[str]):
        self._set_running_state(False)

        if error:
            messagebox.showerror("实验失败", error)
            self.status_var.set("实验失败")
            self._update_summary("实验失败")
            return

        if exp_result is None:
            messagebox.showerror("实验失败", "未返回实验结果")
            self.status_var.set("实验失败")
            self._update_summary("实验失败")
            return

        self.current_instance_experiment = exp_result
        self.last_experiment_results = [exp_result]

        self._refresh_result_tree(self.last_experiment_results)
        self._refresh_result_text(self.last_experiment_results)
        self._refresh_compare_plot_for_instance(exp_result)

        valid = [r for r in exp_result.results if r.success]
        if valid:
            best = max(valid, key=lambda x: x.value)
            summary = f"{exp_result.instance_name} 最优={best.value}，最佳算法={best.algorithm_name}，算法数={len(valid)}"
        else:
            summary = f"{exp_result.instance_name} 无成功结果"

        self.notebook.select(self.table_tab)
        self.visual_notebook.select(self.compare_plot_tab)
        self.status_var.set("当前实例实验完成")
        self._update_summary(summary)

    def run_batch_experiment(self):
        if not self.instances:
            messagebox.showwarning("提示", "请先加载数据文件")
            return
        if self.is_running:
            return
        if not self._ensure_solvers_selected():
            return

        self._set_running_state(True)
        self.status_var.set("正在运行批量实验...")
        self._update_summary("正在对当前文件全部实例执行多算法批量实验...")

        instances = dict(self.instances)
        solvers = self._get_selected_solvers()

        def worker():
            all_results = None
            err = None
            try:
                runner = ExperimentRunner(solvers)
                all_results = runner.run_all(instances)
            except Exception as e:
                err = str(e)

            self.root.after(0, lambda: self._on_batch_experiment_done(all_results, err))

        threading.Thread(target=worker, daemon=True).start()

    def _on_batch_experiment_done(self, all_results: Optional[List[InstanceExperimentResult]], error: Optional[str]):
        self._set_running_state(False)

        if error:
            messagebox.showerror("批量实验失败", error)
            self.status_var.set("批量实验失败")
            self._update_summary("批量实验失败")
            return

        if all_results is None:
            messagebox.showerror("批量实验失败", "未返回实验结果")
            self.status_var.set("批量实验失败")
            self._update_summary("批量实验失败")
            return

        self.last_experiment_results = all_results

        # 如果当前实例存在，尝试定位其单实例结果
        current_name = self.current_instance.name if self.current_instance else None
        self.current_instance_experiment = None
        if current_name is not None:
            for exp in all_results:
                if exp.instance_name == current_name:
                    self.current_instance_experiment = exp
                    break

        self._refresh_result_tree(all_results)
        self._refresh_result_text(all_results)
        self._refresh_compare_plot_for_batch(all_results)

        instance_count = len(all_results)
        algo_rows = sum(len(exp.results) for exp in all_results)
        summary = f"批量实验完成：实例数={instance_count}，结果行数={algo_rows}"

        self.notebook.select(self.table_tab)
        self.visual_notebook.select(self.compare_plot_tab)
        self.status_var.set(summary)
        self._update_summary(summary)

    # =========================
    # 结果刷新
    # =========================
    def _refresh_result_tree(self, experiment_results: List[InstanceExperimentResult]):
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

        for exp in experiment_results:
            for r in exp.results:
                gap_str = "" if r.gap is None else f"{r.gap:.6f}"
                time_str = f"{r.time_seconds:.6f}"
                optimal_str = "" if r.optimal is None else str(r.optimal)
                self.result_tree.insert(
                    "",
                    tk.END,
                    values=(
                        r.instance_name,
                        r.algorithm_name,
                        r.value,
                        r.weight,
                        time_str,
                        gap_str,
                        optimal_str,
                        str(r.success),
                    )
                )

    def _refresh_result_text(self, experiment_results: List[InstanceExperimentResult]):
        text = build_experiment_text(experiment_results)
        self._set_text(self.result_text, text)

    def _refresh_compare_plot_for_instance(self, exp_result: InstanceExperimentResult):
        self.compare_ax.clear()

        valid = [r for r in exp_result.results if r.success]
        if not valid:
            self._clear_compare_plot()
            return

        names = [r.algorithm_name for r in valid]
        values = [r.value for r in valid]
        times = [r.time_seconds for r in valid]

        x = list(range(len(names)))

        self.compare_ax.bar(x, values)
        self.compare_ax.set_xticks(x)
        self.compare_ax.set_xticklabels(names, rotation=20)
        self.compare_ax.set_title(f"{exp_result.instance_name} - 算法 value 对比")
        self.compare_ax.set_xlabel("Algorithm")
        self.compare_ax.set_ylabel("Value")
        self.compare_ax.grid(True, linestyle="--", alpha=0.35)

        ax2 = self.compare_ax.twinx()
        ax2.plot(x, times, marker="o")
        ax2.set_ylabel("Time(s)")

        for i, (v, t) in enumerate(zip(values, times)):
            self.compare_ax.text(i, v, str(v), ha="center", va="bottom", fontsize=9)
            ax2.text(i, t, f"{t:.4f}", ha="center", va="bottom", fontsize=8)

        self.compare_canvas.draw()

    def _refresh_compare_plot_for_batch(self, experiment_results: List[InstanceExperimentResult]):
        self.compare_ax.clear()

        agg = {}
        for exp in experiment_results:
            for r in exp.results:
                if not r.success:
                    continue
                if r.algorithm_name not in agg:
                    agg[r.algorithm_name] = {"values": [], "times": [], "gaps": []}
                agg[r.algorithm_name]["values"].append(r.value)
                agg[r.algorithm_name]["times"].append(r.time_seconds)
                if r.gap is not None:
                    agg[r.algorithm_name]["gaps"].append(r.gap)

        if not agg:
            self._clear_compare_plot()
            return

        names = list(agg.keys())
        avg_values = [
            sum(agg[name]["values"]) / len(agg[name]["values"]) if agg[name]["values"] else 0.0
            for name in names
        ]
        avg_times = [
            sum(agg[name]["times"]) / len(agg[name]["times"]) if agg[name]["times"] else 0.0
            for name in names
        ]

        x = list(range(len(names)))

        self.compare_ax.bar(x, avg_values)
        self.compare_ax.set_xticks(x)
        self.compare_ax.set_xticklabels(names, rotation=20)
        self.compare_ax.set_title("批量实验 - 平均 value / 平均 time 对比")
        self.compare_ax.set_xlabel("Algorithm")
        self.compare_ax.set_ylabel("Average Value")
        self.compare_ax.grid(True, linestyle="--", alpha=0.35)

        ax2 = self.compare_ax.twinx()
        ax2.plot(x, avg_times, marker="o")
        ax2.set_ylabel("Average Time(s)")

        for i, (v, t) in enumerate(zip(avg_values, avg_times)):
            self.compare_ax.text(i, v, f"{v:.2f}", ha="center", va="bottom", fontsize=9)
            ax2.text(i, t, f"{t:.4f}", ha="center", va="bottom", fontsize=8)

        self.compare_canvas.draw()

    # =========================
    # 导出
    # =========================
    def export_csv(self):
        if not self.last_experiment_results:
            messagebox.showwarning("提示", "无实验结果可导出")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")]
        )
        if not path:
            return

        try:
            export_results_to_csv(self.last_experiment_results, path)
            messagebox.showinfo("成功", "CSV 导出完成")
            self.status_var.set(f"CSV 已导出：{path}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))
            self.status_var.set("CSV 导出失败")

    def export_txt(self):
        if not self.last_experiment_results:
            messagebox.showwarning("提示", "无实验结果可导出")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")]
        )
        if not path:
            return

        try:
            export_results_to_txt(self.last_experiment_results, path)
            messagebox.showinfo("成功", "TXT 导出完成")
            self.status_var.set(f"TXT 已导出：{path}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))
            self.status_var.set("TXT 导出失败")


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