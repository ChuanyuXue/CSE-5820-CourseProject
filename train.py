import src.var as var
from src.environment import Environment
from src.utils import Time
from src.model import Q_learning

env = Environment(Time(100))
env.make()

m = Q_learning(alpha=0.9,
               delta=0.9,
               epsilon=0.8,
               nflow=1,
               grua=Time(100),
               lcm=env.LCM,
               init_state=env.state)

count = 0
while count <= 10000:
    ### Step.1 Get the action from agent:
    acts = []
    for flow in var._flows:
        _act = m.action(env.state, flow.id)
        acts.append(_act)
        env.action(flow.id, 0, env.time_granularity * _act[0])
        env.action(flow.id, 1, env.time_granularity * _act[1])

    ### Update each 10000 iteration
    for i in range(10000):
        env.run()

    reward = env.reward()
    state = env.state

    for i, flow in enumerate(var._flows):
        m.update(new_state=state,
                 frame_id=flow.id,
                 side=0,
                 action=acts[i][0],
                 reward=reward)

        m.update(new_state=state,
                 frame_id=flow.id,
                 side=1,
                 action=acts[i][1],
                 reward=reward)
    # print("[Iter %6d] Current reward %f" % (count, reward))

    ## This line is for drawing output
    print(reward,
          len(var._devices[0].egress_ports[0].queues[0]),
          state[0][0],
          state[0][1],
          sep=',')
