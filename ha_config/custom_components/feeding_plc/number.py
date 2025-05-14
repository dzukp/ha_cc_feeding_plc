from homeassistant.components.number import NumberEntity
from homeassistant.components.time import TimeEntity
# from homeassistant.util.dt import parse_time, time_to_seconds
from datetime import time
from .const import DOMAIN, INPUT_ADDRESSES


class ModbusNumber(NumberEntity):
    def __init__(self, client, name, address, unit=None, min_value=0, max_value=9999):
        self._client = client
        self._attr_name = name
        self._address = address
        self._attr_unique_id = f"{DOMAIN}_number_{address}"
        self._unit = unit
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = 1

    def update(self):
        value = self._client.get(self._address)
        if value is not None:
            self._attr_native_value = value

    async def async_set_native_value(self, value: float) -> None:
        self._client.write_register(self._address, int(value))
        self._attr_native_value = value


class ModbusStartTime(TimeEntity):
    def __init__(self, client, name, address):
        self._client = client
        self._attr_name = name
        self._address = address
        self._attr_unique_id = f"{DOMAIN}_time_{address}"
        self._time: time | None = None

    def update(self):
        value = self._client.get(self._address)
        if value is not None:
            hours = value // 60
            minutes = value % 60
            self._time = time(hour=hours, minute=minutes)

    @property
    def native_value(self):
        return self._time

    async def async_set_value(self, value: time) -> None:
        total_minutes = value.hour * 60 + value.minute
        self._client.write_register(self._address, total_minutes)
        self._time = value
