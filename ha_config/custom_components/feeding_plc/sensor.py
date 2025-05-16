from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_ADDRESSES, STATE_MAP, ALARM_MASK, PLC_FEEDING_NUMBER, HAS_NH4_SENSOR


class ModbusSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry_id, name, address, unit=None, map_fn=None, ratio=None):
        super().__init__(coordinator)
        self.ratio = ratio
        self._attr_name = name
        self._address = address
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{address:03}"
        self._unit = unit
        self._map_fn = map_fn

    @property
    def native_value(self):
        value = self.coordinator.data.get(self._address)
        if self.ratio and value is not None:
            value *= self.ratio
        return self._map_fn(value) if self._map_fn and value is not None else value

    @property
    def native_unit_of_measurement(self):
        return self._unit


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    coordinator = data["coordinator"]
    plc_feeding_number = entry.data[PLC_FEEDING_NUMBER]
    has_nh4 = entry.data[HAS_NH4_SENSOR]
    address_offset = plc_feeding_number * 20
    sensors = [
        ModbusSensor(
            coordinator, entry.entry_id, f"Б{plc_feeding_number} Температура", address_offset + 15, "°C",
            ratio=0.01),
        ModbusSensor(
            coordinator, entry.entry_id, f"Б{plc_feeding_number} Кислород", address_offset + 16, "мг/л",
            ratio=0.01),
        ModbusSensor(coordinator, entry.entry_id, f"Б{plc_feeding_number} Кормушка 1", address_offset + 5,
                     map_fn=lambda v: STATE_MAP.get(v, f"? ({v})")),
        ModbusSensor(coordinator, entry.entry_id, f"Б{plc_feeding_number} До след кормления 1",
                     address_offset + 6),
        ModbusSensor(coordinator, entry.entry_id, f"Б{plc_feeding_number} Кормушка 2", address_offset + 12,
                     map_fn=lambda v: STATE_MAP.get(v, f"? ({v})")),
        ModbusSensor(coordinator, entry.entry_id, f"Б{plc_feeding_number} До след кормления 2",
                     address_offset + 13),
    ]

    async_add_entities(sensors)
