#!/usr/bin/env python3


""" This is the source code related to the paper 'Mining Potentially Explanatory Patterns via Partial Solutions',
    The authors of the paper are Giancarlo Catalano (me),
      Sandy Brownlee, David Cairns (Stirling Uni)
      John McCall (RGU)
      Russell Ainsle (BT).


    This code is a minimal implementation of the system I proposed in the paper,
    and I hope you can find the answers to any questions that you have!

    I recommend playing around with:
        - The problem being solved
        - The metrics used to search for PSs (find them in PSMiner.with_default_settings)
        - the sample sizes etc...
"""
import csv
import json
import os
from typing import Optional

import utils
from BenchmarkProblems.GraphColouring import GraphColouring
from Core import TerminationCriteria
from BenchmarkProblems.BT.BTProblem import BTProblem
from BenchmarkProblems.BenchmarkProblem import BenchmarkProblem
from BenchmarkProblems.EfficientBTProblem.EfficientBTProblem import EfficientBTProblem
from Core.EvaluatedFS import EvaluatedFS
from Experimentation.DetectingPatterns import json_to_cohorts, cohorts_to_json, \
    BTProblemPatternDetector, mine_cohorts_from_problem, analyse_data_from_json_cohorts, \
    show_interactive_3d_plot_of_scores, mine_pss_from_problem, get_shap_values_plot
from Core.Explainer import Explainer
from Core.PSMiner import PSMiner
from Core.PickAndMerge import PickAndMergeSampler
from PSMiners.DEAP.NSGAMiner import plot_stats_for_run, report_in_order_of_last_metric
from utils import announce, indent


def show_overall_system(benchmark_problem: BenchmarkProblem):
    """
    This function gives an overview of the system:
        1. Generate a reference population (a PRef)
        2. Generate a Core Catalog using the Core Miner
        3. Sample new solutions from the catalog using Pick & Merge
        4. Explain those new solutions using the catalog

    :param benchmark_problem: a benchmark problem, find more in the BenchmarkProblems directory
    :return: Nothing! Just printing
    """

    print(f"The problem is {benchmark_problem}")

    # 1. Generating the reference population
    pRef_size = 10000
    with announce("Generating Reference Population"):
        pRef = benchmark_problem.get_reference_population(pRef_size)
    pRef.describe_self()

    # 2. Obtaining the Core catalog
    ps_miner = PSMiner.with_default_settings(pRef)
    ps_evaluation_budget = 10000
    termination_criterion = TerminationCriteria.PSEvaluationLimit(ps_evaluation_budget)

    with announce("Running the Core Miner"):
        ps_miner.run(termination_criterion)

    ps_catalog = ps_miner.get_results(20)

    print("The catalog consists of:")
    for item in ps_catalog:
        print("\n")
        print(indent(f"{benchmark_problem.repr_ps(item.ps)}, weight = {item.aggregated_score:.3f}"))

    # 3. Sampling new solutions
    print("\nFrom the catalog we can sample new solutions")
    new_solutions_to_produce = 12
    sampler = PickAndMergeSampler(search_space=benchmark_problem.search_space,
                                  individuals=ps_catalog)

    with announce("Sampling from the Core Catalog using Pick & Merge"):
        sampled_solutions = [sampler.sample() for _ in range(new_solutions_to_produce)]

    evaluated_sampled_solutions = [EvaluatedFS(fs, benchmark_problem.fitness_function(fs)) for fs in sampled_solutions]
    evaluated_sampled_solutions.sort(reverse=True)

    for index, sample in enumerate(evaluated_sampled_solutions):
        print(f"[{index}]")
        print(indent(indent(f"{benchmark_problem.repr_fs(sample.full_solution)}, has fitness {sample.fitness:.2f}")))

    # 4. Explainability, at least locally.
    explainer = Explainer(benchmark_problem, ps_catalog, pRef)
    explainer.explanation_loop(evaluated_sampled_solutions)

    print("And that concludes the showcase")



def mine_cohorts_and_write_to_file(benchmark_problem: BTProblem,
                                   cohort_output_file_name: str,
                                   scores_output_file_name: str,
                                   plots_of_run_file_name: Optional[str],
                                   nsga_pop_size: int,
                                   nsga_ngens: int,
                                   pRef_size: int,
                                   verbose=True):

    if verbose:
        print("Initialising mine_cohorts_and_write_to_file(")
        print(f"\tbenchmark_problem={benchmark_problem},")
        print(f"\toutput_file_name={cohort_output_file_name}")

    pss, scores, logbook = mine_pss_from_problem(benchmark_problem=benchmark_problem,
                                                 method="SA",
                                                 pRef_size=pRef_size,
                                                 nsga_pop_size=nsga_pop_size,
                                                 nsga_ngens=nsga_ngens,
                                                 verbose=verbose)

    detector = BTProblemPatternDetector(benchmark_problem)
    cohorts = [detector.ps_to_cohort(ps) for ps in pss]

    with announce(f"Writing the cohorts ({len(cohorts)} onto the file", verbose):
        cohort_data = cohorts_to_json(cohorts)
        os.makedirs(os.path.dirname(cohort_output_file_name), exist_ok=True)  # in case the directory does not exist
        with open(cohort_output_file_name, "w+") as file:
            json.dump(cohort_data, file)

    with announce(f"Writing the scores onto the file", verbose):
        headers = ["Simplicity", "Mean Fitness", "Atomicity"]
        with open(scores_output_file_name, mode='w+', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            for row in scores:
                writer.writerow(row)

    if plots_of_run_file_name is not None:
        plot_stats_for_run(logbook, plots_of_run_file_name, show_max=True, show_mean=True)
        without_max_filename = utils.prepend_to_file_name(plots_of_run_file_name, "only_mean")
        plot_stats_for_run(logbook, without_max_filename, show_max=False, show_mean=True)

    if verbose:
        print(f"Finished writing onto {cohort_output_file_name}, {scores_output_file_name}")

def analyse_cohort_data(benchmark_problem: BTProblem,
                        cohorts_json_file_name: str,
                        csv_file_name: str,
                        verbose=True):
    with announce(f"Reading the file {cohorts_json_file_name} to obtain the cohorts", verbose):
        cohorts = json_to_cohorts(cohorts_json_file_name)


    detector = BTProblemPatternDetector(benchmark_problem)
    control_cohorts = detector.generate_matching_random_cohorts(cohorts,
                                                                amount_to_generate=len(cohorts))


    analyse_data_from_json_cohorts(problem = benchmark_problem,
                                   real_cohorts=cohorts,
                                   control_cohorts=control_cohorts,
                                   output_csv_file_name = csv_file_name,
                                   verbose=verbose)



def run_for_bt_problem():
    experimental_directory = r"C:\Users\gac8\PycharmProjects\PS-PDF\Experimentation"
    current_directory = r"C:\Users\gac8\PycharmProjects\PS-PDF\Experimentation\Best"
    # current_directory = os.path.join(experimental_directory, "cohorts_"+utils.get_formatted_timestamp())
    cohort_file = os.path.join(current_directory, "cohort.json")
    scores_file = os.path.join(current_directory, "scores.csv")
    run_plot_file = os.path.join(current_directory, "run_plot.png")
    csv_file = os.path.join(current_directory, "analysis.csv")
    plot_file = os.path.join(current_directory, "shap.png")

    problem = EfficientBTProblem.from_default_files()
    #problem = RoyalRoad(3, 4)
    #show_overall_system(problem)
    # mine_cohorts_and_write_to_file(problem,
    #                                cohort_output_file_name=cohort_file,
    #                                scores_output_file_name=scores_file,
    #                                plots_of_run_file_name=run_plot_file,
    #                                nsga_pop_size=600,
    #                                nsga_ngens=600,
    #                                pRef_size=100000,
    #                                verbose=True)


    # show_interactive_3d_plot_of_scores(scores_file)

    # analyse_cohort_data(problem, cohort_file, csv_file, True)

    # cohorts = json_to_cohorts(cohort_file)
    # coverage = generate_coverage_stats(problem, cohorts)
    #
    # for worker_id in coverage:
    #     print(f"{worker_id}\t{coverage[worker_id]}")

    get_shap_values_plot(csv_file, plot_file)


if __name__ == '__main__':
    # problem = GraphColouring.random(amount_of_colours=3, amount_of_nodes=6, chance_of_connection=0.4)
    # print(f"Initialised the problem, which is {problem.long_repr()}")
    # problem.view()
    #
    # ps_catalog, scores, logbook = mine_pss_from_problem(benchmark_problem=problem,
    #                                                      method="SA",
    #                                                      pRef_size=10000,
    #                                                      nsga_pop_size=200,
    #                                                      nsga_ngens=100,
    #                                                      verbose=True)
    # report_in_order_of_last_metric(ps_catalog, problem, limit_to=12)
    run_for_bt_problem()