from typing import TypeAlias, Optional

import numpy as np

import SearchSpace
import utils
from PRef import PRef
from PS import PS, STAR
from PSMetric.Metric import Metric
from custom_types import ArrayOfFloats

LinkageTable: TypeAlias = np.ndarray


class SecondLinkage(Metric):
    linkage_table: Optional[LinkageTable]
    normalised_linkage_table: Optional[LinkageTable]

    def __init__(self):
        super().__init__()
        self.linkage_table = None
        self.normalised_linkage_table = None

    def __repr__(self):
        return "SecondLinkage"

    def set_pRef(self, pRef: PRef):
        self.linkage_table = self.get_linkage_table(pRef)
        self.normalised_linkage_table = self.get_normalised_linkage_table(self.linkage_table)

    @staticmethod
    def get_linkage_table(pRef: PRef) -> LinkageTable:
        median_fitness = np.median(pRef.fitness_array)
        total_successfull_count = pRef.sample_size // 2

        empty = PS.empty(pRef.search_space)
        trivial_pss = [[empty.with_fixed_value(var_index, val)
                        for val in range(cardinality)]
                       for var_index, cardinality in enumerate(pRef.search_space.cardinalities)]
        def get_successfull_proportion_for_ps(ps: PS) -> float:
            fitnesses = pRef.fitnesses_of_observations(ps)
            successes = [fitness for fitness in fitnesses if fitness > median_fitness]
            return len(successes) / total_successfull_count
        def interaction_effect_between_pss(ps_a, ps_b) -> float:
            score_a = get_successfull_proportion_for_ps(ps_a)
            score_b = get_successfull_proportion_for_ps(ps_b)
            expected_score = score_a + score_b - score_a*score_b
            score_ab = get_successfull_proportion_for_ps(PS.merge(ps_a, ps_b))

            return abs(score_ab - expected_score)

        def interaction_effect_between_vars(var_a: int, var_b: int) -> float:
            return sum([interaction_effect_between_pss(ps_a, ps_b)
                        for ps_b in trivial_pss[var_b]
                        for ps_a in trivial_pss[var_a]])

        linkage_table = np.zeros((pRef.search_space.amount_of_parameters, pRef.search_space.amount_of_parameters))
        for var_a in range(pRef.search_space.amount_of_parameters):
            for var_b in range(var_a, pRef.search_space.amount_of_parameters):
                linkage_table[var_a][var_b] = interaction_effect_between_vars(var_a, var_b)

        # then we mirror it for convenience...
        upper_triangle = np.triu(linkage_table, k=1)
        linkage_table = linkage_table + upper_triangle.T
        return linkage_table


    @staticmethod
    def get_normalised_linkage_table(linkage_table: LinkageTable):
        where_to_consider = np.triu(np.full_like(linkage_table, True, dtype=bool), k=1)
        triu_min = np.min(linkage_table, where=where_to_consider, initial=np.inf)
        triu_max = np.max(linkage_table, where=where_to_consider, initial=-np.inf)
        normalised_linkage_table: LinkageTable = (linkage_table - triu_min)/triu_max

        return normalised_linkage_table



    def get_linkage_scores(self, ps: PS) -> np.ndarray:
        fixed = ps.values != STAR
        fixed_combinations: np.array = np.outer(fixed, fixed)
        fixed_combinations = np.triu(fixed_combinations, k=1)
        return self.linkage_table[fixed_combinations]


    def get_normalised_linkage_scores(self, ps: PS) -> np.ndarray:
        fixed = ps.values != STAR
        fixed_combinations: np.array = np.outer(fixed, fixed)
        fixed_combinations = np.triu(fixed_combinations, k=1)
        return self.normalised_linkage_table[fixed_combinations]


    def get_single_score_using_avg(self, ps: PS) -> float:
        if ps.fixed_count() < 2:
            return 0
        else:
            return np.average(self.get_linkage_scores(ps))


    def get_single_normalised_score(self, ps: PS) -> float:
        if ps.fixed_count() < 2:
            return 0
        else:
            return np.average(self.get_normalised_linkage_scores(ps))

    def get_single_score(self, ps: PS) -> float:
        return self.get_single_score_using_avg(ps)
