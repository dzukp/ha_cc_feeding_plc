from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from .const import DOMAIN

class ModbusSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, entry_id, client, name, address, bit):
        super().__init__(coordinator)
        self._client = client
        self._attr_name = name
        self._address = address
        self._bit = bit
        self._mask = 1 << bit
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_sw_{address:03}.{bit:02}"

    @property
    def is_on(self):
        value = self.coordinator.data.get(self._address)
        if value is not None:
            return (value & self._mask) != 0
        return False

    async def async_turn_on(self, **kwargs):
        value = self.coordinator.data.get(self._address)
        new_value = value | self._mask
        self._client.write_register(self._address, new_value)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        value = self.coordinator.data.get(self._address)
        new_value = value & (~self._mask)
        self._client.write_register(self._address, new_value)
        await self.coordinator.async_request_refresh()


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    if discovery_info is None:
        return

    device_id = discovery_info["device_id"]
    pool_plc_index = discovery_info["pool_plc_index"]
    pool_number = discovery_info["pool_number"]
    fry = discovery_info['fry']
    data = hass.data[DOMAIN][device_id]
    coordinator = data["coordinator"]
    start_address = 254 if fry else 214
    address_offset = start_address + (pool_plc_index - 1) * 20
    client = data["client"]
    switches = create_items(
        coordinator=coordinator, device_id=device_id, pool_number=pool_number, client=client,
        address_offset=address_offset
    )
    async_add_entities(switches)


def create_items(
        coordinator: DataUpdateCoordinator, device_id: str, pool_number: int, client, address_offset: int
) -> list[SwitchEntity]:
    switches_config = [
        (f"Б{pool_number:02} Игнор аварии температуры", address_offset + 0, 0),
        (f"Б{pool_number:02} Игнор аварии кислорода", address_offset + 0, 1),
        (f"Б{pool_number:02} Игнор аварии оксигенератора", address_offset + 0, 2),
        (f"Б{pool_number:02} Игнор аварии кормушки 1", address_offset + 0, 3),
        (f"Б{pool_number:02} Игнор аварии кормушки 2", address_offset + 0, 4),
    ]
    switches = []
    for name, address, bit in switches_config:
        switches.append(
            ModbusSwitch(coordinator, device_id, client, name, address, bit)
        )
    return switches