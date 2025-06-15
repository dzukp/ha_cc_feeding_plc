import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN


logger = logging.getLogger('feeding')


class ModbusBinarySensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, entry_id, client, name, address, bit, device_class=None):
        super().__init__(coordinator)
        self._client = client
        self._attr_name = name
        self._address = address
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{address:03}.{bit:02}"
        self._attr_device_class = device_class
        self.mask = 1 << bit
        logger.debug(
            f'bin sensor created addr: {self._address:03} uid: `{self._attr_unique_id}` name: `{self._attr_name}`'
        )

    @property
    def is_on(self):
        value = self.coordinator.data.get(self._address)
        return (value & self.mask) != 0 if value is not None else None


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    coordinator = data["coordinator"]
    pool_plc_index = entry.data['pool_plc_index']
    pool_number = entry.data['pool_number']
    device_id = entry.entry_id
    address_offset = (pool_plc_index - 1) * 20 + 20

    entities = create_items(coordinator, client, device_id, pool_number, address_offset)
    async_add_entities(entities)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up Modbus binary sensors from YAML config."""
    if discovery_info is None:
        return

    device_id = discovery_info["device_id"]
    data = hass.data[DOMAIN][device_id]
    coordinator = data["coordinator"]
    pool_plc_index = discovery_info["pool_plc_index"]
    pool_number = discovery_info["pool_number"]
    client = data["client"]
    address_offset = (pool_plc_index - 1) * 20 + 20

    entities = create_items(coordinator, client, device_id, pool_number, address_offset)
    async_add_entities(entities)


def create_items(
        coordinator: DataUpdateCoordinator, client, device_id: str, plc_feeding_number: int, address_offset: int
) -> list[BinarySensorEntity]:
    binary_sensors_config = [
        (f"Б{plc_feeding_number:02} Автомат", address_offset + 0, 0, "plug"),
        (f"Б{plc_feeding_number:02} Ручной", address_offset + 0, 1, "plug"),
        (f"Б{plc_feeding_number:02} Корм 1 работа", address_offset + 1, 0, "running"),
        (f"Б{plc_feeding_number:02} Корм 1 пуск", address_offset + 1, 1, "plug"),
        (f"Б{plc_feeding_number:02} Корм 2 работа", address_offset + 8, 0, "running"),
        (f"Б{plc_feeding_number:02} Корм 2 пуск", address_offset + 8, 1, "plug"),
    ]
    sensors = []
    for name, address, bit, device_class in binary_sensors_config:
        sensors.append(ModbusBinarySensor(coordinator, device_id, client, name, address, bit, device_class))
    return sensors
