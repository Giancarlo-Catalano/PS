import numpy as np

from BenchmarkProblems.BT.BTProblem import BTProblem
from BenchmarkProblems.EfficientBTProblem.EfficientBTProblem import EfficientBTProblem
from Core.PS import PS
from Explanation.BT.Cohort import ps_to_cohort
from Explanation.BT.cohort_measurements import get_hamming_distances, get_ranges_in_weekdays
from Explanation.Detector import Detector


class BTDetector(Detector):
    problem: EfficientBTProblem

    def __init__(self,
                 problem: EfficientBTProblem,
                 folder: str,
                 speciality_threshold: float,
                 verbose = False):
        super().with_folder(problem = problem,
                            folder = folder,
                            speciality_threshold = speciality_threshold,
                            verbose = verbose)

    def ps_to_properties(self, ps: PS) -> dict:
        cohort = ps_to_cohort(self.problem, ps)

        mean_rota_choice_amount = np.average([member.get_amount_of_choices() for member in cohort])
        mean_amount_of_hours = np.average(member.get_amount_of_working_hours() for member in cohort)
        mean_hamming_distance = np.average(get_hamming_distances(cohort))
        local_fitness = np.average(get_ranges_in_weekdays(cohort))

        return {"mean_rota_choice_quantity": mean_rota_choice_amount,
                "mean_amount_of_hours": mean_amount_of_hours,
                "mean_difference_in_rotas": mean_hamming_distance,
                "local_fitness": local_fitness}