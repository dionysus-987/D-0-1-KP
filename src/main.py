# -*- coding: utf-8 -*-
import ttkbootstrap as ttk
from main_window import MainWindow

import matplotlib

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
matplotlib.rcParams["axes.unicode_minus"] = False

from main_window import MainWindow
def main():
    root = ttk.Window(themename="flatly")
    MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()

