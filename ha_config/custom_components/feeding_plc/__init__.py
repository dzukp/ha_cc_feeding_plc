import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import CONF_HOST

from .const import DOMAIN, SENSOR_ADDRESSES, STATE_MAP, ALARM_MASK, INPUT_ADDRESSES
from .http_api import RecipeCsvUploadView
from .modbus_client import PLCModbusClient

logger = logging.getLogger('feeding')


async def async_setup(hass: HomeAssistant, config: ConfigType):
    hass.data.setdefault(DOMAIN, {})

    conf = config.get(DOMAIN)
    if not conf:
        return True

    for idx, device_conf in enumerate(conf):
        host = device_conf["host"]
        pool_number = device_conf["number"]
        pool_plc_index = device_conf["pool_plc_index"]

        client = PLCModbusClient(hass, host)
        client.setup_coordinator()

        await client.start()

        device_id = f"plc_{pool_number}"

        hass.data[DOMAIN][device_id] = {
            "client": client,
            "coordinator": client.coordinator,
        }

        for platform in ["sensor", "number", "binary_sensor", "time"]:
            hass.async_create_task(
                async_load_platform(
                    hass, platform, DOMAIN,
                    {
                        "device_id": device_id,
                        "pool_number": pool_number,
                        "pool_plc_index": pool_plc_index
                    },
                    config,
                )
            )

    hass.http.register_view(RecipeCsvUploadView)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    host = entry.data[CONF_HOST]
    client = PLCModbusClient(hass, host)
    client.setup_coordinator()

    await client.start()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": client.coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(
        entry,
        ["sensor", "number", "binary_sensor", "time"]
    )

    return True
