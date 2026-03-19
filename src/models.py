# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class GroupItem:
    weight: int
    profit: int
    option_id: int  # 1, 2, 3

    @property
    def ratio(self) -> float:
        return self.profit / self.weight if self.weight != 0 else float("inf")


@dataclass
class ItemGroup:
    group_id: int
    items: List[GroupItem]

    @property
    def third_ratio(self) -> float:
        if len(self.items) < 3:
            raise ValueError(f"group {self.group_id}: 当前分组不足 3 个元素，无法计算 third_ratio")
        third = self.items[2]
        return third.profit / third.weight if third.weight != 0 else float("inf")

    @property
    def best_item_by_ratio(self) -> GroupItem:
        return max(self.items, key=lambda x: x.ratio)

    @property
    def best_ratio(self) -> float:
        return self.best_item_by_ratio.ratio


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
class AlgorithmResult:
    instance_name: str
    algorithm_name: str
    sorted_before_solve: bool

    value: int
    weight: int
    time_seconds: float

    selected: List[Optional[int]]
    sorted_group_order: List[int]

    optimal: Optional[bool] = None
    gap: Optional[float] = None
    reference_value: Optional[int] = None

    success: bool = True
    error_message: str = ""
    extra: Dict[str, float] = field(default_factory=dict)

    def selected_count(self) -> int:
        return sum(x is not None for x in self.selected)


@dataclass
class InstanceExperimentResult:
    instance_name: str
    results: List[AlgorithmResult]