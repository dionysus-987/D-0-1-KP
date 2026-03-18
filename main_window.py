# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Optional
import threading

from models import DKPInstance, SolveResult
from parser_utils import parse_dkp_instances
from plot_panel import PlotPanel
from solver import sort_groups_by_third_ratio, solve_dkp_dp, build_result_text


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("D{0-1}KP 动态规划求解系统")
        self.root.geometry("1600x920")
        self.root.minsize(1250, 760)

        self.instances: Dict[str, DKPInstance] = {}
        self.current_instance: Optional[DKPInstance] = None
        self.current_result: Optional[SolveResult] = None
        self.is_solving = False

        self.sorted_plot_var = tk.BooleanVar(value=False)
        self.sorted_solve_var = tk.BooleanVar(value=False)
        self.auto_plot_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="就绪 - 请加载数据文件")

        self._setup_styles()
        self._build_ui()
        self._bind_shortcuts()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", font=("Microsoft YaHei", 10))
        style.configure("TButton", padding=(10, 6))
        style.configure("Treeview", rowheight=26)
        style.configure("TLabelframe", padding=6)
        style.configure("TLabelframe.Label", font=("Microsoft YaHei", 10, "bold"))
        style.configure("Title.TLabel", font=("Microsoft YaHei", 10, "bold"))
        style.configure("Status.TLabel", background="#eef2f7")

    def _build_ui(self):
        self._build_menu()

        container = ttk.Frame(self.root, padding=8)
        container.pack(fill=tk.BOTH, expand=True)

        self._build_top_toolbar(container)
        self._build_main_panes(container)
        self._build_status_bar()

    def _build_top_toolbar(self, parent):
        bar = ttk.Frame(parent)
        bar.pack(fill=tk.X, pady=(0, 8))

        ttk.Button(bar, text="打开数据", command=self.load_file).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(bar, text="保存结果", command=self.save_result).pack(side=tk.LEFT, padx=(0, 12))

        ttk.Separator(bar, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=6)

        ttk.Checkbutton(bar, text="绘图按第三项比率排序", variable=self.sorted_plot_var).pack(side=tk.LEFT, padx=6)
        ttk.Checkbutton(bar, text="求解前排序", variable=self.sorted_solve_var).pack(side=tk.LEFT, padx=6)
        ttk.Checkbutton(bar, text="切换实例后自动绘图", variable=self.auto_plot_var).pack(side=tk.LEFT, padx=6)

        ttk.Separator(bar, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=6)

        self.btn_plot_top = ttk.Button(bar, text="绘制散点图", command=self.plot_current_instance)
        self.btn_plot_top.pack(side=tk.LEFT, padx=6)

        self.btn_solve_top = ttk.Button(bar, text="开始求解", command=self.solve_current_instance)
        self.btn_solve_top.pack(side=tk.LEFT, padx=6)

    def _build_main_panes(self, parent):
        main_pane = ttk.Panedwindow(parent, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        self.left_panel = ttk.Frame(main_pane)
        self.center_panel = ttk.Frame(main_pane)
        self.right_panel = ttk.Frame(main_pane)

        main_pane.add(self.left_panel, weight=2)
        main_pane.add(self.center_panel, weight=6)
        main_pane.add(self.right_panel, weight=4)

        self._build_left_panel(self.left_panel)
        self._build_middle_panel(self.center_panel)
        self._build_right_panel(self.right_panel)

    def _build_status_bar(self):
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.progress = ttk.Progressbar(status_frame, mode="indeterminate", length=140)
        self.progress.pack(side=tk.RIGHT, padx=8, pady=4)

        status_bar = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            anchor="w",
            padding=6,
            style="Status.TLabel"
        )
        status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _bind_shortcuts(self):
        self.root.bind("<Control-o>", lambda e: self.load_file())
        self.root.bind("<Control-s>", lambda e: self.save_result())
        self.root.bind("<F5>", lambda e: self.plot_current_instance())
        self.root.bind("<F6>", lambda e: self.solve_current_instance())

    def _build_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="打开数据 (Ctrl+O)", command=self.load_file)
        file_menu.add_command(label="保存结果 (Ctrl+S)", command=self.save_result)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="文件", menu=file_menu)

        action_menu = tk.Menu(menubar, tearoff=0)
        action_menu.add_command(label="绘制散点图 (F5)", command=self.plot_current_instance)
        action_menu.add_command(label="开始求解 (F6)", command=self.solve_current_instance)
        action_menu.add_command(label="显示排序表", command=self.show_sorted_table)
        menubar.add_cascade(label="操作", menu=action_menu)

        self.root.config(menu=menubar)

    def _build_left_panel(self, parent):
        parent.rowconfigure(0, weight=3)
        parent.rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)

        list_frame = ttk.LabelFrame(parent, text="实例列表")
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=(0, 6))
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        list_container = ttk.Frame(list_frame)
        list_container.grid(row=0, column=0, sticky="nsew")
        list_container.rowconfigure(0, weight=1)
        list_container.columnconfigure(0, weight=1)

        self.instance_listbox = tk.Listbox(
            list_container,
            exportselection=False,
            font=("Segoe UI", 10),
            selectbackground="#0078D7",
            activestyle="none",
            relief=tk.FLAT
        )
        self.instance_listbox.grid(row=0, column=0, sticky="nsew")

        list_scroll = ttk.Scrollbar(list_container, orient="vertical", command=self.instance_listbox.yview)
        list_scroll.grid(row=0, column=1, sticky="ns")
        self.instance_listbox.config(yscrollcommand=list_scroll.set)

        self.instance_listbox.bind("<<ListboxSelect>>", self.on_instance_changed)
        self.instance_listbox.bind("<Double-Button-1>", lambda e: self.plot_current_instance())

        info_frame = ttk.LabelFrame(parent, text="基本信息")
        info_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        info_frame.rowconfigure(0, weight=1)
        info_frame.columnconfigure(0, weight=1)

        self.info_text = tk.Text(
            info_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Consolas", 10),
            bg="#fafafa",
            relief=tk.FLAT,
            padx=8,
            pady=8
        )
        self.info_text.grid(row=0, column=0, sticky="nsew")

    def _build_middle_panel(self, parent):
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        frame = ttk.LabelFrame(parent, text="数据可视化")
        frame.grid(row=0, column=0, sticky="nsew", pady=(0, 0))
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)

        toolbar = ttk.Frame(frame)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        ttk.Label(toolbar, text="当前分析区", style="Title.TLabel").pack(side=tk.LEFT, padx=(4, 12))
        ttk.Button(toolbar, text="刷新图像", command=self.plot_current_instance).pack(side=tk.LEFT, padx=4)

        plot_container = ttk.Frame(frame)
        plot_container.grid(row=1, column=0, sticky="nsew")
        plot_container.rowconfigure(0, weight=1)
        plot_container.columnconfigure(0, weight=1)

        self.plot_panel = PlotPanel(plot_container)
        self.plot_panel.pack(fill=tk.BOTH, expand=True)

    def _build_right_panel(self, parent):
        parent.rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)

        # 参数与操作区
        control_frame = ttk.LabelFrame(parent, text="参数与操作")
        control_frame.grid(row=0, column=0, sticky="ew", padx=(6, 0), pady=(0, 6))
        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)

        ttk.Checkbutton(
            control_frame, text="求解前排序", variable=self.sorted_solve_var
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=2)

        ttk.Button(
            control_frame, text="显示排序预览", command=self.show_sorted_table
        ).grid(row=1, column=0, sticky="ew", padx=2, pady=4)

        self.btn_solve = ttk.Button(
            control_frame, text="开始求解", command=self.solve_current_instance
        )
        self.btn_solve.grid(row=1, column=1, sticky="ew", padx=2, pady=4)

        ttk.Button(
            control_frame, text="保存结果", command=self.save_result
        ).grid(row=2, column=0, columnspan=2, sticky="ew", padx=2, pady=4)

        # Notebook 结果区
        notebook = ttk.Notebook(parent)
        notebook.grid(row=1, column=0, sticky="nsew", padx=(6, 0))

        sort_tab = ttk.Frame(notebook)
        result_tab = ttk.Frame(notebook)
        notebook.add(sort_tab, text="排序预览")
        notebook.add(result_tab, text="求解结果")

        self._build_sort_tab(sort_tab)
        self._build_result_tab(result_tab)

    def _build_sort_tab(self, parent):
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        columns = ("idx", "gid", "w3", "p3", "ratio")
        self.sort_tree = ttk.Treeview(parent, columns=columns, show="headings")
        self.sort_tree.grid(row=0, column=0, sticky="nsew")

        headers = {
            "idx": "序号",
            "gid": "组号",
            "w3": "重量3",
            "p3": "价值3",
            "ratio": "价值/重量"
        }
        widths = {
            "idx": 60,
            "gid": 70,
            "w3": 90,
            "p3": 90,
            "ratio": 110
        }

        for col in columns:
            self.sort_tree.heading(col, text=headers[col])
            self.sort_tree.column(col, width=widths[col], anchor="center", stretch=True)

        yscroll = ttk.Scrollbar(parent, orient="vertical", command=self.sort_tree.yview)
        yscroll.grid(row=0, column=1, sticky="ns")
        self.sort_tree.configure(yscrollcommand=yscroll.set)

    def _build_result_tab(self, parent):
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        result_container = ttk.Frame(parent)
        result_container.grid(row=0, column=0, sticky="nsew")
        result_container.rowconfigure(0, weight=1)
        result_container.columnconfigure(0, weight=1)

        self.result_text = tk.Text(
            result_container,
            wrap=tk.NONE,
            state=tk.DISABLED,
            font=("Consolas", 10),
            bg="#f9f9f9",
            relief=tk.FLAT,
            padx=8,
            pady=8
        )
        self.result_text.grid(row=0, column=0, sticky="nsew")

        yscroll = ttk.Scrollbar(result_container, orient="vertical", command=self.result_text.yview)
        yscroll.grid(row=0, column=1, sticky="ns")
        self.result_text.configure(yscrollcommand=yscroll.set)

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
        self.btn_plot_top.config(state=state if solving else "normal")
        self.instance_listbox.config(state=state)

        if solving:
            self.root.config(cursor="watch")
            self.progress.start(10)
        else:
            self.root.config(cursor="")
            self.progress.stop()

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

            self.instance_listbox.delete(0, tk.END)
            for name in self.instances:
                self.instance_listbox.insert(tk.END, name)

            self.current_instance = None
            self.current_result = None
            self._set_text(self.info_text, "")
            self._set_text(self.result_text, "")

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

        self.status_var.set(f"排序预览已更新，共显示 {inserted} 条")

    def solve_current_instance(self):
        if not self.current_instance:
            messagebox.showwarning("提示", "请先选择实例")
            return
        if self.is_solving:
            return

        self._set_solving_state(True)
        self.status_var.set("正在求解（DP）...")

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
            return

        self.current_result = result
        txt = build_result_text(self.current_instance, result)
        self._set_text(self.result_text, txt)
        self.status_var.set(
            f"求解完成：最优值={result.max_profit}，耗时={result.elapsed_seconds:.4f}s"
        )

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