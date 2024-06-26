import random

import numpy as np
from pymoo.core.crossover import Crossover
from pymoo.core.mutation import Mutation
from pymoo.core.variable import Real, get
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PolynomialMutation
from pymoo.operators.sampling.rnd import FloatRandomSampling

from Core.SearchSpace import SearchSpace


class PSGeometricSampling(FloatRandomSampling):

    def generate_single_individual(self, n, xu) -> np.ndarray:
        result_values = np.full(shape=n, fill_value=-1)  # the stars
        chance_of_success = 0.79
        while random.random() < chance_of_success:
            var_index = random.randrange(n)
            new_value = random.randrange(xu[var_index]+1)
            result_values[var_index] = new_value
        return result_values

    def _do(self, problem, n_samples, **kwargs):
        n, (xl, xu) = problem.n_var, problem.bounds()
        return np.array([self.generate_single_individual(n, xu) for _ in range(n_samples)])


# ---------------------------------------------------------------------------------------------------------
# Class
# ---------------------------------------------------------------------------------------------------------


class PSPolynomialMutation(Mutation):
    search_space: SearchSpace
    single_point_probability: float

    def __init__(self, search_space: SearchSpace, prob=None):
        self.search_space = search_space
        if prob is None:
            prob = 1 / self.search_space.amount_of_parameters
        self.single_point_probability = prob
        super().__init__(prob=0.9)  # no idea what's supposed to be there, but it used to say 0.9 by default..


    def mutate_single_individual(self, x: np.ndarray) -> np.ndarray:
        result_values = x.copy()
        for index, _ in enumerate(result_values):
            if random.random() < self.single_point_probability:
                new_value = random.randrange(self.search_space.cardinalities[index])
                result_values[index] = new_value

        return result_values

    def _do(self, problem, X, params=None, **kwargs):
        result_values = X.copy()
        for index, row in enumerate(result_values):
            result_values[index] = self.mutate_single_individual(row)

        return result_values


def ps_sbx_mate(mother:np.ndarray, father:np.ndarray):
    daughter = mother.copy()
    son = father.copy()

    for index, _ in enumerate(daughter):
        if random.random() < 0.5:
            daughter[index], son[index] = son[index], daughter[index]

    return (daughter, son)


# ---------------------------------------------------------------------------------------------------------
# Class
# ---------------------------------------------------------------------------------------------------------


class PSSimulatedBinaryCrossover(Crossover):

    def __init__(self,
                 n_offsprings=2,
                 **kwargs):
        super().__init__(2, n_offsprings, **kwargs)


    def _do(self, problem, X, **kwargs):
        _, n_matings, _ = X.shape


        children = np.array([ps_sbx_mate(mother, father)
                    for mother, father in zip(X[0], X[1])])

        return np.swapaxes(children, 0, 1)


