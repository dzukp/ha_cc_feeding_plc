# binary_sensor.py

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

class ModbusBinarySensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, entry_id, client, name, address, bit, device_class=None):
        super().__init__(coordinator)
        self._client = client
        self._attr_name = name
        self._address = address
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{address:03}.{bit:02}"
        self._attr_device_class = device_class
        self.mask = 1 << bit

    @property
    def is_on(self):
        value = self.coordinator.data.get(self._address)
        if value is not None:
            return (value & self.mask) != 0


binary_sensors_config = [
    ("Automate", 0, 0, "plug"),
    ("Manual", 0, 1, "plug"),
    ("Feeding 1 run", 1, 0, "run"),
    ("Feeding 1 cmd", 1, 1, "run"),
    ("Feeding 2 run", 8, 0, "run"),
    ("Feeding 2 cmd", 8, 1, "run"),
]


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    coordinator = data["coordinator"]

    binary_sensors = []

    for name, address, bit, device_class in binary_sensors_config:
        binary_sensors.append(ModbusBinarySensor(coordinator, client, entry.entry_id, name, address, bit, device_class))

    async_add_entities(binary_sensors)
