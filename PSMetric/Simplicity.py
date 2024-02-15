import numpy as np

from PRef import PRef
from PS import PS, STAR
from PSMetric.Metric import Metric


class Simplicity(Metric):
    def __init__(self):
        super().__init__()

    def __repr__(self):
        return "Simplicity"

    def set_pRef(self, pRef: PRef):
        pass

    def get_single_score(self, ps: PS) -> float:
        return float(np.sum(ps.values == STAR))

    def get_single_normalised_score(self, ps: PS) -> float:
        return 1.0 - float(np.sum(ps.values == STAR) / len(ps))
