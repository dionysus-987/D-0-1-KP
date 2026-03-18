# -*- coding: utf-8 -*-
import time
from typing import List, Optional

import numpy as np

from models import DKPInstance, ItemGroup, SolveResult


def sort_groups_by_third_ratio(groups: List[ItemGroup]) -> List[ItemGroup]:
    return sorted(groups, key=lambda g: g.third_ratio, reverse=True)


def solve_dkp_dp(instance: DKPInstance, sort_before_solve: bool = False) -> SolveResult:
    groups = sort_groups_by_third_ratio(instance.groups) if sort_before_solve else list(instance.groups)
    n = len(groups)
    C = instance.capacity

    NEG_INF = np.int64(-10**18)
    dp_prev = np.full(C + 1, NEG_INF, dtype=np.int64)
    dp_prev[0] = 0

    choices = np.zeros((n, C + 1), dtype=np.uint8)

    weights = np.array([[it.weight for it in g.items] for g in groups], dtype=np.int32)
    profits = np.array([[it.profit for it in g.items] for g in groups], dtype=np.int64)

    start = time.perf_counter()

    for i in range(n):
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
                choice_view = best_choice[w:]
                choice_view[better_mask] = opt + 1

        dp_prev = dp_curr
        choices[i] = best_choice

    elapsed = time.perf_counter() - start

    best_capacity = int(np.argmax(dp_prev))
    max_profit = int(dp_prev[best_capacity])

    selected: List[Optional[int]] = [None] * n
    c = best_capacity
    for i in range(n - 1, -1, -1):
        ch = int(choices[i, c])
        if ch == 0:
            selected[i] = None
        else:
            selected[i] = ch
            c -= int(weights[i, ch - 1])

    return SolveResult(
        instance_name=instance.name,
        max_profit=max_profit,
        used_weight=best_capacity,
        best_capacity_index=best_capacity,
        elapsed_seconds=elapsed,
        selected=selected,
        sorted_by_third_ratio=sort_before_solve,
        sorted_group_order=[g.group_id for g in groups]
    )


def build_result_text(instance: DKPInstance, result: SolveResult) -> str:
    groups_lookup = {g.group_id: g for g in instance.groups}

    lines = []
    lines.append("D{0-1}KP 动态规划求解结果")
    lines.append("=" * 80)
    lines.append(f"实例名称: {result.instance_name}")
    lines.append(f"dimension: {instance.dimension}")
    lines.append(f"组数: {instance.num_groups}")
    lines.append(f"capacity: {instance.capacity}")
    lines.append(f"是否排序后求解: {result.sorted_by_third_ratio}")
    lines.append(f"最优总价值: {result.max_profit}")
    lines.append(f"总重量: {result.used_weight}")
    lines.append(f"选中组数: {result.selected_count()}")
    lines.append(f"求解时间(秒): {result.elapsed_seconds:.6f}")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"{'排序后序号':<12}{'原始组号':<10}{'选中项':<8}{'重量':<10}{'价值':<10}{'价值重量比':<14}")
    lines.append("-" * 80)

    for idx, choice in enumerate(result.selected):
        gid = result.sorted_group_order[idx]
        if choice is None:
            continue
        g = groups_lookup[gid]
        item = g.items[choice - 1]
        ratio = item.profit / item.weight
        lines.append(
            f"{idx + 1:<12}{gid:<10}{choice:<8}{item.weight:<10}{item.profit:<10}{ratio:<14.6f}"
        )

    return "\n".join(lines)