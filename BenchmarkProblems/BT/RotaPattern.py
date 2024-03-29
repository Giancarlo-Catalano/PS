from typing import Optional

import numpy as np


class WorkDay:
    working: bool
    start_time: Optional[int]   # ignored for now
    end_time: Optional[int]     # ignored for now


    def __init__(self, working: bool, start_time: Optional[int], end_time: Optional[int]):
        self.working = working
        self.start_time = start_time
        self.end_time = end_time


    @classmethod
    def working_day(cls, start_time, end_time):
        return cls(True, start_time, end_time)

    @classmethod
    def not_working(cls):
        return cls(False, None, None)

    def __repr__(self):
        if self.working:
            return f"{self.start_time}~{self.end_time}"
        else:
            return "----"

class RotaPattern:
    workweek_length: int
    days: list[WorkDay]

    def __init__(self, workweek_length: int, days: list[WorkDay]):
        assert(len(days) % workweek_length == 0)
        self.workweek_length = workweek_length
        self.days = days


    def __repr__(self):
        split_by_week = [self.days[(which*self.workweek_length):(which+1*self.workweek_length)]
                          for which in range(len(self.days) // self.workweek_length)]

        def repr_week(week: list[WorkDay]) -> str:
            return "<" + ", ".join(f"{day}" for day in week)+">"

        return ", ".join(map(repr_week, split_by_week))

    def with_starting_day(self, starting_day: int):
        if (starting_day >= len(self.days)):
            print("FUCK")
        assert(starting_day < len(self.days))
        return RotaPattern(self.workweek_length, self.days[starting_day:]+self.days[:starting_day])

    def with_starting_week(self, starting_week: int):
        return self.with_starting_day(starting_week * self.workweek_length)

    def as_bools(self) -> list[bool]:
        return [day.working for day in self.days]

    def working_days_in_calendar(self, calendar_length: int) -> np.ndarray:
        result = []
        as_bools = self.as_bools()
        while len(result) < calendar_length:
            result.extend(as_bools)

        return np.array(result[:calendar_length])


    def __len__(self):
        return len(self.days)


def get_workers_present_each_day_of_the_week(rotas: list[RotaPattern], calendar_length: int) -> np.ndarray:
    all_rotas = np.array([rota.working_days_in_calendar(calendar_length) for rota in rotas])
    workers_per_day = np.sum(all_rotas, axis=0, dtype=int)

    return workers_per_day.reshape((-1, 7))


def get_range_scores(workers_per_weekday: np.ndarray):
    maxs = np.max(workers_per_weekday, axis=0)
    mins = np.min(workers_per_weekday, axis=0)

    def range_score(min_amount, max_amount):
        if max_amount == 0:
            return 0
        return (max_amount - min_amount) / max_amount

    return [range_score(min_amount, max_amount) for min_amount, max_amount in zip(mins, maxs)]







