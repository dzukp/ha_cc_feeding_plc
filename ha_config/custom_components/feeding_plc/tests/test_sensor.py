# tests/test_sensor.py
import pytest
from ..sensor import ModbusSensor


@pytest.fixture
def mock_coordinator():
    class MockCoordinator:
        data = {25: 42, 26: 3}
    return MockCoordinator()


def test_sensor_native_value_plain(mock_coordinator):
    sensor = ModbusSensor(mock_coordinator, '123', "Test Temp", 25)
    assert sensor.native_value == 42


def test_sensor_native_value_mapped(mock_coordinator):
    def map_fn(value):
        return "Alarm" if value == 3 else "OK"
    sensor = ModbusSensor(mock_coordinator, '654', "Test Alarm", 26, map_fn=map_fn)
    assert sensor.native_value == "Alarm"


def test_sensor_native_value_none(mock_coordinator):
    sensor = ModbusSensor(mock_coordinator, '123rtrt', "Missing", 99)
    assert sensor.native_value is None
