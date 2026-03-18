# -*- coding: utf-8 -*-
"""
D{0-1}KP 动态规划求解系统 - 主界面优化版
优化内容：多线程求解、UI 响应增强、代码规范化、快捷键支持
"""
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Optional, Any
from functools import partial

# 假设这些模块在同一目录下且功能正常
from models import DKPInstance, SolveResult
from parser_utils import parse_dkp_instances
from plot_panel import PlotPanel
from solver import sort_groups_by_third_ratio, solve_dkp_dp, build_result_text

# --- 常量定义 ---
APP_TITLE = "D{0-1}KP 动态规划求解系统（Tkinter 版）"
DEFAULT_WIDTH = 1450
DEFAULT_HEIGHT = 860
MIN_WIDTH = 1024
MIN_HEIGHT = 768
FONT_FAMILY = "Segoe UI"  # 或 "Microsoft YaHei"

class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}")
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)

        # 状态数据
        self.instances: Dict[str, DKPInstance] = {}
        self.current_instance: Optional[DKPInstance] = None
        self.current_result: Optional[SolveResult] = None
        self.is_solving = False  # 防止重复求解的标志位

        # UI 变量
        self.sorted_plot_var = tk.BooleanVar(value=False)
        self.sorted_solve_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="就绪")

        # 初始化界面
        self._setup_styles()
        self._build_ui()
        self._bind_shortcuts()

    def _setup_styles(self):
        """配置全局样式"""
        style = ttk.Style()
        style.theme_use('clam')  # 使用更现代的主题
        style.configure("TLabel", font=(FONT_FAMILY, 10))
        style.configure("TButton", font=(FONT_FAMILY, 10))
        style.configure("TLabelframe.Label", font=(FONT_FAMILY, 11, "bold"))

    def _build_ui(self):
        self._build_menu()

        # 主容器配置
        main_frame = ttk.Frame(self.root, padding=8)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 配置网格权重，确保缩放比例合理
        for i in range(3):
            main_frame.columnconfigure(i, weight=1 if i == 0 else 2)
        main_frame.rowconfigure(0, weight=1)

        self._build_left_panel(main_frame)
        self._build_middle_panel(main_frame)
        self._build_right_panel(main_frame)

        # 状态栏
        status_bar = ttk.Label(
            self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w", padding=4
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _bind_shortcuts(self):
        """绑定键盘快捷键"""
        self.root.bind("<Control-o>", lambda e: self.load_file())
        self.root.bind("<Control-s>", lambda e: self.save_result())
        self.root.bind("<Control-q>", lambda e: self.root.quit())

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="打开数据文件 (Ctrl+O)", command=self.load_file, accelerator="Ctrl+O")
        file_menu.add_command(label="保存求解结果 (Ctrl+S)", command=self.save_result, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="退出 (Ctrl+Q)", command=self.root.quit, accelerator="Ctrl+Q")
        menubar.add_cascade(label="文件", menu=file_menu)
        self.root.config(menu=menubar)

    def _build_left_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="实例列表与基本信息", padding=8)
        frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)  # Listbox 占主要空间
        frame.rowconfigure(3, weight=1)  # Info Text 占次要空间

        ttk.Label(frame, text="已加载实例：").grid(row=0, column=0, sticky="w")

        self.instance_listbox = tk.Listbox(frame, exportselection=False, font=(FONT_FAMILY, 10))
        self.instance_listbox.grid(row=1, column=0, sticky="nsew", pady=4)
        self.instance_listbox.bind("<<ListboxSelect>>", self.on_instance_changed)

        ttk.Label(frame, text="实例信息：").grid(row=2, column=0, sticky="w")

        self.info_text = tk.Text(frame, height=10, wrap=tk.WORD, state=tk.DISABLED, font=("Consolas", 9))
        self.info_text.grid(row=3, column=0, sticky="nsew", pady=4)

    def _build_middle_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="散点图分析", padding=8)
        frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        top_bar = ttk.Frame(frame)
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        ttk.Checkbutton(
            top_bar, text="按第三项价值/重量比排序", variable=self.sorted_plot_var
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(top_bar, text="绘制散点图", command=self.plot_current_instance).pack(
            side=tk.LEFT, padx=5
        )

        plot_container = ttk.Frame(frame)
        plot_container.grid(row=1, column=0, sticky="nsew")
        # PlotPanel 内部应处理 pack/grid，这里确保容器可伸缩
        self.plot_panel = PlotPanel(plot_container)
        self.plot_panel.pack(fill=tk.BOTH, expand=True)

    def _build_right_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="操作与结果", padding=8)
        frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=2)  # 表格
        frame.rowconfigure(4, weight=2)  # 结果文本

        ops = ttk.Frame(frame)
        ops.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        ttk.Checkbutton(
            ops, text="求解前排序", variable=self.sorted_solve_var
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=2)

        # 按钮布局优化
        btn_opts = {"padx": 4, "pady": 4, "sticky": "ew"}
        ttk.Button(ops, text="显示排序表", command=self.show_sorted_table).grid(row=1, column=0, **btn_opts)
        self.btn_solve = ttk.Button(ops, text="动态规划求解", command=self.solve_current_instance)
        self.btn_solve.grid(row=1, column=1, **btn_opts)
        ttk.Button(ops, text="保存结果", command=self.save_result).grid(row=2, column=0, columnspan=2, **btn_opts)

        ttk.Label(frame, text="排序预览：").grid(row=1, column=0, sticky="w")

        columns = ("idx", "gid", "w3", "p3", "ratio")
        self.sort_tree = ttk.Treeview(frame, columns=columns, show="headings", height=10)
        self.sort_tree.grid(row=2, column=0, sticky="nsew", pady=4)

        # 配置列
        col_widths = {"idx": 60, "gid": 60, "w3": 80, "p3": 80, "ratio": 100}
        col_names = {"idx": "序号", "gid": "组号", "w3": "重量 3", "p3": "价值 3", "ratio": "价值/重量"}
        for col in columns:
            self.sort_tree.heading(col, text=col_names[col])
            self.sort_tree.column(col, width=col_widths[col], anchor="center")

        ttk.Label(frame, text="求解结果：").grid(row=3, column=0, sticky="w", pady=(8, 0))

        self.result_text = tk.Text(frame, wrap=tk.NONE, state=tk.DISABLED, font=("Consolas", 9))
        self.result_text.grid(row=4, column=0, sticky="nsew", pady=4)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.result_text, orient="vertical", command=self.result_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.result_text.config(yscrollcommand=scrollbar.set)

    def _set_text(self, text_widget: tk.Text, content: str):
        """安全设置 Text 控件内容"""
        try:
            text_widget.config(state=tk.NORMAL)
            text_widget.delete("1.0", tk.END)
            text_widget.insert(tk.END, content)
            text_widget.config(state=tk.DISABLED)
        except Exception:
            pass

    def _reset_ui(self):
        """重置界面状态"""
        self.instance_listbox.delete(0, tk.END)
        self._set_text(self.info_text, "")
        self._set_text(self.result_text, "")
        self.plot_panel.clear()
        for item in self.sort_tree.get_children():
            self.sort_tree.delete(item)
        self.current_instance = None
        self.current_result = None

    def _set_controls_state(self, state: str):
        """批量设置控件状态 (normal/disabled)"""
        # 求解过程中禁用主要操作按钮
        self.btn_solve.config(state=state)
        # 可以根据需要禁用其他按钮，例如加载文件时禁用求解

    def load_file(self):
        file_path = filedialog.askopenfilename(
            title="选择 D{0-1}KP 数据文件",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        try:
            self.status_var.set("正在解析文件...")
            self.root.config(cursor="watch")
            self.root.update_idletasks()

            self.instances = parse_dkp_instances(file_path)
            self._reset_ui()

            for name in self.instances:
                self.instance_listbox.insert(tk.END, name)

            self.status_var.set(f"成功加载 {len(self.instances)} 个实例：{os.path.basename(file_path)}")

            if self.instance_listbox.size() > 0:
                self.instance_listbox.selection_set(0)
                self.on_instance_changed()

        except Exception as e:
            messagebox.showerror("读取失败", f"无法解析文件：\n{str(e)}")
            self.status_var.set("文件加载失败")
        finally:
            self.root.config(cursor="")

    def on_instance_changed(self, event=None):
        selection = self.instance_listbox.curselection()
        if not selection:
            self.current_instance = None
            self._set_text(self.info_text, "")
            return

        name = self.instance_listbox.get(selection[0])
        if name not in self.instances:
            return

        self.current_instance = self.instances[name]
        self.current_result = None
        self._set_text(self.result_text, "")
        for item in self.sort_tree.get_children():
            self.sort_tree.delete(item)
        self.plot_panel.clear()

        inst = self.current_instance
        info = [
            f"实例名称：{inst.name}",
            f"维度 (Dimension)：{inst.dimension}",
            f"组数 (Groups)：{inst.num_groups}",
            f"背包容量 (Capacity)：{inst.capacity}",
            f"利润数组大小：{len(inst.profits)}",
            f"重量数组大小：{len(inst.weights)}",
        ]
        self._set_text(self.info_text, "\n".join(info))
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
            self.status_var.set("绘图失败")

    def show_sorted_table(self):
        if self.current_instance is None:
            messagebox.showwarning("提示", "请先选择一个实例。")
            return

        for item in self.sort_tree.get_children():
            self.sort_tree.delete(item)

        try:
            groups = sort_groups_by_third_ratio(self.current_instance.groups)
            for i, g in enumerate(groups, start=1):
                # 确保 items 存在且至少有 3 个元素，防止索引错误
                if len(g.items) > 2:
                    item3 = g.items[2]
                    self.sort_tree.insert(
                        "", tk.END,
                        values=(i, g.group_id, item3.weight, item3.profit, f"{g.third_ratio:.6f}")
                    )
            self.status_var.set("排序结果已显示。")
        except Exception as e:
            messagebox.showerror("排序失败", str(e))

    def solve_current_instance(self):
        if self.current_instance is None:
            messagebox.showwarning("提示", "请先选择一个实例。")
            return

        if self.is_solving:
            messagebox.showinfo("提示", "正在求解中，请稍候...")
            return

        # 启动后台线程
        self.is_solving = True
        self._set_controls_state("disabled")
        self.status_var.set("正在求解...")
        self.root.config(cursor="watch")

        # 使用线程避免阻塞 UI
        thread = threading.Thread(target=self._solve_worker, daemon=True)
        thread.start()

    def _solve_worker(self):
        """后台求解工作线程"""
        result = None
        error_msg = None
        try:
            result = solve_dkp_dp(
                self.current_instance,
                sort_before_solve=self.sorted_solve_var.get()
            )
        except MemoryError:
            error_msg = "内存不足：该实例容量较大，当前环境无法完成本次 DP。"
        except Exception as e:
            error_msg = f"求解异常：{str(e)}"

        # 通过 mainloop 安全更新 UI
        self.root.after(0, self._on_solve_complete, result, error_msg)

    def _on_solve_complete(self, result: Optional[SolveResult], error_msg: Optional[str]):
        """求解完成后的 UI 回调（运行在主线程）"""
        self.is_solving = False
        self._set_controls_state("normal")
        self.root.config(cursor="")

        if error_msg:
            messagebox.showerror("求解失败", error_msg)
            self.status_var.set("求解失败")
            return

        if result:
            self.current_result = result
            txt = build_result_text(self.current_instance, result)
            self._set_text(self.result_text, txt)
            self.status_var.set(
                f"求解完成：最优价值={result.max_profit}，耗时={result.elapsed_seconds:.4f} 秒"
            )
        else:
            self.status_var.set("求解未返回结果")

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
            self.status_var.set(f"结果已保存到：{os.path.basename(file_path)}")
            messagebox.showinfo("保存成功", "结果文件已保存。")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

def main():
    root = tk.Tk()
    # 设置 DPI 感知 (Windows 10+ 高分屏支持)
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()