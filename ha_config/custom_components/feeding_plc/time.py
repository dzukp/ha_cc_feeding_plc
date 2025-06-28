import logging
from datetime import time, timedelta

from homeassistant.components.time import TimeEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN


logger = logging.getLogger('feeding')


class ModbusTime(CoordinatorEntity, TimeEntity):
    def __init__(self, coordinator, entry_id, client, name, address, ratio=1.0):
        super().__init__(coordinator)
        self._client = client
        self._attr_name = name
        self._address = address
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{address:03}"
        self._ratio = ratio
        logger.debug(f'time created addr: {self._address:03} uid: `{self._attr_unique_id}` name: `{self._attr_name}`')

    @property
    def native_value(self):
        value = self.coordinator.data.get(self._address)
        if value is None:
            return None
        value = int(value * self._ratio)
        hours = value // 3600
        minutes = (value - hours * 3600) // 60
        seconds = value % 60
        return time(hour=hours, minute=minutes, second=seconds)

    async def async_set_value(self, value: time) -> None:
        number_value = timedelta(hours=value.hour, minutes=value.minute, seconds=value.second).total_seconds()
        number_value /= self._ratio
        self._client.write_register(self._address, round(number_value))
        await self.coordinator.async_request_refresh()


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    coordinator = data["coordinator"]
    pool_plc_index = entry.data['pool_plc_index']
    pool_number = entry.data['pool_number']
    device_id = entry.entry_id
    address_offset = 215 + pool_plc_index * 20

    entities = create_items(coordinator, device_id, pool_number, client, address_offset)
    async_add_entities(entities)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up Modbus number and time entities from YAML config."""
    if discovery_info is None:
        return

    device_id = discovery_info["device_id"]
    pool_number = discovery_info["pool_number"]
    pool_plc_index = discovery_info["pool_plc_index"]
    data = hass.data[DOMAIN][device_id]
    coordinator = data["coordinator"]
    client = data["client"]
    address_offset = 215 + (pool_plc_index - 1) * 20

    entities = create_items(coordinator, device_id, pool_number, client, address_offset)
    async_add_entities(entities)


def create_items(
        coordinator: DataUpdateCoordinator, device_id: str, pool_number: int, client, address_offset: int
) -> list:
    return [
        ModbusTime(
            coordinator, device_id, client, f"Б{pool_number:02} Время начала 1",
            address_offset + 1, ratio=60.0
        ),
        ModbusTime(
            coordinator, device_id, client, f"Б{pool_number:02} Длительность 1",
            address_offset + 2
        ),
        ModbusTime(
            coordinator, device_id, client, f"Б{pool_number:02} Период 1",
            address_offset + 3, ratio=60.0
        ),
        ModbusTime(
            coordinator, device_id, client, f"Б{pool_number:02} Время начала 2",
            address_offset + 7, ratio=60.0
        ),
        ModbusTime(
            coordinator, device_id, client, f"Б{pool_number:02} Длительность 2",
            address_offset + 8,
        ),
        ModbusTime(
            coordinator, device_id, client, f"Б{pool_number:02} Период 2",
            address_offset + 9, ratio=60.0
        ),
    ]
