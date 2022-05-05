## Hardcode the configuration file
from src import qbv_core
from src.qbv_core import *
import json

ENV_PATH = "configs/env.json"
NETWORK_PATH = "configs/network.json"
TRAFFIC_PATH = "configs/traffic.json"

f_0 = frame(id=0, flow_id=0, o=Time_point(0, 0))

# gcl_0 = GCL(
#     t=[Time_point(0, 500), Time_point(0, 1300)],
#     p=s_0.period,
#     e=[
#         [True],
#         [False],
#     ],
# )

def load_gcl(path: str) -> GCL:
    _t = []
    _e = []
    


class env:

    def __init__(self, ) -> None:
        pass

    def make(self, ) -> Tuple[List[Flow], List[Device]]:
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
            _route = Tuple(_route)

            _flow = Flow(id=properties["id"],
                         p=Time_duration(properties["period"]),
                         l=properties['length'],
                         pcp=properties['pcp'],
                         route=_route)

            qbv_core._flows.append(_flow)

        with open(NETWORK_PATH) as f:
            network_conf = json.load(f)

        for switch_name, properties in network_conf.items():
            dev_id = properties['id']
            dev_type = properties['type']
            for i in range(1, 5):
                if "p%d" % i in properties:
                    _prop = properties["p%d" % i]
                    _gcl = GCL(
                        t=[Time_point(0, 500), Time_point(0, 1300)],
                        p=s_0.period,
                        e=[
                            [True],
                            [False],
                        ],
                    )



                    _eg = Egress(
                        id=i,
                        speed=_prop['speed'],
                        queue_nums=_prop['n_queues'],
                        neighbor=_prop['neighbor'],
                        clock=Clock(Time_point(0, 0)),
                        queues=[Queue() for _ in range(_prop['n_queues'])],
                        ## Only supports one-one mapping now
                        pcp_to_prio={k: k
                                     for k in range(_prop['n_queues'])},
                        prio_to_tc={k: k
                                    for k in range(_prop['n_queues'])})
        

#### Create 1 egress queue with speed 1000 mbits = [10^9 bit / second = 1/8 byte / nanosecond]

### Create device switch1
switch_1 = Device(0, egress_ports=[sw1p0])
