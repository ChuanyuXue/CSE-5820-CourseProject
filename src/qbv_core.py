from distutils.log import error
from time import time
from typing import Dict, List, Tuple
import src.var as var
from src.utils import Time, Clock


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

    def __init__(self, id: int, p: Time, o: Time, l: int, pcp: int,
                 route: Tuple[Link]) -> None:
        '''
        length: length in byte
        '''

        self.id = id
        self.pcp = pcp
        self.period = p
        self.offset = o
        self.length = l

        # self.frames = frames
        # ([a,b],[b,c],[c,d]...)
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
        # if len(self._data) > self.length:
        #     print("[!] Queue overflow")
        self._data.append(x)

    def get(self, ) -> Frame:
        return self._data.pop(0)


class GCL:

    def __init__(self, t: List[Time], p: Time, e: List[List[bool]]) -> None:
        '''

        gate_time = [Time0, Time1, Time2, ... , TimeN]

        e = [
                [True, False, ...., ]
        ]
        
        p = period

        '''
        self.gate_time = t
        self.gate_event = e
        self.period = p
        self.length = len(self.gate_time)

        ## Close time of gate i at t
        # self._close_time_map = {}
        # for i, t in range(len(self.gate_time)):
        #     for k, v in self.gate_event[i]:
        #         pass

    def get_current_status(self, t: Time) -> Tuple[List[bool], Time]:
        ## Find time in GCL period
        t = t % self.period

        start = self._match_time(t=t)
        if start + 1 < self.length:
            return self.gate_event[start], self.gate_time[start + 1] - t
        else:
            return self.gate_event[start], self.period - t

    def _match_time(self, t: Time) -> int:
        '''
        Use binary search to quickly find the posistion of GCL
        '''
        left = 0
        right = self.length - 1
        if t >= self.gate_time[right]:
            return right

        while True:
            median = (left + right) // 2
            if right - left <= 1:
                return left
            elif self.gate_time[left] <= t < self.gate_time[median]:
                right = median
            else:
                left = median


class Egress:

    def __init__(self, id: int, dev_id: int, speed: float, gcl: GCL,
                 queue_nums: int, neighbor: int, clock: Clock,
                 queues: List[Queue], pcp_to_prio: Dict[int, int],
                 prio_to_tc: Dict[int, int]) -> None:
        '''

        speed: bytes per-nanosecond
        neighbor: ID of adjancent device
        queues: ordered list of egress queues

        '''
        self.id = id
        self.dev_id = dev_id
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

        self._transmitting = None

    def trans(self, ):
        ## Transmit frame to next hop in the predicted time
        if self.clock.is_aviable and self._transmitting:
            var._devices[self.neighbor].recv(self._transmitting)

            self._transmitting = None

    def run(self, t: Time) -> int:
        '''
        
        Core part of Qbv: Check the aviablity of queue pop based on GCL

        '''

        status, left_time = self.gcl.get_current_status(
            t=self.clock.current_time)

        ## Only keep the first `self.queue_nums` gate status
        status = status[:self.queue_nums]

        ## Check if the left time is still enough for frame [Look ahead]
        for i, v in enumerate(status):
            if v and not len(self.queues[i]):
                status[i] = False
            if v and len(self.queues[i]) and left_time < Time(
                    var._flows[self.queues[i][0].flow_id].length / self.speed):
                status[i] = False

        ## Compete by priority
        _max_prio = -1
        _max_index = None
        for i, v in enumerate(status):
            if v and self.tc_to_prio[i] > _max_prio:
                _max_index = i
                _max_prio = self.tc_to_prio[i]

        ## Pop frame from queue and sent it from port
        if _max_index != None and self.clock.is_aviable:
            _trans_duration = Time(
                var._flows[self.queues[_max_index][0].flow_id].length /
                self.speed)
            self._transmitting = self.queues[_max_index].get()

            ## Only waitting here for transmition
            self.clock.wait(_trans_duration)

        ## Increase time
        self.clock.increase(t)

    def recv(self, frame: Frame):
        pcp = var._flows[frame.flow_id].pcp
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
        ## 'talker' / 'bridge' / 'listener'
        self.dev_type = dev_type
        self.egress_ports = egress_ports
        self.clock = Clock(Time(0))

    def _switching_fabric(self, frame: Frame) -> int:
        for x in var._flows[frame.flow_id].route:
            a, b = x[0], x[1]
            if self.id == a:
                for eg in self.egress_ports:
                    if eg.neighbor == b:
                        eg.recv(frame)

    def run(self, t: Time) -> None:
        for i in self.egress_ports:
            i.trans()
        for i in self.egress_ports:
            i.run(t)
        self.clock.increase(t)

    def recv(self, frame: Frame) -> None:
        # print("[Time %s] Flow %d --- Frame %d is received in Dev %d" %
        #       (str(self.clock.current_time), frame.flow_id, frame.id, self.id))

        if self.dev_type == 'listener':
            var._reward += 1e6 / int(self.clock.current_time - frame.release_t)
            # var._reward += 1
        else:
            self._switching_fabric(frame)