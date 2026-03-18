# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class GroupItem:
    weight: int
    profit: int
    option_id: int  # 1, 2, 3


@dataclass
class ItemGroup:
    group_id: int
    items: List[GroupItem]

    @property
    def third_ratio(self) -> float:
        third = self.items[2]
        return third.profit / third.weight if third.weight != 0 else float("inf")


@dataclass
class DKPInstance:
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
            raise ValueError(f"{self.name}: dimension 必须是 3 的倍数")
        if len(self.profits) != self.dimension:
            raise ValueError(
                f"{self.name}: profits 数量错误，期望 {self.dimension}，实际 {len(self.profits)}"
            )
        if len(self.weights) != self.dimension:
            raise ValueError(
                f"{self.name}: weights 数量错误，期望 {self.dimension}，实际 {len(self.weights)}"
            )
        if self.capacity < 0:
            raise ValueError(f"{self.name}: capacity 非法")

    def build_groups(self) -> None:
        self.validate()
        self.groups = []

        for i in range(self.dimension // 3):
            base = 3 * i
            group = ItemGroup(
                group_id=i + 1,
                items=[
                    GroupItem(weight=self.weights[base], profit=self.profits[base], option_id=1),
                    GroupItem(weight=self.weights[base + 1], profit=self.profits[base + 1], option_id=2),
                    GroupItem(weight=self.weights[base + 2], profit=self.profits[base + 2], option_id=3),
                ]
            )
            self.groups.append(group)

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
    selected: List[Optional[int]]
    sorted_by_third_ratio: bool
    sorted_group_order: List[int]

    def selected_count(self) -> int:
        return sum(x is not None for x in self.selected)