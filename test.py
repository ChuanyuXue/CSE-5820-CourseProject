from src.qbv_core import *
from src.environment import *
import src.qbv_core as qbv

# TIME_GURANULARITY = 100

## ---------------- Test for gcl search algorithm -------------

# from time import time

# time_list = [0, 0.3, 0.5, 0.9, 1, 10, 100, 100.5, 3000]
# time_list = [0, 0.4, 0.5]
# time_list = [0]

# def _match_time(t):
#     left = 0
#     right = len(time_list) - 1
#     if t >= time_list[right]:
#         return right

#     while True:
#         median = (left + right) // 2
#         if right - left <= 1:
#             return left
#         elif time_list[left] <= t < time_list[median]:
#             right = median
#         else:
#             left = median

# if __name__ == "__main__":
#     print(_match_time(0.2))
#     print(_match_time(0.3))
#     print(_match_time(0.4))
#     print(_match_time(0.6))
#     print(_match_time(0.5))
#     print(_match_time(0.9))
#     print(_match_time(8))
#     print(_match_time(1200))

## -------------- Test for one flow one switch -------------------
# f_0 = frame(id=0, flow_id=0, o=Time(0, 0))

# s_0 = Flow(id=0,
#            p=Time(1 / 12500 * 1e9),
#            l=100,
#            pcp=0,
#            frames=(f_0),
#            route=([Link(0, 1), Link(1, 2)]))

# ### Initialize GCL

# gcl_0 = GCL(
#     t=[Time(0, 500), Time(0, 1300)],
#     p=s_0.period,
#     e=[
#         [True],
#         [False],
#     ],
# )

# #### Create 1 egress queue with speed 1000 mbits = [10^9 bit / second = 1/8 byte / nanosecond]

# sw1p0 = Egress(
#     id=0,
#     speed=1 / 8,
#     gcl=gcl_0,
#     queue_nums=1,
#     neighbor=1,
#     clock=Clock(Time(0, 0)),
#     queues=[Queue()],
#     pcp_to_prio={0: 0},
#     prio_to_tc={0: 0},
# )

# ### Create device switch1
# switch_1 = Device(0, egress_ports=[sw1p0])

# ### Register
# qbv._flows = []
# qbv._devices = []
# qbv._flows.append(s_0)
# qbv._devices.append(switch_1)

# ### Test for one receive data
# switch_1.recv(f_0)
# for i in range(100):
#     switch_1.run(Time(TIME_GURANULARITY))
#     print(switch_1.egress_ports[0].clock.current_time)

## ------------ TEST FOR ENVIRONMENT and SINGLE FRAME ---------------
# env = Environment(Time(100))
# env.make()
# while True:
#     env.run()

## ------------ TEST FOR TWO FRAMEs ------------------------------
# env = Environment(Time(100))
# env.make()
# for i in range(10000):
#     env.run()

## ------------ TEST FOR THE [FOWARD] AND [ACTION] FUNCTION -------
# env = Environment(Time(100))
# env.make()
# print(env.state)
# while True:
#     for i in range(10000):
#         env.run()

#     env.action(0, 1, Time(100))
