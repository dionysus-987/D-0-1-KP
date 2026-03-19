# -*- coding: utf-8 -*-
from parser_utils import parse_dkp_instances
from algorithms.dp_solver import DPSolver
from algorithms.greedy_ratio import GreedyRatioSolver
from algorithms.greedy_third_ratio import GreedyThirdRatioSolver
from experiment.runner import ExperimentRunner
from experiment.exporter import export_results_to_csv, export_results_to_txt


def main():
    instances = parse_dkp_instances("udkp1-10.txt")

    solvers = [
        DPSolver(sort_before_solve=False),
        DPSolver(sort_before_solve=True),
        GreedyRatioSolver(),
        GreedyThirdRatioSolver(),
    ]

    runner = ExperimentRunner(solvers)
    results = runner.run_all(instances)

    export_results_to_csv(results, "experiment_results.csv")
    export_results_to_txt(results, "experiment_results.txt")

    print("实验完成，结果已导出。")


if __name__ == "__main__":
    main()