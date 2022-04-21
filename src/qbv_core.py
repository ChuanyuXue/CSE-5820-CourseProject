from distutils.log import error
from time import time
from typing import *

from src.utils import time_duration, time_point, clock

_devices = []
_flows = []


class link:

    def __init__(self, x: int, y: int) -> None:
        self.ingress_id = x
        self.egress_id = y

    def __getitem__(self, x: int) -> int:
        if x == 0:
            return self.ingress_id
        elif x == 1:
            return self.egress_id
        else:
            return error("Index out of range")


class frame:

    def __init__(self, id: int, flow_id: int, o: time_point) -> None:
        self.id = id
        self.release_t = o
        self.flow_id = flow_id


class flow:

    def __init__(self, id: int, p: time_duration, l: int, pcp: int,
                 frames: Tuple[frame], route: Tuple[link]) -> None:
        self.id = id
        self.pcp = pcp
        self.period = p
        self.length = l

        self.frames = frames
        self.route = route


class queue:

    def __init__(self, length: int = 32) -> None:
        self._data = []
        self.length = length

    def __getitem__(self, key: int) -> int:
        return self._data[key]

    def put(self, x: frame) -> None:
        self._data.append(x)

    def get(self, ) -> frame:
        return self._data.pop(0)


class gcl:

    def __init__(self, t: List[time_point], p: time_duration,
                 e: List[List[bool]]) -> None:
        self.gate_time = t
        self.gate_event = e
        self.period = p
        self.length = len(self.gate_time)

        self._max_time = t(0, 0) + self.period

        ## Close time of gate i at t
        self._close_time_map = {}
        for i, t in range(self.gate_time):
            for k, v in self.gate_event[i]:
                pass

    def get_current_status(self,
                           t: time_point) -> Tuple[List[bool], time_duration]:
        start = self._match_time(t)
        if start + 1 < self.length:
            return self.gate_event[start], self.gate_time[start + 1] - t
        else:
            return self.gate_event[
                start], self._max_time - t + self.gate_time[0]

    @staticmethod
    def _match_time(self, t: time_point) -> int:
        '''
        Use binary search to quickly find the posistion of GCL
        '''
        left = 0
        right = self.length - 1
        if t < self.gate_time[left] or t > self.gate_time[right]:
            return right

        while True:
            median = (left + right) // 2
            if right - left == 1:
                return left
            elif self.gate_time[left] <= t < self.gate_time[median]:
                right = median
            else:
                left = median


class egress:

    def __init__(self, id: int, speed: float, gcl: gcl, queue_nums: int,
                 neighbor: int, clock: clock, queues: List[queue],
                 pcp_to_prio: Dict[int:int],
                 prio_to_tc: Dict[int:int]) -> None:
        '''

        speed: bytes per-nanosecond
        neighbor: ID of adjancent device
        queues: ordered list of egress queues

        '''
        self.id = id
        self.gcl = gcl
        self.speed = speed
        self.queue_nums = queue_nums if queue_nums else 8
        self.clock = clock
        self.queues = queues
        self.neighbor = neighbor
        self.pcp_to_prio = pcp_to_prio
        self.prio_to_tc = prio_to_tc
        self.tc_to_prio = {}
        for key, value in self.tc_to_prio.items():
            if value in self.tc_to_prio:
                print(
                    "[!] Warning: Priority to Traffic class is not one-to-one mapping!"
                )
            self.tc_to_prio[value] = key

    def check_aviable(self, ) -> int:
        '''
        
        Core part of Qbv: Check the aviablity of queue pop based on GCL

        '''

        ## if current port is not aviable (transmitting data)
        if not self.clock.is_aviable:
            return -1
        status, left_time = self.gcl.get_current_status(
            self.clock.current_time)

        ## Check if the left time is still enough for frame
        for i, v in status:
            if v and left_time < self.queues[i][0].length / self.speed:
                status[i] = False

        ## Compete by priority
        _max_prio = -1
        _max_index = None
        for i, v in status:
            if self.tc_to_prio[i] > _max_prio:
                _max_index = i
                _max_prio = self.tc_to_prio

        if _max_index >= 0:
            self.transmit(_max_index)

    def transmit(self, i: int):
        frame = self.queues[i].get()
        for a, b in _flows[frame.flow_id].route:
            if self.id == a:
                _devices[b].recv(frame)


# class ingress:
#     '''
#     No ingress concept for now.
#     Currently replaced by device.recv function
#     '''

#     def __init__(self, ) -> None:
#         pass


class device:

    def __init__(self, id: int, egress_ports: List[egress]) -> None:
        self.id = id
        self.egress_ports = egress_ports

    def recv(self, frame: frame) -> None:
        pass
