from re import T
import secrets
from typing import Union


class time_duration:

    def __init__(self, nano: int) -> None:
        self.second = nano // 1e9
        self.nanoscrond = nano % 1e9


class time_point:

    def __init__(self, sec: int, nano: int) -> None:
        self.second = sec
        self.nanosecond = nano

    def _normalize(self, ) -> time_point:
        while self.nanosecond >= 1e9:
            self.second += 1
            self.nanosecond -= 1e9
        while self.nanosecond < 0:
            self.second -= 1
            self.nanosecond += 1e9
        return self

    def __add__(self, t: time_duration):
        if not isinstance(t, time_duration):
            print("[!]Warning: ", type(t),
                  " is no supported by time point __add__ operation")
        return time_point(self.second + t.second,
                          self.nanosecond + t.nanoscrond)._normalize()

    def __sub__(self, t: Union[time_point, time_duration]):
        return time_point(self.second - t.second,
                          self.nanosecond - t.nanoscrond)._normalize()

    def __gt__(self, t: time_point):
        return self.second * 1e9 + self.nanosecond > t.second * 1e9 + self.nanosecond

    def __lt__(self, t: time_point):
        return self.second * 1e9 + self.nanosecond < t.second * 1e9 + self.nanosecond

    def __eq__(self, t: time_point) -> bool:
        return self.second == t.second and self.nanosecond == t.nanosecond


class clock:

    def __init__(self, t: time_point) -> None:
        self.current_time = t
        self.aviable_t = t
        self.is_aviable = True

    def increase(self, t: time_duration) -> None:
        self.current_time += t
        if self.current_time > self.aviable_t:
            self.is_aviable = True

    def wait(self, t: time_duration) -> None:
        self.aviable_t = self.current_time + t
        self.is_aviable = False
