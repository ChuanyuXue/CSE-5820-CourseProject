from distutils.log import error
from time import time
from typing import *
from src.utils import Time, Clock

_devices = []
_flows = []


class Link:

    def __init__(self, x: int, y: int) -> None:
        self.ingress_id = x
        self.egress_id = y

    def __len__(self, ) -> int:
        return 2

    def __iter__(self, ) -> int:
        yield self.ingress_id
        yield self.egress_id

    def __getitem__(self, x: int) -> int:
        if x == 0:
            return self.ingress_id
        elif x == 1:
            return self.egress_id
        else:
            return error("Index out of range")


class Frame:

    def __init__(self, id: int, flow_id: int, o: Time) -> None:
        self.id = id
        self.release_t = o
        self.flow_id = flow_id


class Flow:

    def __init__(self, id: int, p: Time, l: int, pcp: int,
                 route: Tuple[Link]) -> None:
        '''
        length: length in byte
        '''

        self.id = id
        self.pcp = pcp
        self.period = p
        self.length = l

        # self.frames = frames
        self.route = route


class Queue:

    def __init__(self, length: int = 32) -> None:
        self._data = []
        self.length = length

    def __getitem__(self, key: int) -> int:
        return self._data[key]

    def __len__(self, ) -> int:
        return len(self._data)

    def put(self, x: Frame) -> None:
        if len(self._data) > self.length:
            print("[!] Queue overflow")
        self._data.append(x)

    def get(self, ) -> Frame:
        return self._data.pop(0)


class GCL:

    def __init__(self, t: List[Time], p: Time, e: List[List[bool]]) -> None:
        self.gate_time = t
        self.gate_event = e
        self.period = p
        self.length = len(self.gate_time)

        self._max_time = Time(0, 0) + self.period

        ## Close time of gate i at t
        # self._close_time_map = {}
        # for i, t in range(len(self.gate_time)):
        #     for k, v in self.gate_event[i]:
        #         pass

    def get_current_status(self, t: Time) -> Tuple[List[bool], Time]:
        start = self._match_time(t=t)
        if start + 1 < self.length:
            return self.gate_event[start], self.gate_time[start + 1] - t
        else:
            return self.gate_event[
                start], self._max_time - t + self.gate_time[0]

    def _match_time(self, t: Time) -> int:
        '''
        Use binary search to quickly find the posistion of GCL
        '''

        ## Find time in GCL period
        while t > self.period:
            t -= self.period

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


class Egress:

    def __init__(self, id: int, speed: float, gcl: GCL, queue_nums: int,
                 neighbor: int, clock: Clock, queues: List[Queue],
                 pcp_to_prio: Dict[int, int], prio_to_tc: Dict[int,
                                                               int]) -> None:
        '''

        speed: bytes per-nanosecond
        neighbor: ID of adjancent device
        queues: ordered list of egress queues

        '''
        self.gcl = gcl
        self.speed = speed
        self.queue_nums = queue_nums if queue_nums else 8
        self.clock = clock
        self.queues = queues
        self.neighbor = neighbor
        self.pcp_to_prio = pcp_to_prio
        self.prio_to_tc = prio_to_tc
        self.tc_to_prio = {}
        for key, value in self.prio_to_tc.items():
            if value in self.tc_to_prio:
                print(
                    "[!] Warning: Priority to Traffic class is not one-to-one mapping!"
                )
            self.tc_to_prio[value] = key

        ## TODO: Make this as a HEAP
        ## (reg_time, frame)
        self._trans_rejister = []

    def run(self, t: Time) -> int:
        '''
        
        Core part of Qbv: Check the aviablity of queue pop based on GCL

        '''

        ## if current port is not aviable (transmitting data)
        if not self.clock.is_aviable:
            return -1

        status, left_time = self.gcl.get_current_status(
            t=self.clock.current_time)

        ## Check if the left time is still enough for frame [Look ahead]
        for i, v in enumerate(status):
            if v and not len(self.queues[i]):
                status[i] = False
            if v and len(self.queues[i]) and left_time < Time(
                    _flows[self.queues[i][0].flow_id].length / self.speed):
                status[i] = False

        ## Compete by priority
        _max_prio = -1
        _max_index = None
        for i, v in enumerate(status):
            if v and self.tc_to_prio[i] > _max_prio:
                _max_index = i
                _max_prio = self.tc_to_prio

        if _max_index != None:
            self.transmit(_max_index)

        ## Increase time
        self.clock.increase(t)

    def transmit(self, i: int):
        global _devices, _flows
        _trans_duration = Time(_flows[self.queues[i][0].flow_id].length /
                               self.speed)

        self._trans_rejister.append((
            _trans_duration,
            self.queues[i].get(),
        ))

        ## Only waitting here for transmition
        self.clock.wait(_trans_duration)

        for t, frame in self._trans_rejister:
            if t >= self.clock.current_time:
                _devices[self.neighbor].recv(frame)

    def recv(self, frame: Frame):
        global _flows
        pcp = _flows[frame.flow_id].pcp
        prio = self.pcp_to_prio[pcp]
        tc = self.prio_to_tc[prio]
        self.queues[tc].put(frame)


# class ingress:
#     '''
#     No ingress concept for now.
#     Currently replaced by device.recv function
#     '''

#     def __init__(self, ) -> None:
#         pass


class Device:

    def __init__(self, id: int, dev_type: int,
                 egress_ports: List[Egress]) -> None:
        self.id = id
        self.dev_type = dev_type
        self.egress_ports = egress_ports

    def _switching_fabric(self, frame: Frame) -> int:
        global _flows
        for x in _flows[frame.flow_id].route:
            a, b = x[0], x[1]
            if self.id == a:
                for eg in self.egress_ports:
                    if eg.neighbor == b:
                        eg.recv(frame)

    def run(self, t: Time) -> None:
        for i in self.egress_ports:
            i.run(t)

    def recv(self, frame: Frame) -> None:
        self._switching_fabric(frame)