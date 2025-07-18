import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from ..feeding_plc.binary_sensor import ModbusBinarySensor


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

    entities = create_items(coordinator, device_id, client, plc_number)
    async_add_entities(entities)


def create_items(
        coordinator: DataUpdateCoordinator, device_id: str, client, plc_number: int
):
    return [
        ModbusBinarySensor(coordinator, device_id, client, f"Ш{plc_number} Питание",9, 0),
    ]
