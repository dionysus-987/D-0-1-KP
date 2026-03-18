# -*- coding: utf-8 -*-
import re
from typing import Dict, List

from models import DKPInstance


def extract_ints(text: str) -> List[int]:
    return [int(x) for x in re.findall(r'-?\d+', text)]


def parse_dkp_instances(file_path: str) -> Dict[str, DKPInstance]:
    with open(file_path, "r", encoding="utf-8") as f:
        raw = f.read()

    pattern = re.compile(r'(IDKP\d+\s*:)', re.IGNORECASE)
    parts = pattern.split(raw)

    if len(parts) < 3:
        raise ValueError("未识别到任何 IDKP 实例，请检查 txt 文件格式。")

    instances: Dict[str, DKPInstance] = {}

    for i in range(1, len(parts), 2):
        name = parts[i].replace(":", "").strip()
        block = parts[i + 1]

        dim_match = re.search(r'd\s*=\s*3\s*\*\s*(\d+)', block, re.IGNORECASE)
        if not dim_match:
            raise ValueError(f"{name}: 未找到 dimension 信息。")
        group_count = int(dim_match.group(1))
        dimension = 3 * group_count

        cap_match = re.search(
            r'(?:cubage|capacity)\s+of\s+knapsack\s+is\s+(\d+)',
            block,
            re.IGNORECASE
        )
        if not cap_match:
            cap_match = re.search(r'knapsack\s+is\s+(\d+)', block, re.IGNORECASE)
        if not cap_match:
            raise ValueError(f"{name}: 未找到 capacity/cubage 信息。")
        capacity = int(cap_match.group(1))

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

        profits = extract_ints(profit_match.group(1))[:dimension]

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

        weights = extract_ints(weight_match.group(1))[:dimension]

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