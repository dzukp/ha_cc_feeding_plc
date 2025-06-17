import logging
import random
from datetime import timedelta
from asyncio import sleep

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ConnectionException

logger = logging.getLogger('feeding')


class PLCModbusClient:
    def __init__(self, hass, host, port=502):
        self.client = ModbusClientPool.get_client(host, port)
        self._host = host
        self._port = port
        self._cache = {}
        self._hass = hass
        self._coordinator = None
        self._started = False

    def setup_coordinator(self):
        async def _update():
            all_data = {}
            try:
                for start, count in ((1, 100), (101, 100), (201, 98)):
                    data = self.read_all(start, count)
                    if data:
                        all_data.update(data)
            except ConnectionException:
                logger.error(f'ConnectionException {self._host}')
                self._cache = {i: None for i in range(1, 299)}
                return {}
            return all_data

        self._coordinator = CoordinatorPool.get_coordinator(
            host=self._host, port=self._port, hass=self._hass, name=f"modbus_plc_{self._host}", update_method=_update
        )

    async def start(self, delay: float | None = None):
        if self._started:
            return
        if delay is None:
            delay = random.uniform(0., 1.)
        await sleep(delay)
        if self._coordinator:
            await self._coordinator.async_refresh()
        self._started = True

    @property
    def coordinator(self):
        return self._coordinator

    def read_all(self, start, count):
        logger.debug(f'start read_all {id(self)} {self._host} {start}:{count}')
        try:
            self._read_all(start, count)
        except BrokenPipeError:
            logger.warning(f'Modbus reconnection {self._host}')
            self.client.close()
            self.client.connect()
            try:
                self._read_all(start, count)
            except BrokenPipeError as e:
                logger.exception(f"Modbus read failed after reconnect {self._host}")
                return None
        logger.debug(f'end real_all {self._host} {self._cache}')
        return self._cache

    def _read_all(self, start, count):
        rr = self.client.read_holding_registers(address=start, count=count)
        if rr.isError():
            logger.error('error')
            return
        self._cache = {start + i: v for i, v in enumerate(rr.registers)}

    def get(self, address):
        return self._cache.get(address)

    def write_registers(self, address: int, values: list):
        return self.client.write_registers(address, values)

    def write_register(self, address: int, value: int):
        return self.client.write_registers(address, [value])


class ModbusClientPool:
    _clients = {}

    @classmethod
    def get_client(cls, host, port):
        key = (host, port)
        if key not in cls._clients:
            cls._clients[key] = ModbusTcpClient(host, port=port, timeout=0.2)
        return cls._clients[key]


class CoordinatorPool:
    _coordinators = {}

    @classmethod
    def get_coordinator(cls, host, port, hass, name, update_method):
        key = (host, port)
        if key not in cls._coordinators:
            cls._coordinators[key] = DataUpdateCoordinator(
                hass,
                logger,
                name=name,
                update_method=update_method,
                update_interval=timedelta(seconds=3),
            )
        return cls._coordinators[key]
