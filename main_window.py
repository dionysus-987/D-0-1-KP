# -*- coding: utf-8 -*-
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Optional

from models import DKPInstance, SolveResult
from parser_utils import parse_dkp_instances
from plot_panel import PlotPanel
from solver import sort_groups_by_third_ratio, solve_dkp_dp, build_result_text


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("D{0-1}KP 动态规划求解系统（Tkinter版）")
        self.root.geometry("1450x860")

        self.instances: Dict[str, DKPInstance] = {}
        self.current_instance: Optional[DKPInstance] = None
        self.current_result: Optional[SolveResult] = None

        self.sorted_plot_var = tk.BooleanVar(value=False)
        self.sorted_solve_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="就绪")

        self._build_ui()

    def _build_ui(self):
        self._build_menu()

        main_frame = ttk.Frame(self.root, padding=8)
        main_frame.pack(fill=tk.BOTH, expand=True)

        main_frame.columnconfigure(0, weight=2)
        main_frame.columnconfigure(1, weight=4)
        main_frame.columnconfigure(2, weight=4)
        main_frame.rowconfigure(0, weight=1)

        self._build_left_panel(main_frame)
        self._build_middle_panel(main_frame)
        self._build_right_panel(main_frame)

        status_bar = ttk.Label(
            self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w", padding=4
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _build_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="打开数据文件", command=self.load_file)
        file_menu.add_command(label="保存求解结果", command=self.save_result)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)

        menubar.add_cascade(label="文件", menu=file_menu)
        self.root.config(menu=menubar)

    def _build_left_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="实例列表与基本信息", padding=8)
        frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=3)
        frame.rowconfigure(3, weight=2)

        ttk.Label(frame, text="已加载实例：").grid(row=0, column=0, sticky="w")

        self.instance_listbox = tk.Listbox(frame, exportselection=False)
        self.instance_listbox.grid(row=1, column=0, sticky="nsew", pady=4)
        self.instance_listbox.bind("<<ListboxSelect>>", self.on_instance_changed)

        ttk.Label(frame, text="实例信息：").grid(row=2, column=0, sticky="w")

        self.info_text = tk.Text(frame, height=12, wrap=tk.WORD)
        self.info_text.grid(row=3, column=0, sticky="nsew", pady=4)
        self.info_text.config(state=tk.DISABLED)

    def _build_middle_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="散点图", padding=8)
        frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        top_bar = ttk.Frame(frame)
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        ttk.Checkbutton(
            top_bar,
            text="绘图时按第三项价值/重量比排序",
            variable=self.sorted_plot_var
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(top_bar, text="绘制散点图", command=self.plot_current_instance).pack(
            side=tk.LEFT, padx=5
        )

        plot_container = ttk.Frame(frame)
        plot_container.grid(row=1, column=0, sticky="nsew")
        plot_container.rowconfigure(0, weight=1)
        plot_container.columnconfigure(0, weight=1)

        self.plot_panel = PlotPanel(plot_container)
        self.plot_panel.pack(fill=tk.BOTH, expand=True)

    def _build_right_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="操作与结果", padding=8)
        frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=3)
        frame.rowconfigure(4, weight=2)

        ops = ttk.Frame(frame)
        ops.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        ttk.Checkbutton(
            ops,
            text="求解前按第三项价值/重量比排序",
            variable=self.sorted_solve_var
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=2)

        ttk.Button(ops, text="显示排序结果", command=self.show_sorted_table).grid(
            row=1, column=0, padx=4, pady=4, sticky="ew"
        )
        ttk.Button(ops, text="动态规划求最优解", command=self.solve_current_instance).grid(
            row=1, column=1, padx=4, pady=4, sticky="ew"
        )
        ttk.Button(ops, text="保存结果到TXT", command=self.save_result).grid(
            row=2, column=0, columnspan=2, padx=4, pady=4, sticky="ew"
        )

        ttk.Label(frame, text="排序结果：").grid(row=1, column=0, sticky="w")

        columns = ("idx", "gid", "w3", "p3", "ratio")
        self.sort_tree = ttk.Treeview(frame, columns=columns, show="headings", height=16)
        self.sort_tree.grid(row=2, column=0, sticky="nsew")

        self.sort_tree.heading("idx", text="排序后序号")
        self.sort_tree.heading("gid", text="原始组号")
        self.sort_tree.heading("w3", text="第三项重量")
        self.sort_tree.heading("p3", text="第三项价值")
        self.sort_tree.heading("ratio", text="第三项价值/重量比")

        self.sort_tree.column("idx", width=90, anchor="center")
        self.sort_tree.column("gid", width=90, anchor="center")
        self.sort_tree.column("w3", width=100, anchor="center")
        self.sort_tree.column("p3", width=100, anchor="center")
        self.sort_tree.column("ratio", width=140, anchor="center")

        ttk.Label(frame, text="求解结果：").grid(row=3, column=0, sticky="w", pady=(8, 0))

        self.result_text = tk.Text(frame, wrap=tk.NONE)
        self.result_text.grid(row=4, column=0, sticky="nsew", pady=4)
        self.result_text.config(state=tk.DISABLED)

    def _set_text(self, text_widget: tk.Text, content: str):
        text_widget.config(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)
        text_widget.insert(tk.END, content)
        text_widget.config(state=tk.DISABLED)

    def load_file(self):
        file_path = filedialog.askopenfilename(
            title="选择 D{0-1}KP 数据文件",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        try:
            self.instances = parse_dkp_instances(file_path)
            self.instance_listbox.delete(0, tk.END)

            for name in self.instances:
                self.instance_listbox.insert(tk.END, name)

            self.current_instance = None
            self.current_result = None
            self._set_text(self.info_text, "")
            self._set_text(self.result_text, "")
            self.plot_panel.clear()

            for item in self.sort_tree.get_children():
                self.sort_tree.delete(item)

            self.status_var.set(f"成功加载 {len(self.instances)} 个实例：{os.path.basename(file_path)}")

            if self.instance_listbox.size() > 0:
                self.instance_listbox.selection_set(0)
                self.on_instance_changed()

        except Exception as e:
            messagebox.showerror("读取失败", str(e))

    def on_instance_changed(self, event=None):
        selection = self.instance_listbox.curselection()
        if not selection:
            self.current_instance = None
            return

        name = self.instance_listbox.get(selection[0])
        if name not in self.instances:
            return

        self.current_instance = self.instances[name]
        self.current_result = None

        inst = self.current_instance
        info = [
            f"实例名称：{inst.name}",
            f"dimension：{inst.dimension}",
            f"组数：{inst.num_groups}",
            f"capacity：{inst.capacity}",
            f"profits 数量：{len(inst.profits)}",
            f"weights 数量：{len(inst.weights)}",
        ]
        self._set_text(self.info_text, "\n".join(info))
        self._set_text(self.result_text, "")

        for item in self.sort_tree.get_children():
            self.sort_tree.delete(item)

        self.status_var.set(f"当前实例：{inst.name}")

    def plot_current_instance(self):
        if self.current_instance is None:
            messagebox.showwarning("提示", "请先选择一个实例。")
            return

        try:
            self.plot_panel.plot_instance(
                self.current_instance,
                sorted_view=self.sorted_plot_var.get()
            )
            self.status_var.set("散点图绘制完成。")
        except Exception as e:
            messagebox.showerror("绘图失败", str(e))

    def show_sorted_table(self):
        if self.current_instance is None:
            messagebox.showwarning("提示", "请先选择一个实例。")
            return

        for item in self.sort_tree.get_children():
            self.sort_tree.delete(item)

        groups = sort_groups_by_third_ratio(self.current_instance.groups)
        for i, g in enumerate(groups, start=1):
            item3 = g.items[2]
            self.sort_tree.insert(
                "",
                tk.END,
                values=(i, g.group_id, item3.weight, item3.profit, f"{g.third_ratio:.6f}")
            )

        self.status_var.set("排序结果已显示。")

    def solve_current_instance(self):
        if self.current_instance is None:
            messagebox.showwarning("提示", "请先选择一个实例。")
            return

        try:
            self.root.config(cursor="watch")
            self.root.update_idletasks()

            result = solve_dkp_dp(
                self.current_instance,
                sort_before_solve=self.sorted_solve_var.get()
            )
            self.current_result = result

            txt = build_result_text(self.current_instance, result)
            self._set_text(self.result_text, txt)

            self.status_var.set(
                f"求解完成：最优价值={result.max_profit}，耗时={result.elapsed_seconds:.6f} 秒"
            )
        except MemoryError:
            messagebox.showerror("内存不足", "该实例容量较大，当前环境无法完成本次 DP。")
        except Exception as e:
            messagebox.showerror("求解失败", str(e))
        finally:
            self.root.config(cursor="")
            self.root.update_idletasks()

    def save_result(self):
        if self.current_instance is None or self.current_result is None:
            messagebox.showwarning("提示", "当前没有可保存的求解结果，请先求解。")
            return

        file_path = filedialog.asksaveasfilename(
            title="保存结果",
            defaultextension=".txt",
            initialfile=f"{self.current_instance.name}_result.txt",
            filetypes=[("Text Files", "*.txt")]
        )
        if not file_path:
            return

        try:
            txt = build_result_text(self.current_instance, self.current_result)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(txt)

            self.status_var.set(f"结果已保存到：{file_path}")
            messagebox.showinfo("保存成功", "结果文件已保存。")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))