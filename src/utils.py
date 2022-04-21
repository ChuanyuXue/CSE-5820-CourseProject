from re import T


class time_duration:

    def __init__(self) -> None:
        pass


class time_point:

    def __init__(self, sec: int, nano: int) -> None:
        self.second = sec
        self.nanosecond = nano


class clock:

    def __init__(self, t: time_point) -> None:
        self.current_time = t
        self.aviable_t = t
        self.is_aviable = True

    def increase(self, t: time_duration) -> None:
        pass
