from typing import Tuple
from random import random, randint

from src.utils import Time


def argmax(x):
    _max_v = -1e9
    _max_i = -1
    for i, v in enumerate(x):
        if v > _max_v:
            _max_i = i
    return _max_i


class Q_learning:

    def __init__(self, alpha, delta, epsilon, nflow, grua, lcm,
                 init_state) -> None:
        self.Q = {}
        self.alpha = alpha
        self.delta = delta
        self.epi = epsilon
        self.grua = grua
        self.lcm = lcm

        dim = int(lcm / grua)

        for frame_id in range(nflow):
            self.Q[frame_id] = [None] * 2
            self.Q[frame_id][0] = [[0, 0, 0] for y in range(dim)]
            self.Q[frame_id][1] = [[0, 0, 0] for y in range(dim)]

        self._old_state = init_state

    def action(self, state, frame_id) -> Tuple[int, int]:
        result = []
        for side in [0, 1]:
            _pos = int(state[frame_id][side] / self.grua)
            if random() > self.epi:
                result.append(argmax(self.Q[frame_id][0][_pos]))
            else:
                result.append(randint(0, 2))

        ### Avoid out of range:
        ### Constraint on left left
        if result[0] == 0 and state[frame_id][0] - self.grua < Time(0):
            result[0] = 1
        ### Constraint on left right
        if result[0] == 2 and state[frame_id][0] + self.grua >= state[
                frame_id][1]:
            result[0] = 1
        ### Constraint on right left
        if result[1] == 0 and state[frame_id][1] - self.grua <= state[
                frame_id][1]:
            result[1] = 1
        ### Constraint on right right
        if result[1] == 2 and state[frame_id][1] + self.grua >= self.lcm:
            result[1] = 1

        return [x - 1 for x in result]

    def update(self, new_state, frame_id, side, action, reward):
        action = action + 1

        if side == 0:
            _pos = int(new_state[frame_id][0] / self.grua)
            _oldpos = int(self._old_state[frame_id][0] / self.grua)
        elif side == 1:
            _pos = int(new_state[frame_id][1] / self.grua)
            _oldpos = int(self._old_state[frame_id][1] / self.grua)

        ### Update the Q table
        td_target = reward + self.delta * max(self.Q[frame_id][side][_pos])
        td_delta = td_target - self.Q[frame_id][side][_oldpos][action]
        self.Q[frame_id][side][_oldpos][action] += self.alpha * td_delta
