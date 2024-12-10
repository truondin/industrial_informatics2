from enum import Enum


class State(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2


class Sensor:
    def __init__(self, sensor_id, low_threshold, high_threshold):
        self.sensor_id = sensor_id
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold


class Measurement:
    def __init__(self, sensor_id, value, time, state):
        self.sensor_id = sensor_id
        self.value = value
        self.time = time
        self.state = state