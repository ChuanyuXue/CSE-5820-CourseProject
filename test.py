## ---------------- Test for gcl search algorithm -------------

# from time import time

# time_list = [0.3, 0.5, 0.9, 1, 10, 100, 100.5, 3000]


# def _match_time(t):
#     left = 0
#     right = len(time_list) - 1
#     if t < time_list[left] or t > time_list[right]:
#         return right

#     while True:
#         median = (left + right) // 2
#         if right - left == 1:
#             return left
#         elif time_list[left] <= t < time_list[median]:
#             right = median
#         else:
#             left = median


# if __name__ == "__main__":
#     print(_match_time(0.2))
#     print(_match_time(0.4))
#     print(_match_time(0.6))
#     print(_match_time(0.5))
#     print(_match_time(0.9))
#     print(_match_time(8))
#     print(_match_time(1200))

