from BenchmarkProblems.UnitaryProblem import UnitaryProblem


class RoyalRoad(UnitaryProblem):

    def __init__(self, amount_of_cliques: int, clique_size: int):
        super().__init__(amount_of_cliques, clique_size)

    def get_problem_name(self) -> str:
        return "RoyalRoad"

    def unitary_function(self, bitcount: int) -> float:
        if bitcount == self.clique_size:
            return float(self.clique_size)
        else:
            return 0.0

