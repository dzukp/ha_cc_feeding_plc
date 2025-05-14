from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .modbus_client import PLCModbusClient
from .const import DOMAIN, SENSOR_ADDRESSES, STATE_MAP, ALARM_MASK, INPUT_ADDRESSES
from .sensor import ModbusSensor
from .number import ModbusNumber, ModbusStartTime


async def async_setup(hass: HomeAssistant, config: ConfigType):
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    host = entry.data["host"]
    unit = entry.data.get("unit", 1)
    client = PLCModbusClient(host, unit_id=unit)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"client": client}

    # Групповое чтение данных
    client.read_all()

    sensors = [
        ModbusSensor(client, "Temperature", SENSOR_ADDRESSES["temperature"], "°C"),
        ModbusSensor(client, "Oxygen", SENSOR_ADDRESSES["oxygen"], "%"),
        ModbusSensor(client, "Valve 1 State", SENSOR_ADDRESSES["valve1_state"]),
        ModbusSensor(client, "Valve 2 State", SENSOR_ADDRESSES["valve2_state"]),
        ModbusSensor(client, "State", SENSOR_ADDRESSES["state_code"], map_fn=lambda v: STATE_MAP.get(v, f"Unknown ({v})")),
        ModbusSensor(client, "Alarm", SENSOR_ADDRESSES["alarm_code"], map_fn=lambda v: ', '.join(name for bit, name in ALARM_MASK.items() if v & (1 << bit)))
    ]

    numbers = [
        ModbusNumber(client, "Duration", INPUT_ADDRESSES["duration"], "s"),
        ModbusNumber(client, "Period", INPUT_ADDRESSES["period"], "s"),
        ModbusNumber(client, "Count", INPUT_ADDRESSES["count"])
    ]

    time_entities = [
        ModbusStartTime(client, "Start Time", INPUT_ADDRESSES["start_time"])
    ]

    hass.helpers.discovery.load_platform("sensor", DOMAIN, {"entities": sensors}, hass.config)
    hass.helpers.discovery.load_platform("number", DOMAIN, {"entities": numbers}, hass.config)
    hass.helpers.discovery.load_platform("time", DOMAIN, {"entities": time_entities}, hass.config)

    return True
