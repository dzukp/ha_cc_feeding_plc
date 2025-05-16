from homeassistant.components.number import NumberEntity
from homeassistant.components.time import TimeEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.dt import parse_time
from datetime import time
from .const import DOMAIN, INPUT_ADDRESSES, PLC_FEEDING_NUMBER, HAS_NH4_SENSOR


class ModbusNumber(CoordinatorEntity, NumberEntity):
    def __init__(self, coordinator, entry_id, client, name, address, min_value=0, max_value=9999):
        super().__init__(coordinator)
        self._client = client
        self._attr_name = name
        self._address = address
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{address:03}"
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = 1

    @property
    def native_value(self):
        return self.coordinator.data.get(self._address)

    async def async_set_native_value(self, value: float) -> None:
        self._client.write_register(self._address, int(value))
        await self.coordinator.async_request_refresh()


class ModbusStartTime(CoordinatorEntity, TimeEntity):
    def __init__(self, coordinator, entry_id, client, name, address):
        super().__init__(coordinator)
        self._client = client
        self._attr_name = name
        self._address = address
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{address:03}"

    @property
    def native_value(self):
        value = self.coordinator.data.get(self._address)
        if value is None:
            return None
        hours = value // 60
        minutes = value % 60
        return time(hour=hours, minute=minutes)

    async def async_set_value(self, value: time) -> None:
        total_minutes = value.hour * 60 + value.minute
        self._client.write_register(self._address, total_minutes)
        await self.coordinator.async_request_refresh()


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    coordinator = data["coordinator"]
    plc_feeding_number = entry.data[PLC_FEEDING_NUMBER]
    has_nh4 = entry.data[HAS_NH4_SENSOR]
    address_offset = 215 + plc_feeding_number * 20

    numbers = [
        ModbusNumber(coordinator, entry.entry_id, client, "Duration 1", address_offset + INPUT_ADDRESSES["duration_1"], "s"),
        ModbusNumber(coordinator, entry.entry_id, client, "Period 1", address_offset + INPUT_ADDRESSES["period_1"], "s"),
        ModbusNumber(coordinator, entry.entry_id, client, "FeedingCount 1", address_offset + INPUT_ADDRESSES["feeding_count_1"])
    ]

    time_entities = [
        ModbusStartTime(coordinator, entry.entry_id, client, "Start Time 1", address_offset + INPUT_ADDRESSES["start_time_1"])
    ]

    async_add_entities(numbers)
    async_add_entities(time_entities)
