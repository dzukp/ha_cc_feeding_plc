import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from ..feeding_plc.number import ModbusNumber

logger = logging.getLogger('feeding')


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    coordinator = data["coordinator"]
    plc_number = entry.data['plc_number']
    device_id = entry.entry_id
    fry = entry.data["fry"]

    start_address = 240 if fry else 200
    entities = create_items(coordinator, device_id, client, plc_number, start_address)
    async_add_entities(entities)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    if discovery_info is None:
        return

    device_id = discovery_info["device_id"]
    plc_number = discovery_info['plc_number']
    fry = discovery_info["fry"]
    data = hass.data[DOMAIN][device_id]
    coordinator = data["coordinator"]
    client = data["client"]

    start_address = 240 if fry else 200
    entities = create_items(coordinator, device_id, client, plc_number, start_address)
    async_add_entities(entities)


def create_items(
        coordinator: DataUpdateCoordinator, device_id: str, client, plc_number: int, start_address: int
):
    return [
        ModbusNumber(
            coordinator, device_id, client, f"Ш{plc_number} Верх Лимит Температуры",
            start_address + 8, '°C', min_value=-100, max_value=100
        ),
        ModbusNumber(
            coordinator, device_id, client, f"Ш{plc_number} Низ Лимит Температуры",
            start_address + 9, '°C', min_value=-100, max_value=100
        ),
        ModbusNumber(
            coordinator, device_id, client, f"Ш{plc_number} Верх Лимит Кислорода",
            start_address + 10, 'мг/л', min_value=0, max_value=100
        ),
        ModbusNumber(
            coordinator, device_id, client, f"Ш{plc_number} Откл Кислорода",
            start_address + 11, 'мг/л', min_value=0, max_value=100
        ),
        ModbusNumber(
            coordinator, device_id, client, f"Ш{plc_number} Вкл Кислорода",
            start_address + 12, 'мг/л', min_value=0, max_value=100
        ),
        ModbusNumber(
            coordinator, device_id, client, f"Ш{plc_number} Низ Лимит Кислорода",
            start_address + 13, 'мг/л', min_value=0, max_value=100
        ),
    ]
