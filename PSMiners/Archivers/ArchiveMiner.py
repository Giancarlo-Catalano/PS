import heapq
import random
import warnings
from math import ceil

from pandas import DataFrame

import utils
from BenchmarkProblems.BenchmarkProblem import BenchmarkProblem
from PRef import PRef
from PS import PS
from PSMetric.Atomicity import Atomicity
from PSMetric.Linkage import Linkage
from PSMetric.MeanFitness import MeanFitness
from PSMetric.Metric import MultipleMetrics
from PSMetric.Simplicity import Simplicity
from PSMiners.Individual import Individual, add_metrics, with_aggregated_scores, add_normalised_metrics, \
    with_average_score, with_product_score, partition_by_simplicity
from SearchSpace import SearchSpace
from TerminationCriteria import TerminationCriteria, EvaluationBudgetLimit
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import plotly.express as px


class ArchiveMiner:
    population_size: int
    metrics: MultipleMetrics

    current_population: list[Individual]
    archive: set[PS]

    selection_proportion = 0.3
    tournament_size = 3

    search_space: SearchSpace

    def __init__(self,
                 population_size: int,
                 pRef: PRef,
                 metrics=None):
        self.search_space = pRef.search_space
        self.population_size = population_size
        if metrics is None:
            self.metrics = MultipleMetrics([Simplicity(), MeanFitness(), Linkage()])
        else:
            self.metrics = metrics
        self.metrics.set_pRef(pRef)

        print(f"Initialised the ArchiveMiner with metrics {self.metrics.get_labels()}")

        self.current_population = self.calculate_metrics_and_aggregated_score(self.make_initial_population())
        self.archive = set()

    def calculate_metrics_and_aggregated_score(self, population: list[Individual]) -> list[Individual]:
        for individual in population:
            scores = self.metrics.get_normalised_scores(individual.ps)
            individual.metric_scores = scores
            individual.aggregated_score = self.metrics.get_aggregated_score(scores)
        return population

    def make_initial_population(self) -> list[Individual]:
        """ basically takes the elite of the PRef, and converts them into PSs """
        """this is called get_init in the paper"""
        return [Individual(PS.empty(self.search_space))]

    def get_localities(self, ps: PS) -> list[PS]:
        return ps.specialisations(self.search_space)

    def select_one(self) -> PS:
        tournament_pool = random.choices(self.current_population, k=self.tournament_size)
        winning_individual = max(tournament_pool, key=lambda x: x.aggregated_score)
        return winning_individual.ps

    @staticmethod
    def top(evaluated_population: list[Individual], amount: int) -> list[Individual]:
        return heapq.nlargest(amount, evaluated_population, key=lambda x: x.aggregated_score)

    def make_new_population_efficient(self):
        """Note how this relies on the current population being evaluated,
                and how at the end it returns an evaluated population"""
        selected = [self.select_one() for _ in range(ceil(self.population_size * self.selection_proportion))]
        localities = [local for ps in selected
                      for local in self.get_localities(ps)]
        self.archive.update(selected)

        # make a population with the current + localities
        new_population = self.current_population + self.calculate_metrics_and_aggregated_score(
            [Individual(ps) for ps in localities])

        # remove selected individuals and those in the archive
        new_population = [ind for ind in new_population if ind.ps not in self.archive]

        # remove duplicates
        new_population = list(set(new_population))

        # convert to individual and evaluate
        # new_population = self.calculate_metrics_and_aggregated_score(new_population)

        return self.top(new_population, self.population_size)

    def make_new_population(self):
        return self.make_new_population_efficient()

    def show_best_of_current_population(self, how_many: int):
        best = self.top(self.current_population, how_many)
        for individual in best:
            print(individual)

    def run(self,
            termination_criteria: TerminationCriteria,
            show_each_generation=False):
        iteration = 0

        def termination_criteria_met():
            if len(self.current_population) == 0:
                warnings.warn("The run is ending because the population is empty!!!")
                return True

            return termination_criteria.met(iterations=iteration,
                                            evaluations=self.get_used_evaluations(),
                                            evaluated_population=self.current_population)  # TODO change this

        while not termination_criteria_met():
            self.current_population = self.make_new_population()
            if show_each_generation:
                print(f"Population at iteration {iteration}, used_budget = {self.get_used_evaluations()}--------------")
                self.show_best_of_current_population(12)
            iteration += 1

        print(f"Execution terminated with {iteration = } and used_budget = {self.get_used_evaluations()}")

    def get_results(self, quantity_returned=None) -> list[(PS, float)]:
        if quantity_returned is None:
            quantity_returned = len(self.archive)
        evaluated_archive = self.calculate_metrics_and_aggregated_score([Individual(ps) for ps in self.archive])
        return self.top(evaluated_archive, quantity_returned)

    def get_used_evaluations(self) -> int:
        return self.metrics.used_evaluations


def show_plot_of_individuals(individuals: list[Individual], metrics: MultipleMetrics):
    labels = metrics.get_labels()
    points = [i.metric_scores for i in individuals]

    utils.make_interactive_3d_plot(points, labels)


def test_archive_miner(problem: BenchmarkProblem,
                       show_each_generation=True,
                       show_interactive_plot = False,
                       metrics=None):
    print(f"Testing the modified archive miner")
    pRef: PRef = problem.get_pRef(15000)

    budget_limit = EvaluationBudgetLimit(15000)
    # iteration_limit = TerminationCriteria.IterationLimit(12)
    # termination_criteria = TerminationCriteria.UnionOfCriteria(budget_limit, iteration_limit)

    if metrics is None:
        metrics = MultipleMetrics(metrics=[Simplicity(), MeanFitness(), Linkage()],
                                  weights=[1, 2, 1])

    miner = ArchiveMiner(150,
                         pRef,
                         metrics=metrics)

    miner.run(budget_limit, show_each_generation=show_each_generation)

    results = miner.get_results()
    # print("The results of the archive miner are:")
    # for individual in results:
    #     print(f"{individual}")

    print(f"The used budget is {miner.get_used_evaluations()}")

    if show_interactive_plot:
        print("Displaying the plot")
        show_plot_of_individuals(results, miner.metrics)

    print("Partitioned by complexity, the PSs are")
    for fixed_count, pss in enumerate(partition_by_simplicity(results)):
        if len(pss) > 0:
            print(f"With {fixed_count} fixed vars: --------")
            for individual in pss:
                print(individual)

    print("The top 12 by mean fitness are")
    sorted_by_mean_fitness = sorted(results, key=lambda i: i.aggregated_score, reverse=True)
    for individual in sorted_by_mean_fitness[:12]:
        print(individual)
