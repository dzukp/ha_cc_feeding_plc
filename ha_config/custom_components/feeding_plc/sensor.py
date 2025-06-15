import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN


logger = logging.getLogger('feeding')


class ModbusSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry_id, name, address, unit=None, map_fn=None, ratio=None):
        super().__init__(coordinator)
        self._ratio = ratio
        self._attr_name = name
        self._address = address
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{address:03}"
        self._unit = unit
        self._map_fn = map_fn
        logger.debug(f'sensor created addr: {self._address:03} uid: `{self._attr_unique_id}` name: `{self._attr_name}`')

    @property
    def native_value(self):
        value = self.coordinator.data.get(self._address)
        if self._ratio and value is not None:
            value *= self._ratio
        return self._map_fn(value) if self._map_fn and value is not None else value

    @property
    def native_unit_of_measurement(self):
        return self._unit


class ModbusBitMaskListSensor(ModbusSensor):
    def __init__(self, coordinator, entry_id, name, address, error_map: dict[int, str]):
        super().__init__(coordinator, entry_id, name, address)
        self._digit_value = None
        self._error_map = error_map

    @property
    def native_value(self):
        raw = self.coordinator.data.get(self._address)
        self._digit_value = raw
        if raw is None:
            return "Нет данных"
        errors = [desc for bit, desc in self._error_map.items() if raw & (1 << bit)]
        return ", ".join(errors) if errors else "Ошибок нет"


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    pool_plc_index = entry.data['pool_plc_index']
    pool_number = entry.data['pool_number']
    device_id = entry.entry_id
    address_offset = pool_plc_index * 20
    sensors = create_items(coordinator, device_id, pool_number, address_offset)
    async_add_entities(sensors)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up Modbus sensors from YAML config."""
    if discovery_info is None:
        return

    device_id = discovery_info["device_id"]
    pool_plc_index = discovery_info["pool_plc_index"]
    pool_number = discovery_info["pool_number"]
    data = hass.data[DOMAIN][device_id]
    coordinator = data["coordinator"]
    address_offset = pool_plc_index * 20
    sensors = create_items(coordinator, device_id, pool_number, address_offset)
    async_add_entities(sensors)


def create_items(
        coordinator: DataUpdateCoordinator, device_id: str, plc_feeding_number: int, address_offset: int
) -> list[SensorEntity]:
    feeding_state_map = {
        0: "Ожидание начала",
        1: "Ожидание следующего",
        2: "Кормление",
        3: "Закончено",
    }

    error_bitmask = {
        0: 'Высокая температура',
        1: 'Низкая температура',
        2: 'Высокий кислород',
        3: 'Низкий кислород',
        4: 'Отключен оксигенератор',
        5: 'Не вкл кормушка 1',
        6: 'Не вкл кормушка 2',
        7: 'Ошибка датчика кислорода',
    }

    sensors = [
        ModbusSensor(
            coordinator, device_id, f"Б{plc_feeding_number:02} Температура", address_offset + 15, "°C",
            ratio=0.01
        ),
        ModbusSensor(
            coordinator, device_id, f"Б{plc_feeding_number:02} Кислород", address_offset + 16, "мг/л",
            ratio=0.01
        ),
        ModbusSensor(
            coordinator, device_id, f"Б{plc_feeding_number:02} Кормление 1", address_offset + 5,
            map_fn=lambda v: feeding_state_map.get(v, f"? ({v})")
        ),
        ModbusSensor(
            coordinator, device_id, f"Б{plc_feeding_number:02} След корм 1", address_offset + 6, "сек"
        ),
        ModbusSensor(coordinator, device_id, f"Б{plc_feeding_number:02} Прошло корм 1", address_offset + 7),
        ModbusSensor(
            coordinator, device_id, f"Б{plc_feeding_number:02} Кормление 2", address_offset + 12,
            map_fn=lambda v: feeding_state_map.get(v, f"? ({v})")
        ),
        ModbusSensor(
            coordinator, device_id, f"Б{plc_feeding_number:02} След корм 2", address_offset + 13, "сек"
        ),
        ModbusSensor(coordinator, device_id, f"Б{plc_feeding_number:02} Прошло корм 2", address_offset + 14),
        ModbusBitMaskListSensor(
            coordinator, device_id, f"Б{plc_feeding_number:02} Авария", address_offset + 17, error_bitmask
        )
    ]
    return sensors
