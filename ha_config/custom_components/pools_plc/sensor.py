import datetime
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from ..feeding_plc.sensor import ModbusSensor


logger = logging.getLogger('feeding')


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    coordinator = data["coordinator"]
    plc_number = entry.data['plc_number']
    device_id = entry.entry_id

    entities = create_items(coordinator, device_id, client, plc_number)
    async_add_entities(entities)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    if discovery_info is None:
        return

    device_id = discovery_info["device_id"]
    plc_number = discovery_info['plc_number']
    data = hass.data[DOMAIN][device_id]
    coordinator = data["coordinator"]
    client = data["client"]

    entities = create_items(coordinator, device_id, plc_number)
    async_add_entities(entities)


class PlcTimeModbusSensor(ModbusSensor):
    @property
    def native_value(self):
        hour = self.coordinator.data.get(self._address)
        minute = self.coordinator.data.get(self._address + 1)
        second = self.coordinator.data.get(self._address + 2)
        if None in (hour, minute, second):
            return None
        return datetime.time(hour=hour, minute=minute, second=second)


def create_items(
        coordinator: DataUpdateCoordinator, device_id: str, plc_number: int
):
    return [
        PlcTimeModbusSensor(coordinator, device_id, f"Ш{plc_number} Время",5),
        ModbusSensor(coordinator, device_id, f"Ш{plc_number} NH4", 9, unit='мг/л', ratio=0.1, signed=True),
        ModbusSensor(coordinator, device_id, f"Ш{plc_number} pH", 10, ratio=0.01, signed=True),
    ]
