import logging
from datetime import time

from homeassistant.components.number import NumberEntity
from homeassistant.components.time import TimeEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN, INPUT_ADDRESSES, PLC_FEEDING_NUMBER, HAS_NH4_SENSOR


logger = logging.getLogger('feeding')


class ModbusNumber(CoordinatorEntity, NumberEntity):
    def __init__(self, coordinator, entry_id, client, name, address, unit=None, min_value=0, max_value=9999):
        super().__init__(coordinator)
        self._client = client
        self._attr_name = name
        self._address = address
        self._unit = unit
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{address:03}"
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = 1
        logger.debug(f'number created addr: {self._address:03} uid: `{self._attr_unique_id}` name: `{self._attr_name}`')

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
    plc_feeding_number = entry.data[PLC_FEEDING_NUMBER]
    has_nh4 = entry.data[HAS_NH4_SENSOR]
    device_id = entry.entry_id
    address_offset = 215 + plc_feeding_number * 20

    entities = create_items(coordinator, device_id, plc_feeding_number, client, address_offset)
    async_add_entities(entities)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up Modbus number and time entities from YAML config."""
    if discovery_info is None:
        return

    device_id = discovery_info["device_id"]
    plc_feeding_number = discovery_info["plc_feeding_number"]
    has_nh4 = discovery_info["has_nh4"]
    data = hass.data[DOMAIN][device_id]
    coordinator = data["coordinator"]
    client = data["client"]
    address_offset = 215 + (plc_feeding_number - 1) * 20

    entities = create_items(coordinator, device_id, plc_feeding_number, client, address_offset)
    async_add_entities(entities)


def create_items(
        coordinator: DataUpdateCoordinator, device_id: str, plc_feeding_number: int, client, address_offset: int
):
    return [
        ModbusStartTime(
            coordinator, device_id, client, f"Б{plc_feeding_number:02} Уст Время начала 1",
            address_offset + 2
        ),
        ModbusNumber(
            coordinator, device_id, client, f"Б{plc_feeding_number:02} Уст Длительность 1",
            address_offset + 3, "сек"
        ),
        ModbusNumber(
            coordinator, device_id, client, f"Б{plc_feeding_number:02} Уст Период 1",
            address_offset + 4, "сек"
        ),
        ModbusNumber(
            coordinator, device_id, client, f"Б{plc_feeding_number:02} Уст Кол-во кормлений 1",
            address_offset + 5
        ),
    ]
