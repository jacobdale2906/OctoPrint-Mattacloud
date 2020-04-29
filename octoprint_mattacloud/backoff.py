import time
import random


class BackoffTime:
    def __init__(self, max_time):
        self.attempt = 0
        self.max_time = max_time

    def longer(self):
        self.attempt += 1
        sleep_time = (2 ** self.attempt) + (random.randint(0, 1000) / 1000)
        if sleep_time > self.max_time:
            sleep_time = self.max_time
        time.sleep(sleep_time)

    def zero(self):
        self.attempt = 0
