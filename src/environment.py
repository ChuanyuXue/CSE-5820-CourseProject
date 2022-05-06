import math
import json
from operator import index
from src import qbv_core
import src.var as var
from src.qbv_core import GCL, Device, Egress, Flow, Frame, Link, Queue
from src.utils import Clock, Time
from random import randint

ENV_PATH = "configs/env.json"
NETWORK_PATH = "configs/network.json"
TRAFFIC_PATH = "configs/traffic.json"


def load_gcl(path: str) -> GCL:
    with open(path) as f:
        _t = []
        _e = []
        _time = Time(0, 0)
        for line in f.readlines():
            _, t, s = line.split()
            _e.append([True if x == '1' else False for x in bin(eval(s))[2:]])
            _t.append(_time)
            _time += Time(int(t))
        _p = _time

    return GCL(
        t=_t,
        e=_e,
        p=_p,
    )


class Environment:

    def __init__(self, t: Time) -> None:
        self.time_granularity = t
        self.LCM = None

        self.clock = Clock(Time(0, 0))
        self.counter = {}

        self.iter = 0

        ### {flow_id, [LEFT, RIGHT]}
        self.state = None

    def make(self, ) -> None:
        ## Create flows
        '''
            {
            "flow0": {
                 "id": 0,
                "pcp": 0,
                "length": 100,
                "period": 80000,
                "route": [
                    0,
                    1,
                    2
                ]
            }
        }
        '''

        with open(TRAFFIC_PATH) as f:
            traffic_conf = json.load(f)

        for flow_name, properties in traffic_conf.items():
            ## Generate route
            _route = []
            for i, dev in enumerate(properties['route'][:-1]):
                _route.append(Link(dev, properties['route'][i + 1]))
            _route = tuple(_route)

            _flow = Flow(id=properties["id"],
                         p=Time(properties["period"]),
                         o=Time(properties["offset"]),
                         l=properties['length'],
                         pcp=properties['pcp'],
                         route=_route)

            var._flows.append(_flow)
        self.LCM = Time(math.lcm(*[int(x.period) for x in var._flows]))

        with open(NETWORK_PATH) as f:
            network_conf = json.load(f)

        for switch_name, properties in network_conf.items():
            _dev_id = properties['id']
            _dev_type = properties['type']
            _dev_eg = []
            for i in range(1, 5):
                if "p%d" % i in properties:
                    _prop = properties["p%d" % i]

                    _eg = Egress(
                        id=i,
                        dev_id=_dev_id,
                        speed=_prop['speed'],
                        gcl=load_gcl(_prop['gcl']),
                        queue_nums=_prop['n_queues'],
                        neighbor=_prop['neighbor'],
                        clock=Clock(Time(0, 0)),
                        queues=[Queue() for _ in range(_prop['n_queues'])],
                        ## Only supports one-one mapping now
                        pcp_to_prio={k: k
                                     for k in range(_prop['n_queues'])},
                        prio_to_tc={k: k
                                    for k in range(_prop['n_queues'])})

                    _dev_eg.append(_eg)
            _sw = Device(_dev_id, _dev_type, _dev_eg)
            var._devices.append(_sw)

        ### Initialize -- Randomly assign each traffic to one spare window
        self.state = {}

        ### Clear GCL
        # for i in len(var._devices):
        #     for k in len(var._devices[i].egress_ports):
        #         var._devices[i].egress_ports[k].gcl = GCL(t=[],
        #                                                   e=[],
        #                                                   p=self.LCM)

        for flow in var._flows:
            self.state.setdefault(flow.id, [Time(0), Time(100)])
        self._map_state_to_gcl()

    def run(self) -> None:
        ## Add frame to network
        for flow in var._flows:
            if (self.clock.current_time + flow.offset) % flow.period == 0:
                # Add jitter from [-500ns, 500ns]
                # if (self.clock.current_time +
                #         Time(100) * randint(-5, 5)) % flow.period == 0:
                self.counter.setdefault(flow.id, 0)
                if self.counter[flow.id] >= self.LCM / flow.period:
                    self.counter[flow.id] = 0

                # ins = Frame(id=self.counter[flow.id],
                #             flow_id=flow.id,
                #             o=flow.period * self.counter[flow.id])

                ins = Frame(id=self.counter[flow.id],
                            flow_id=flow.id,
                            o=self.clock.current_time)

                self.counter[flow.id] += 1
                for i, v in enumerate(var._devices):
                    if v.id == flow.route[0][0]:
                        var._devices[i].recv(ins)

        ## Traverse every divice twice to make sure the order of running doesn't effect the result.
        for dev in var._devices:
            dev.run(Time(0))
        for dev in var._devices:
            dev.run(self.time_granularity)

        self.clock.increase(self.time_granularity)
        self.iter += 1

    def reward(self, ) -> float:
        reward = var._reward
        var._reward = 0
        return reward

    def action(self, frame_id: int, side: int, direc: Time) -> None:
        self.state[frame_id][side] += direc
        self._map_state_to_gcl()

    def _map_state_to_gcl(self, ) -> None:
        ### Check if there is overlap in GLC:
        ### https://www.geeksforgeeks.org/check-if-any-two-intervals-overlap-among-a-given-set-of-intervals/

        values = sorted(list(self.state.values()),
                        key=lambda x: x[0],
                        reverse=False)
        for i, v in enumerate(values[:-1]):
            if v[1] > values[i + 1][0]:
                print("[!] GCL Overlap: Wrong statues setting.")

        _t = []
        _e = []
        _p = self.LCM

        for flow_id, state in self.state.items():
            start, end = state[0], state[1]
            status = [
                True if i == var._flows[flow_id].pcp else None
                for i in range(8)
            ]
            _t.append(start)
            _e.append(status)
            _t.append(end)
            _e.append([
                False if i == var._flows[flow_id].pcp else None
                for i in range(8)
            ])

        ## Insertaion sort
        for i in range(len(_t)):
            current_t = _t[i]
            current_e = _e[i]
            k = i - 1
            while k >= 0 and _t[k] > current_t:
                _t[k + 1] = _t[k]
                _e[k + 1] = _e[k]
                k -= 1
            _t[k + 1] = current_t
            _e[k + 1] = current_e

        ## Complete the GCL
        for k, v in enumerate(_e[0]):
            if v == None:
                _e[0][k] = False
        for i in range(1, len(_t)):
            for k, v in enumerate(_e[i]):
                if v == None:
                    _e[i][k] = _e[i - 1][k]

        var._devices[0].egress_ports[0].gcl = GCL(t=_t, e=_e, p=_p)
