DOMAIN = "feeding_plc"
PLC_FEEDING_NUMBER = "plc_feeding_number"
HAS_NH4_SENSOR = "has_nh4_sensor"


SENSOR_ADDRESSES = {
    "temperature": 15,
    "oxygen": 16,
    "valve1_state": 2,
    "valve2_state": 3,
    "state_code": 8,
    "alarm_code": 9,
}

INPUT_ADDRESSES = {
    "start_time_1": 3,
    "duration_1": 4,
    "period_1": 5,
    "feeding_count_1": 6,
    "start_time_2": 9,
    "duration_2": 10,
    "period_2": 11,
    "feeding_count_2": 12,
}

STATE_MAP = {
    0: "Ожидание начала",
    1: "Ожидание следующего",
    2: "Кормление",
    3: "Закончено",
}

ALARM_MASK = {
    0: "Sensor Error",
    1: "Valve Failure",
    2: "Overheat",
    3: "Low Oxygen",
}