import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import CONF_HOST

from .modbus_client import PLCModbusClient
from .const import DOMAIN, PLC_FEEDING_NUMBER, HAS_NH4_SENSOR, SENSOR_ADDRESSES, STATE_MAP, ALARM_MASK, INPUT_ADDRESSES
from .sensor import ModbusSensor
from .number import ModbusNumber, ModbusStartTime


logger = logging.getLogger('feeding')


async def async_setup(hass: HomeAssistant, config: ConfigType):
    hass.data.setdefault(DOMAIN, {})

    conf = config.get(DOMAIN)
    if not conf:
        return True

    for idx, device_conf in enumerate(conf):
        host = device_conf["host"]
        plc_feeding_number = device_conf["number"]
        has_nh4 = device_conf.get("has_nh4", False)

        client = PLCModbusClient(host)

        start_address = 20 * plc_feeding_number

        coordinator = DataUpdateCoordinator(
            hass,
            logger,
            name=f"modbus_plc_{plc_feeding_number}",
            update_method=make_update_data_func(client, start_address),
            update_interval=timedelta(seconds=1),
        )

        await coordinator.async_refresh()

        device_id = f"plc_{plc_feeding_number}"

        hass.data[DOMAIN][device_id] = {
            "client": client,
            "coordinator": coordinator,
        }

        # Передаём конфиг платформам (sensor, number, binary_sensor)
        for platform in ["sensor", "number", "binary_sensor"]:
            hass.async_create_task(
                async_load_platform(
                    hass, platform, DOMAIN,
                    {
                        "device_id": device_id,
                        "plc_feeding_number": plc_feeding_number,
                        "has_nh4": has_nh4,
                    },
                    config,
                )
            )

    return True



async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    host = entry.data[CONF_HOST]
    plc_feeding_number = entry.data[PLC_FEEDING_NUMBER]
    has_nh4 = entry.data[HAS_NH4_SENSOR]
    client = PLCModbusClient(host)

    start_address = 20 * plc_feeding_number

    coordinator = DataUpdateCoordinator(
        hass,
        logger,
        name=f"modbus_plc_{plc_feeding_number}",
        update_method=make_update_data_func(client, start_address),
        update_interval=timedelta(seconds=1),
        config_entry=entry,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator
    }

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "number", "binary_sensor"])

    return True


def make_update_data_func(client: PLCModbusClient, start_address: int):
    async def async_update_data():
        result = client.read_all(start=start_address, count=30)
        if result is None:
            raise UpdateFailed(f"Modbus read failed at address {start_address}")
        return result
    return async_update_data
