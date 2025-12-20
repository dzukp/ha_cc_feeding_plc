import logging
from datetime import time

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.components.time import TimeEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN


logger = logging.getLogger('feeding')


class ModbusNumber(CoordinatorEntity, NumberEntity):
    def __init__(self, coordinator, entry_id, client, name, address, unit=None, min_value=0, max_value=9999, ratio=None):
        super().__init__(coordinator)
        self._client = client
        self._attr_name = name
        self._address = address
        self._unit = unit
        self._ratio = ratio
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{address:03}"
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = 1
        self._attr_mode = NumberMode.BOX
        logger.debug(f'number created addr: {self._address:03} uid: `{self._attr_unique_id}` name: `{self._attr_name}`')

    @property
    def native_value(self):
        val = self.coordinator.data.get(self._address)
        if self._ratio:
            return val * self._ratio
        return val

    async def async_set_native_value(self, value: float) -> None:
        if self._ratio:
            value = value / self._ratio
        self._client.write_register(self._address, int(value))
        await self.coordinator.async_request_refresh()


class ModbusStartTime(CoordinatorEntity, TimeEntity):
    def __init__(self, coordinator, entry_id, client, name, address):
        super().__init__(coordinator)
        self._client = client
        self._attr_name = name
        self._address = address
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{address:03}"
        logger.debug(f'time created addr: {self._address:03} uid: `{self._attr_unique_id}` name: `{self._attr_name}`')

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
    pool_plc_index = entry.data['pool_plc_index']
    pool_number = entry.data['pool_number']
    fry = entry.data['fry']
    device_id = entry.entry_id
    start_address = 255 if fry else 215
    address_offset = start_address + (pool_plc_index - 1) * 20

    entities = create_items(coordinator, device_id, pool_number, client, address_offset)
    async_add_entities(entities)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up Modbus number and time entities from YAML config."""
    if discovery_info is None:
        return

    device_id = discovery_info["device_id"]
    pool_number = discovery_info["pool_number"]
    pool_plc_index = discovery_info["pool_plc_index"]
    fry = discovery_info['fry']
    data = hass.data[DOMAIN][device_id]
    coordinator = data["coordinator"]
    client = data["client"]
    start_address = 255 if fry else 215
    address_offset = start_address + (pool_plc_index - 1) * 20

    entities = create_items(coordinator, device_id, pool_number, client, address_offset)
    async_add_entities(entities)


def create_items(
        coordinator: DataUpdateCoordinator, device_id: str, pool_number: int, client, address_offset: int
):
    return [
        ModbusNumber(
            coordinator, device_id, client, f"Б{pool_number:02} Уст Время начала 1",
            address_offset + 1, 'мин', min_value=0, max_value=60 * 24
        ),
        ModbusNumber(
            coordinator, device_id, client, f"Б{pool_number:02} Уст Длительность 1",
            address_offset + 2, "сек", min_value=0, max_value=32000
        ),
        ModbusNumber(
            coordinator, device_id, client, f"Б{pool_number:02} Уст Период 1",
            address_offset + 3, "сек", min_value=0, max_value=32000
        ),
        ModbusNumber(
            coordinator, device_id, client, f"Б{pool_number:02} Уст Кол-во кормлений 1",
            address_offset + 4, min_value=0, max_value=32000
        ),
        ModbusNumber(
            coordinator, device_id, client, f"Б{pool_number:02} Уст Время начала 2",
            address_offset + 7, 'мин', min_value=0, max_value=60 * 24
        ),
        ModbusNumber(
            coordinator, device_id, client, f"Б{pool_number:02} Уст Длительность 2",
            address_offset + 8, "сек", min_value=0, max_value=32000
        ),
        ModbusNumber(
            coordinator, device_id, client, f"Б{pool_number:02} Уст Период 2",
            address_offset + 9, "сек", min_value=0, max_value=32000
        ),
        ModbusNumber(
            coordinator, device_id, client, f"Б{pool_number:02} Уст Кол-во кормлений 2",
            address_offset + 10, min_value=0, max_value=32000
        ),
    ]
