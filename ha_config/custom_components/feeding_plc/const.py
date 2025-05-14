DOMAIN = "feeding_plc"
SENSOR_ADDRESSES = {
    "temperature": 0,
    "oxygen": 1,
    "valve1_state": 2,
    "valve2_state": 3,
    "state_code": 8,
    "alarm_code": 9,
}

INPUT_ADDRESSES = {
    "start_time": 4,
    "duration": 5,
    "period": 6,
    "count": 7,
}

STATE_MAP = {
    0: "Idle",
    1: "Start",
    2: "In Progress",
    3: "Finished",
    4: "Error"
}

ALARM_MASK = {
    0: "Sensor Error",
    1: "Valve Failure",
    2: "Overheat",
    3: "Low Oxygen",
    # и т.д.
}