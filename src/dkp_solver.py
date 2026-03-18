# -*- coding: utf-8 -*-
"""
D{0-1}KP 动态规划求解用户程序
--------------------------------
功能：
1. 读入 txt 数据文件中的 D{0-1}KP 实例
2. 绘制任意实例的重量-价值散点图
3. 按每个项集第三项的 价值/重量 比非递增排序
4. 用户可选择指定实例进行最优求解
5. 将最优解、求解时间和详细结果保存为 txt

依赖：
    pip install numpy matplotlib

说明：
- 每个项集固定 3 个物品，且每组至多选择 1 个
- 动态规划使用“分组背包/多重选择背包”模型
- 为了回溯解，程序保存每一组在每个容量下的最优选择
"""

import os
import re
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple

import numpy as np
import matplotlib.pyplot as plt


# =========================
# 数据结构
# =========================

@dataclass
class GroupItem:
    """项集中的一个候选物品"""
    weight: int
    profit: int
    option_id: int  # 1, 2, 3


@dataclass
class ItemGroup:
    """一个项集：固定 3 个候选物品"""
    group_id: int               # 原始组编号（从 1 开始）
    items: List[GroupItem]      # 长度应为 3

    @property
    def third_ratio(self) -> float:
        """第三项的价值/重量比"""
        third = self.items[2]
        return third.profit / third.weight if third.weight != 0 else float("inf")


@dataclass
class DKPInstance:
    """一个 D{0-1}KP 实例"""
    name: str
    dimension: int
    capacity: int
    profits: List[int]
    weights: List[int]
    groups: List[ItemGroup] = field(default_factory=list)

    def validate(self) -> None:
        if self.dimension <= 0:
            raise ValueError(f"{self.name}: dimension 非法")
        if self.dimension % 3 != 0:
            raise ValueError(f"{self.name}: dimension={self.dimension} 不是 3 的倍数")
        if len(self.profits) != self.dimension:
            raise ValueError(
                f"{self.name}: profit 数量错误，期望 {self.dimension}，实际 {len(self.profits)}"
            )
        if len(self.weights) != self.dimension:
            raise ValueError(
                f"{self.name}: weight 数量错误，期望 {self.dimension}，实际 {len(self.weights)}"
            )
        if self.capacity < 0:
            raise ValueError(f"{self.name}: capacity 非法")

    def build_groups(self) -> None:
        """按顺序每 3 个划成 1 个项集"""
        self.validate()
        self.groups = []
        num_groups = self.dimension // 3

        for i in range(num_groups):
            base = 3 * i
            items = [
                GroupItem(weight=self.weights[base + 0], profit=self.profits[base + 0], option_id=1),
                GroupItem(weight=self.weights[base + 1], profit=self.profits[base + 1], option_id=2),
                GroupItem(weight=self.weights[base + 2], profit=self.profits[base + 2], option_id=3),
            ]
            self.groups.append(ItemGroup(group_id=i + 1, items=items))

    @property
    def num_groups(self) -> int:
        return self.dimension // 3


@dataclass
class SolveResult:
    instance_name: str
    max_profit: int
    used_weight: int
    best_capacity_index: int
    elapsed_seconds: float
    selected: List[Optional[int]]   # 每组选择 1/2/3 或 None
    sorted_by_third_ratio: bool
    sorted_group_order: List[int]   # 排序后第 i 组对应原始 group_id

    def selected_count(self) -> int:
        return sum(x is not None for x in self.selected)


# =========================
# 解析 txt 数据
# =========================

def _extract_ints(text: str) -> List[int]:
    return [int(x) for x in re.findall(r'-?\d+', text)]


def parse_dkp_instances(file_path: str) -> Dict[str, DKPInstance]:
    """
    从 txt 文件中解析多个 IDKP 实例。
    兼容：
    - "The diemnsion is d=3*100, the cubage of knapsack is 61500."
    - "The dimension is d=3*200, the cubage of knapsack is 103936."
    """
    with open(file_path, "r", encoding="utf-8") as f:
        raw = f.read()

    # 按 IDKPx: 切块
    pattern = re.compile(r'(IDKP\d+\s*:)', re.IGNORECASE)
    parts = pattern.split(raw)

    if len(parts) < 3:
        raise ValueError("未识别到任何 IDKP 实例，请检查 txt 文件格式。")

    instances: Dict[str, DKPInstance] = {}

    # parts 形如: [前缀, 'IDKP1:', 内容1, 'IDKP2:', 内容2, ...]
    for i in range(1, len(parts), 2):
        name = parts[i].replace(":", "").strip()
        block = parts[i + 1]

        # dimension
        dim_match = re.search(r'd\s*=\s*3\s*\*\s*(\d+)', block, re.IGNORECASE)
        if not dim_match:
            raise ValueError(f"{name}: 未找到 dimension 信息。")
        group_count = int(dim_match.group(1))
        dimension = 3 * group_count

        # capacity / cubage
        cap_match = re.search(
            r'(?:cubage|capacity)\s+of\s+knapsack\s+is\s+(\d+)',
            block,
            re.IGNORECASE
        )
        if not cap_match:
            # 更宽松的兜底
            cap_match = re.search(r'knapsack\s+is\s+(\d+)', block, re.IGNORECASE)
        if not cap_match:
            raise ValueError(f"{name}: 未找到 capacity/cubage 信息。")
        capacity = int(cap_match.group(1))

        # profits
        profit_match = re.search(
            r'The\s+profit\s+of\s+itmes\s+are\s*:\s*(.*?)\s*The\s+weight\s+of\s+itmes\s+are\s*:',
            block,
            re.IGNORECASE | re.DOTALL
        )
        if not profit_match:
            profit_match = re.search(
                r'The\s+profit\s+of\s+items\s+are\s*:\s*(.*?)\s*The\s+weight\s+of\s+items\s+are\s*:',
                block,
                re.IGNORECASE | re.DOTALL
            )
        if not profit_match:
            raise ValueError(f"{name}: 未找到 profit 段。")
        profits = _extract_ints(profit_match.group(1))

        # weights
        weight_match = re.search(
            r'The\s+weight\s+of\s+itmes\s+are\s*:\s*(.*)',
            block,
            re.IGNORECASE | re.DOTALL
        )
        if not weight_match:
            weight_match = re.search(
                r'The\s+weight\s+of\s+items\s+are\s*:\s*(.*)',
                block,
                re.IGNORECASE | re.DOTALL
            )
        if not weight_match:
            raise ValueError(f"{name}: 未找到 weight 段。")
        weights = _extract_ints(weight_match.group(1))

        # 只取前 dimension 个，避免块尾部串到后文
        profits = profits[:dimension]
        weights = weights[:dimension]

        inst = DKPInstance(
            name=name,
            dimension=dimension,
            capacity=capacity,
            profits=profits,
            weights=weights
        )
        inst.build_groups()
        instances[name] = inst

    return instances


# =========================
# 绘图
# =========================

def plot_instance_scatter(instance: DKPInstance, sorted_view: bool = False,
                          save_path: Optional[str] = None) -> None:
    """
    绘制散点图：横轴重量，纵轴价值
    sorted_view=True 时使用按第三项价值重量比排序后的组顺序
    """
    groups = sort_groups_by_third_ratio(instance.groups) if sorted_view else instance.groups

    x1, y1 = [], []
    x2, y2 = [], []
    x3, y3 = [], []

    for g in groups:
        x1.append(g.items[0].weight)
        y1.append(g.items[0].profit)
        x2.append(g.items[1].weight)
        y2.append(g.items[1].profit)
        x3.append(g.items[2].weight)
        y3.append(g.items[2].profit)

    plt.figure(figsize=(10, 7))
    plt.scatter(x1, y1, s=24, label='Option 1')
    plt.scatter(x2, y2, s=24, label='Option 2')
    plt.scatter(x3, y3, s=24, label='Option 3')

    title_suffix = " (sorted by option3 ratio)" if sorted_view else ""
    plt.title(f"{instance.name}: Weight-Profit Scatter{title_suffix}")
    plt.xlabel("Weight")
    plt.ylabel("Profit")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=200)
        print(f"[已保存图片] {save_path}")

    plt.show()


# =========================
# 排序
# =========================

def sort_groups_by_third_ratio(groups: List[ItemGroup]) -> List[ItemGroup]:
    """按第三项 profit/weight 非递增排序"""
    return sorted(groups, key=lambda g: g.third_ratio, reverse=True)


def print_sorted_groups(instance: DKPInstance, top_k: Optional[int] = None) -> None:
    sorted_groups = sort_groups_by_third_ratio(instance.groups)
    if top_k is None:
        top_k = len(sorted_groups)

    print(f"\n{instance.name} 按第三项 value/weight 非递增排序结果（前 {top_k} 组）:")
    print("-" * 90)
    print(f"{'排序后序号':<10}{'原始组号':<10}{'第三项重量':<12}{'第三项价值':<12}{'第三项比值':<15}")
    print("-" * 90)
    for i, g in enumerate(sorted_groups[:top_k], start=1):
        item3 = g.items[2]
        print(f"{i:<10}{g.group_id:<10}{item3.weight:<12}{item3.profit:<12}{g.third_ratio:<15.6f}")
    print("-" * 90)


# =========================
# 动态规划求解
# =========================

def solve_dkp_dp(instance: DKPInstance, sort_before_solve: bool = False) -> SolveResult:
    """
    精确动态规划求解 D{0-1}KP
    状态：
        dp[c] = 处理到当前组时，容量不超过 c 可获得的最大价值
    转移：
        对每组只能选 0/1/2/3 中的一种（0 表示该组不选）
    说明：
        - 为了回溯解，保存 choice[group_idx, capacity] = 0/1/2/3
        - 其中 1/2/3 分别表示选该组的第 1/2/3 个候选
    """
    groups = sort_groups_by_third_ratio(instance.groups) if sort_before_solve else list(instance.groups)
    n = len(groups)
    C = instance.capacity

    # 使用 int64，避免 Python int 列表导致内存爆炸
    NEG_INF = np.int64(-10**18)
    dp_prev = np.full(C + 1, NEG_INF, dtype=np.int64)
    dp_prev[0] = 0

    # 每组、每容量的选择：0/1/2/3
    # uint8 足够，内存约 n*(C+1) 字节
    choices = np.zeros((n, C + 1), dtype=np.uint8)

    weights = np.array([[it.weight for it in g.items] for g in groups], dtype=np.int32)
    profits = np.array([[it.profit for it in g.items] for g in groups], dtype=np.int64)

    start = time.perf_counter()

    for i in range(n):
        # 默认本组不选，直接继承上一层
        dp_curr = dp_prev.copy()
        best_choice = np.zeros(C + 1, dtype=np.uint8)

        for opt in range(3):
            w = int(weights[i, opt])
            p = int(profits[i, opt])

            if w > C:
                continue

            prev_slice = dp_prev[:C + 1 - w]
            cand = prev_slice + p

            curr_view = dp_curr[w:]
            better_mask = cand > curr_view

            if np.any(better_mask):
                curr_view[better_mask] = cand[better_mask]
                best_choice_view = best_choice[w:]
                best_choice_view[better_mask] = opt + 1

        dp_prev = dp_curr
        choices[i] = best_choice

    elapsed = time.perf_counter() - start

    best_capacity = int(np.argmax(dp_prev))
    max_profit = int(dp_prev[best_capacity])

    # 回溯
    selected: List[Optional[int]] = [None] * n
    c = best_capacity

    for i in range(n - 1, -1, -1):
        ch = int(choices[i, c])
        if ch == 0:
            selected[i] = None
        else:
            selected[i] = ch
            c -= int(weights[i, ch - 1])

    used_weight = best_capacity
    sorted_group_order = [g.group_id for g in groups]

    return SolveResult(
        instance_name=instance.name,
        max_profit=max_profit,
        used_weight=used_weight,
        best_capacity_index=best_capacity,
        elapsed_seconds=elapsed,
        selected=selected,
        sorted_by_third_ratio=sort_before_solve,
        sorted_group_order=sorted_group_order
    )


# =========================
# 结果展示 / 保存
# =========================

def print_instance_summary(instance: DKPInstance) -> None:
    print(f"\n实例名称: {instance.name}")
    print(f"dimension = {instance.dimension}")
    print(f"组数      = {instance.num_groups}")
    print(f"capacity  = {instance.capacity}")


def print_solve_result(instance: DKPInstance, result: SolveResult, max_rows: Optional[int] = 30) -> None:
    print("\n" + "=" * 100)
    print(f"实例: {result.instance_name}")
    print(f"是否先按第三项比值排序后求解: {result.sorted_by_third_ratio}")
    print(f"最优总价值: {result.max_profit}")
    print(f"总重量: {result.used_weight} / {instance.capacity}")
    print(f"选中组数: {result.selected_count()} / {instance.num_groups}")
    print(f"求解时间: {result.elapsed_seconds:.6f} 秒")
    print("=" * 100)

    # 构建展示明细
    rows = []
    groups_lookup = {g.group_id: g for g in instance.groups}

    for idx, choice in enumerate(result.selected):
        sorted_group_id = result.sorted_group_order[idx]
        if choice is None:
            continue
        g = groups_lookup[sorted_group_id]
        item = g.items[choice - 1]
        rows.append((idx + 1, sorted_group_id, choice, item.weight, item.profit, item.profit / item.weight))

    print(f"{'排序后序号':<12}{'原始组号':<10}{'选中项':<8}{'重量':<10}{'价值':<10}{'价值重量比':<14}")
    print("-" * 100)

    show_rows = rows if max_rows is None else rows[:max_rows]
    for row in show_rows:
        sidx, gid, choice, w, p, r = row
        print(f"{sidx:<12}{gid:<10}{choice:<8}{w:<10}{p:<10}{r:<14.6f}")

    if max_rows is not None and len(rows) > max_rows:
        print(f"... 其余 {len(rows) - max_rows} 行未显示")
    print("-" * 100)


def save_result_to_txt(instance: DKPInstance, result: SolveResult, output_path: str) -> None:
    groups_lookup = {g.group_id: g for g in instance.groups}

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("D{0-1}KP 动态规划求解结果\n")
        f.write("=" * 80 + "\n")
        f.write(f"实例名称: {result.instance_name}\n")
        f.write(f"dimension: {instance.dimension}\n")
        f.write(f"组数: {instance.num_groups}\n")
        f.write(f"capacity: {instance.capacity}\n")
        f.write(f"是否排序后求解: {result.sorted_by_third_ratio}\n")
        f.write(f"最优总价值: {result.max_profit}\n")
        f.write(f"总重量: {result.used_weight}\n")
        f.write(f"选中组数: {result.selected_count()}\n")
        f.write(f"求解时间(秒): {result.elapsed_seconds:.6f}\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"{'排序后序号':<12}{'原始组号':<10}{'选中项':<8}{'重量':<10}{'价值':<10}{'价值重量比':<14}\n")
        f.write("-" * 80 + "\n")

        for idx, choice in enumerate(result.selected):
            sorted_group_id = result.sorted_group_order[idx]
            if choice is None:
                continue
            g = groups_lookup[sorted_group_id]
            item = g.items[choice - 1]
            ratio = item.profit / item.weight
            f.write(
                f"{idx + 1:<12}{sorted_group_id:<10}{choice:<8}{item.weight:<10}{item.profit:<10}{ratio:<14.6f}\n"
            )

    print(f"[已保存结果] {output_path}")


# =========================
# 命令行用户程序
# =========================

def choose_instance(instances: Dict[str, DKPInstance]) -> DKPInstance:
    names = list(instances.keys())
    print("\n可用实例：")
    for i, name in enumerate(names, start=1):
        inst = instances[name]
        print(f"{i}. {name}  (组数={inst.num_groups}, capacity={inst.capacity})")

    while True:
        s = input("请输入实例编号：").strip()
        if not s.isdigit():
            print("输入非法，请输入数字编号。")
            continue
        idx = int(s)
        if 1 <= idx <= len(names):
            return instances[names[idx - 1]]
        print("编号越界，请重新输入。")


def main():
    print("=" * 80)
    print("D{0-1}KP 动态规划求解用户程序")
    print("=" * 80)

    instances: Dict[str, DKPInstance] = {}
    last_result: Optional[SolveResult] = None
    last_instance: Optional[DKPInstance] = None

    while True:
        print("\n菜单：")
        print("1. 读取 D{0-1}KP 数据文件")
        print("2. 查看已加载实例列表")
        print("3. 绘制指定实例散点图")
        print("4. 按第三项价值/重量比排序并查看")
        print("5. 求解指定实例（动态规划）")
        print("6. 保存最近一次求解结果到 txt")
        print("0. 退出")

        cmd = input("请输入功能编号：").strip()

        if cmd == "1":
            file_path = input("请输入 txt 数据文件路径：").strip().strip('"')
            if not os.path.isfile(file_path):
                print("文件不存在，请检查路径。")
                continue
            try:
                instances = parse_dkp_instances(file_path)
                print(f"成功读取 {len(instances)} 个实例：{', '.join(instances.keys())}")
            except Exception as e:
                print(f"读取失败：{e}")

        elif cmd == "2":
            if not instances:
                print("尚未加载数据文件。")
                continue
            print("\n已加载实例：")
            for name, inst in instances.items():
                print(f"- {name}: 组数={inst.num_groups}, dimension={inst.dimension}, capacity={inst.capacity}")

        elif cmd == "3":
            if not instances:
                print("尚未加载数据文件。")
                continue
            inst = choose_instance(instances)
            print_instance_summary(inst)

            ans = input("是否先按第三项比值排序后再绘图？(y/n)：").strip().lower()
            sorted_view = (ans == "y")

            save_ans = input("是否保存散点图图片？(y/n)：").strip().lower()
            save_path = None
            if save_ans == "y":
                save_path = input("请输入图片保存路径（如 figure.png）：").strip().strip('"')

            plot_instance_scatter(inst, sorted_view=sorted_view, save_path=save_path)

        elif cmd == "4":
            if not instances:
                print("尚未加载数据文件。")
                continue
            inst = choose_instance(instances)
            print_instance_summary(inst)

            top_k_in = input("显示前多少组？直接回车表示全部：").strip()
            top_k = None
            if top_k_in:
                if not top_k_in.isdigit():
                    print("输入非法。")
                    continue
                top_k = int(top_k_in)
            print_sorted_groups(inst, top_k=top_k)

        elif cmd == "5":
            if not instances:
                print("尚未加载数据文件。")
                continue
            inst = choose_instance(instances)
            print_instance_summary(inst)

            ans = input("求解前是否先按第三项比值排序？(y/n)：").strip().lower()
            sort_before_solve = (ans == "y")

            print("正在进行动态规划求解，请稍候...")
            try:
                result = solve_dkp_dp(inst, sort_before_solve=sort_before_solve)
                print_solve_result(inst, result, max_rows=50)
                last_result = result
                last_instance = inst
            except MemoryError:
                print("内存不足：该实例容量较大，当前机器无法完成本次 DP。")
            except Exception as e:
                print(f"求解失败：{e}")

        elif cmd == "6":
            if last_result is None or last_instance is None:
                print("还没有可保存的求解结果，请先执行求解。")
                continue
            output_path = input("请输入输出 txt 路径：").strip().strip('"')
            try:
                save_result_to_txt(last_instance, last_result, output_path)
            except Exception as e:
                print(f"保存失败：{e}")

        elif cmd == "0":
            print("程序结束。")
            break

        else:
            print("无效命令，请重新输入。")


if __name__ == "__main__":
    main()