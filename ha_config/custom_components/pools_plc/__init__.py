import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from ..feeding_plc.modbus_client import PLCModbusClient

logger = logging.getLogger('pools_plc')


async def async_setup(hass: HomeAssistant, config: ConfigType):
    hass.data.setdefault(DOMAIN, {})

    conf = config.get(DOMAIN)
    if not conf:
        return True

    for idx, device_conf in enumerate(conf):
        host = device_conf["host"]
        plc_number = device_conf["number"]
        extra_sensors = device_conf.get("extra_sensors", False)
        fry = device_conf.get("fry", False)

        client = PLCModbusClient(hass, host)
        client.setup_coordinator()

        await client.start()

        device_id = f"plc_{plc_number}"

        hass.data[DOMAIN][device_id] = {
            "client": client,
            "coordinator": client.coordinator,
        }

        for platform in ["sensor", "number", "binary_sensor"]:
            hass.async_create_task(
                async_load_platform(
                    hass, platform, DOMAIN,
                    {
                        "device_id": device_id,
                        "plc_number": plc_number,
                        "extra_sensors": extra_sensors,
                        "fry": fry
                    },
                    config,
                )
            )

    return True
