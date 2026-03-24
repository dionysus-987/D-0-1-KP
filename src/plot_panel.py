# -*- coding: utf-8 -*-

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from algorithms.dp_solver import sort_groups_by_third_ratio


class PlotPanel:
    """
    D{0-1}KP 实例散点图面板（统一主题版）
    """

    COLORS = {
        "option1": "#2563EB",   # 主蓝
        "option2": "#14B8A6",   # 青绿
        "option3": "#F59E0B",   # 柔橙
        "bg": "#FBFCFE",        # 坐标区背景
        "figure_bg": "#FFFFFF", # 画布背景
        "grid": "#E5EAF3",      # 网格
        "text": "#1F2937",      # 主文本
        "subtext": "#6B7280",   # 次文本
        "border": "#D8E1EE"     # 边框
    }

    def __init__(self, parent):
        self.parent = parent

        self.figure = Figure(figsize=(6, 5), tight_layout=True, dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.widget = self.canvas.get_tk_widget()

        self._apply_axes_style()
        self.clear()

    def pack(self, **kwargs):
        self.widget.pack(**kwargs)

    def grid(self, **kwargs):
        self.widget.grid(**kwargs)

    def place(self, **kwargs):
        self.widget.place(**kwargs)

    def _apply_axes_style(self):
        self.figure.patch.set_facecolor(self.COLORS["figure_bg"])
        self.ax.set_facecolor(self.COLORS["bg"])

        for spine in self.ax.spines.values():
            spine.set_color(self.COLORS["border"])
            spine.set_linewidth(1.0)

        self.ax.tick_params(axis="both", colors="#374151", labelsize=9)

        self.ax.grid(
            True,
            linestyle="--",
            linewidth=0.8,
            color=self.COLORS["grid"],
            alpha=0.9
        )

    def _reset_axes(self):
        self.ax.clear()
        self._apply_axes_style()

    def clear(self):
        self._reset_axes()

        self.ax.set_title(
            "实例散点图",
            fontsize=13,
            fontweight="bold",
            color=self.COLORS["text"],
            pad=14
        )
        self.ax.set_xlabel("Weight", fontsize=10, color=self.COLORS["text"])
        self.ax.set_ylabel("Profit", fontsize=10, color=self.COLORS["text"])

        self.ax.text(
            0.5,
            0.5,
            "请选择实例后进行绘图",
            ha="center",
            va="center",
            transform=self.ax.transAxes,
            fontsize=11,
            color=self.COLORS["subtext"]
        )

        self.canvas.draw()

    def plot_instance(self, instance, sorted_view=False):
        self._reset_axes()

        if instance is None:
            self.clear()
            return

        groups = sort_groups_by_third_ratio(instance.groups) if sorted_view else instance.groups

        x1, y1 = [], []
        x2, y2 = [], []
        x3, y3 = [], []

        skipped = 0

        for g in groups:
            items = getattr(g, "items", None)
            if not items or len(items) < 3:
                skipped += 1
                continue

            try:
                x1.append(items[0].weight)
                y1.append(items[0].profit)

                x2.append(items[1].weight)
                y2.append(items[1].profit)

                x3.append(items[2].weight)
                y3.append(items[2].profit)
            except Exception:
                skipped += 1
                continue

        total_points = len(x1) + len(x2) + len(x3)

        if total_points == 0:
            self.ax.set_title(
                "实例散点图",
                fontsize=13,
                fontweight="bold",
                color=self.COLORS["text"],
                pad=14
            )
            self.ax.set_xlabel("Weight", fontsize=10, color=self.COLORS["text"])
            self.ax.set_ylabel("Profit", fontsize=10, color=self.COLORS["text"])

            self.ax.text(
                0.5,
                0.5,
                "当前实例没有可绘制的数据",
                ha="center",
                va="center",
                transform=self.ax.transAxes,
                fontsize=11,
                color=self.COLORS["subtext"]
            )

            self.canvas.draw()
            return

        self.ax.scatter(
            x1, y1,
            s=36,
            alpha=0.9,
            color=self.COLORS["option1"],
            edgecolors="white",
            linewidth=0.6,
            label="Option 1"
        )

        self.ax.scatter(
            x2, y2,
            s=36,
            alpha=0.9,
            color=self.COLORS["option2"],
            edgecolors="white",
            linewidth=0.6,
            label="Option 2"
        )

        self.ax.scatter(
            x3, y3,
            s=36,
            alpha=0.9,
            color=self.COLORS["option3"],
            edgecolors="white",
            linewidth=0.6,
            label="Option 3"
        )

        suffix = "（按第3项价值重量比排序）" if sorted_view else ""
        title = f"{instance.name}：重量-价值散点图{suffix}"

        self.ax.set_title(
            title,
            fontsize=13,
            fontweight="bold",
            color=self.COLORS["text"],
            pad=14
        )
        self.ax.set_xlabel("Weight", fontsize=10, color=self.COLORS["text"])
        self.ax.set_ylabel("Profit", fontsize=10, color=self.COLORS["text"])

        legend = self.ax.legend(
            loc="best",
            frameon=True,
            fontsize=9,
            borderpad=0.6
        )
        legend.get_frame().set_facecolor("#FFFFFF")
        legend.get_frame().set_edgecolor(self.COLORS["border"])
        legend.get_frame().set_alpha(0.95)

        note = f"groups={len(groups)}, plotted={len(x1)}, skipped={skipped}"
        self.ax.text(
            0.99,
            0.01,
            note,
            transform=self.ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=8,
            color=self.COLORS["subtext"]
        )

        self.canvas.draw()