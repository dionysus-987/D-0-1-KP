# -*- coding: utf-8 -*-
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from solver import sort_groups_by_third_ratio


class PlotPanel:
    def __init__(self, parent):
        self.figure = Figure(figsize=(6, 5), tight_layout=True)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.widget = self.canvas.get_tk_widget()
        self.clear()

    def pack(self, **kwargs):
        self.widget.pack(**kwargs)

    def clear(self):
        self.ax.clear()
        self.ax.set_title("Scatter Plot Area")
        self.ax.set_xlabel("Weight")
        self.ax.set_ylabel("Profit")
        self.ax.grid(True, linestyle="--", alpha=0.4)
        self.canvas.draw()

    def plot_instance(self, instance, sorted_view=False):
        self.ax.clear()

        groups = sort_groups_by_third_ratio(instance.groups) if sorted_view else instance.groups

        x1, y1, x2, y2, x3, y3 = [], [], [], [], [], []
        for g in groups:
            x1.append(g.items[0].weight)
            y1.append(g.items[0].profit)
            x2.append(g.items[1].weight)
            y2.append(g.items[1].profit)
            x3.append(g.items[2].weight)
            y3.append(g.items[2].profit)

        self.ax.scatter(x1, y1, s=24, label="Option 1")
        self.ax.scatter(x2, y2, s=24, label="Option 2")
        self.ax.scatter(x3, y3, s=24, label="Option 3")
        self.ax.set_xlabel("Weight")
        self.ax.set_ylabel("Profit")
        suffix = " (Sorted by option3 ratio)" if sorted_view else ""
        self.ax.set_title(f"{instance.name}: Weight-Profit Scatter{suffix}")
        self.ax.grid(True, linestyle="--", alpha=0.4)
        self.ax.legend()
        self.canvas.draw()