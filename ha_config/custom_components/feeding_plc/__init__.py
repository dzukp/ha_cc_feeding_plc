import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import CONF_HOST

from .modbus_client import PLCModbusClient
from .const import DOMAIN, PLC_FEEDING_NUMBER, HAS_NH4_SENSOR, SENSOR_ADDRESSES, STATE_MAP, ALARM_MASK, INPUT_ADDRESSES
from .sensor import ModbusSensor
from .number import ModbusNumber, ModbusStartTime


logger = logging.getLogger('feeding')


async def async_setup(hass: HomeAssistant, config: ConfigType):
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    host = entry.data[CONF_HOST]
    plc_feeding_number = entry.data[PLC_FEEDING_NUMBER]
    has_nh4 = entry.data[HAS_NH4_SENSOR]
    client = PLCModbusClient(host)

    async def async_update_data():
        start_address = 20 * plc_feeding_number
        result = client.read_all(start=start_address, count=30)
        if result is None:
            raise UpdateFailed("Modbus read failed")
        return result

    coordinator = DataUpdateCoordinator(
        hass,
        logger,
        name="modbus_plc",
        update_method=async_update_data,
        update_interval=timedelta(seconds=1),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator
    }

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "number", "binary_sensor"])

    return True
