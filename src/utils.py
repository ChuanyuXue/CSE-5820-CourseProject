from __future__ import annotations

from re import T
import secrets
from typing import Union


class Time_duration:

    def __init__(self, nano: int) -> None:
        self.second = nano // 1e9
        self.nanosecond = nano % 1e9

    def __repr__(self, ) -> str:
        return "%d.%09d" % (self.second, self.nanosecond)

    def __eq__(self, t: Union[Time_point, Time_duration]) -> bool:
        return self.second * 1e9 + self.nanosecond == t.second * 1e9 + t.nanosecond

    def __gt__(self, t: Union[Time_point, Time_duration]) -> bool:
        return self.second * 1e9 + self.nanosecond > t.second * 1e9 + t.nanosecond

    def __ge__(self, t: Union[Time_point, Time_duration]) -> bool:
        return self.second * 1e9 + self.nanosecond >= t.second * 1e9 + t.nanosecond


class Time_point:

    def __init__(self, sec: int, nano: int) -> None:
        self.second = sec
        self.nanosecond = nano

    def _normalize(self, ) -> Time_point:
        while self.nanosecond >= 1e9:
            self.second += 1
            self.nanosecond -= 1e9
        while self.nanosecond < 0:
            self.second -= 1
            self.nanosecond += 1e9
        return self

    def __add__(self, t: Union[Time_point, Time_duration]) -> bool:
        return Time_point(self.second + t.second,
                          self.nanosecond + t.nanosecond)._normalize()

    def __sub__(self, t: Union[Time_point, Time_duration]) -> bool:
        return Time_point(self.second - t.second,
                          self.nanosecond - t.nanosecond)._normalize()

    def __gt__(self, t: Time_point) -> bool:
        return self.second * 1e9 + self.nanosecond > t.second * 1e9 + t.nanosecond

    def __ge__(self, t: Time_point) -> bool:
        return self.second * 1e9 + self.nanosecond >= t.second * 1e9 + t.nanosecond

    def __eq__(self, t: Time_point) -> bool:
        return self.second == t.second and self.nanosecond == t.nanosecond

    def __repr__(self, ) -> str:
        return "%d.%09d" % (self.second, self.nanosecond)


class Clock:

    def __init__(self, t: Time_point) -> None:
        self.current_time = t
        self.aviable_t = t
        self.is_aviable = True

    def increase(self, t: Time_duration) -> None:
        self.current_time += t
        if self.current_time > self.aviable_t:
            self.is_aviable = True

    def wait(self, t: Time_duration) -> None:
        self.aviable_t = self.current_time + t
        self.is_aviable = False