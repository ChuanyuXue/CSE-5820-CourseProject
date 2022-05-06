from __future__ import annotations

from re import T
from typing import Union


class Time:

    def __init__(self, nano: int, sec: int = 0) -> None:
        self.second = sec
        self.nanosecond = nano
        self._normalize()

    def __int__(self, ) -> int:
        return int(self.second * 1e9 + self.nanosecond)

    def _normalize(self, ) -> Time:
        while self.nanosecond >= 1e9:
            self.second += 1
            self.nanosecond -= 1e9
        while self.nanosecond < 0:
            self.second -= 1
            self.nanosecond += 1e9
        return self

    def __add__(self, t: Time) -> Time:
        return Time(sec=self.second + t.second,
                    nano=self.nanosecond + t.nanosecond)._normalize()

    def __sub__(self, t: Time) -> Time:
        return Time(sec=self.second - t.second,
                    nano=self.nanosecond - t.nanosecond)._normalize()

    def __truediv__(self, t: Time) -> int:
        return (self.second * 1e9 + self.nanosecond) / (t.second * 1e9 +
                                                        t.nanosecond)

    def __mul__(self, fac: int) -> Time:
        return Time(sec=self.second * fac,
                    nano=self.nanosecond * fac)._normalize()

    def __mod__(self, t: Time) -> Time:
        return Time(nano=(self.second * 1e9 + self.nanosecond) %
                    (t.second * 1e9 + t.nanosecond))._normalize()

    def __gt__(self, t: Time) -> bool:
        return self.second * 1e9 + self.nanosecond > t.second * 1e9 + t.nanosecond

    def __lt__(self, t: Time) -> bool:
        return self.second * 1e9 + self.nanosecond < t.second * 1e9 + t.nanosecond

    def __ge__(self, t: Time) -> bool:
        return self.second * 1e9 + self.nanosecond >= t.second * 1e9 + t.nanosecond

    def __le__(self, t: Time) -> bool:
        return self.second * 1e9 + self.nanosecond <= t.second * 1e9 + t.nanosecond

    def __eq__(self, t: Union[Time, int]) -> bool:
        if isinstance(t, int):
            return self.second * 1e9 + self.nanosecond == t
        elif isinstance(t, Time):
            return self.second == t.second and self.nanosecond == t.nanosecond

    def __repr__(self, ) -> str:
        return "%d.%09d" % (self.second, self.nanosecond)


# class Time_duration:

#     def __init__(self, nano: int) -> None:
#         self.second = nano // 1e9
#         self.nanosecond = nano % 1e9

#     def __repr__(self, ) -> str:
#         return "%d.%09d" % (self.second, self.nanosecond)

#     def __eq__(self, t: Union[Time_point, Time_duration]) -> bool:
#         return self.second * 1e9 + self.nanosecond == t.second * 1e9 + t.nanosecond

#     def __gt__(self, t: Union[Time_point, Time_duration]) -> bool:
#         return self.second * 1e9 + self.nanosecond > t.second * 1e9 + t.nanosecond

#     def __ge__(self, t: Union[Time_point, Time_duration]) -> bool:
#         return self.second * 1e9 + self.nanosecond >= t.second * 1e9 + t.nanosecond

# class Time_point:

#     def __init__(self, sec: int, nano: int) -> None:
#         self.second = sec
#         self.nanosecond = nano

#     def _normalize(self, ) -> Time_point:
#         while self.nanosecond >= 1e9:
#             self.second += 1
#             self.nanosecond -= 1e9
#         while self.nanosecond < 0:
#             self.second -= 1
#             self.nanosecond += 1e9
#         return self

#     def __add__(self, t: Union[Time_point, Time_duration]) -> bool:
#         return Time_point(self.second + t.second,
#                           self.nanosecond + t.nanosecond)._normalize()

#     def __sub__(self, t: Union[Time_point, Time_duration]) -> bool:
#         return Time_point(self.second - t.second,
#                           self.nanosecond - t.nanosecond)._normalize()

#     def __gt__(self, t: Time_point) -> bool:
#         return self.second * 1e9 + self.nanosecond > t.second * 1e9 + t.nanosecond

#     def __ge__(self, t: Time_point) -> bool:
#         return self.second * 1e9 + self.nanosecond >= t.second * 1e9 + t.nanosecond

#     def __eq__(self, t: Time_point) -> bool:
#         return self.second == t.second and self.nanosecond == t.nanosecond

#     def __repr__(self, ) -> str:
#         return "%d.%09d" % (self.second, self.nanosecond)


class Clock:

    def __init__(self, t: Time) -> None:
        self.current_time = t
        self.aviable_t = t
        self.is_aviable = True

    def increase(self, t: Time) -> None:
        self.current_time += t
        if self.current_time >= self.aviable_t:
            self.is_aviable = True

    def wait(self, t: Time) -> None:
        self.aviable_t = self.current_time + t
        self.is_aviable = False