from typing import Iterable

import numpy as np

from PRef import PRef
from PS import PS
from custom_types import ArrayOfFloats


class Metric:
    used_evaluations: int

    def __init__(self):
        self.used_evaluations = 0
    def __repr__(self):
        """ Return a string which describes the Criterion, eg 'Robustness' """
        raise Exception(f"Error: a realisation of PSMetric does not implement __repr__")

    def set_pRef(self, pRef: PRef):
        raise Exception(f"Error: a realisation of PSMetric({self.__repr__()}) does not implement set_pRef")

    def get_single_score(self, ps: PS) -> float:
        raise Exception(f"Error: a realisation of PSMetric({self.__repr__()}) does not implement get_single_score_for_PS")

    def get_single_normalised_score(self, ps: PS) -> float:  #
        raise Exception(f"Error: a realisation of PSMetric({self.__repr__()}) does not implement get_single_normalised_score")

    def get_unnormalised_scores(self, pss: Iterable[PS]) -> ArrayOfFloats:
        """default implementation, subclasses might overwrite this"""
        return np.array([self.get_single_score(ps) for ps in pss])


class MultipleMetrics(Metric):
    metrics: list[Metric]
    used_evaluations: int
    weights: list[int]

    def __init__(self, metrics: list[Metric], weights = None):
        self.metrics = metrics
        self.used_evaluations = 0
        if weights is None:
            self.weights = [1 for _ in metrics]
        else:
            self.weights = weights

        super().__init__()

    def get_labels(self) -> list[str]:
        return [m.__repr__() for m in self.metrics]

    def set_pRef(self, pRef: PRef):
        for m in self.metrics:
            m.set_pRef(pRef)

    def __repr__(self):
        return f"MultipleMetrics({' '.join(self.get_labels())})"

    def get_scores(self, ps: PS) -> list[float]:
        self.used_evaluations += 1
        return [m.get_single_score(ps) for m in self.metrics]


    def get_normalised_scores(self, ps: PS) -> list[float]:
        self.used_evaluations += 1
        return [m.get_single_normalised_score(ps) for m in self.metrics]


    def get_amount_of_metrics(self) -> int:
        return len(self.metrics)


    def get_aggregated_score(self, score_list: list[float]):
        return sum([score * weight for score, weight in zip(score_list, self.weights)]) / sum(self.weights)



class AlwaysNormalised(Metric):
    metric: Metric


    def __repr__(self):
        return f"Normalised({self.metric.__repr__()})"

    def __init__(self, metric: Metric):
        self.metric = metric
        super().__init__()

    def set_pRef(self, pRef: PRef):
        self.metric.set_pRef(pRef)

    def get_single_score(self, ps: PS) -> float:
        return self.metric.get_single_normalised_score(ps)   # and this is the entire purpose of the class
