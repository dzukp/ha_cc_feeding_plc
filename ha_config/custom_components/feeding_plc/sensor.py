from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN, SENSOR_ADDRESSES, STATE_MAP, ALARM_MASK

class ModbusSensor(SensorEntity):
    def __init__(self, client, name, address, unit=None, map_fn=None):
        self._client = client
        self._attr_name = name
        self._address = address
        self._attr_unique_id = f"{DOMAIN}_{address}"
        self._unit = unit
        self._map_fn = map_fn

    def update(self):
        value = self._client.get(self._address)
        if value is not None:
            self._attr_native_value = self._map_fn(value) if self._map_fn else value
            self._attr_native_unit_of_measurement = self._unit
