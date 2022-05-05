import math
from src import qbv_core
from src.qbv_core import *
import json

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
            _e.append([True if x == 1 else False for x in bin(eval(s))[2:]])
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
                         l=properties['length'],
                         pcp=properties['pcp'],
                         route=_route)

            qbv_core._flows.append(_flow)
        self.LCM = Time(math.lcm(*[int(x.period) for x in qbv_core._flows]))

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
            qbv_core._devices.append(_sw)

    def run(self):
        counter = {}

        for flow in qbv_core._flows:
            if self.clock.current_time / flow.period == 0:
                counter.setdefault(flow.id, 0)
                if counter[flow.id] >= self.LCM / flow.period:
                    counter[flow.id] = 0

                ins = Frame(id=counter[flow.id],
                            flow_id=flow.id,
                            o=flow.period * counter[flow.id])
                counter[flow.id] += 1
                for i, v in enumerate(qbv_core._devices):
                    if v.id == flow.route[0][0]:
                        qbv_core[i].recv(ins)

        for dev in qbv_core._devices:
            dev.run(self.time_granularity)

        self.clock.increase(self.time_granularity)