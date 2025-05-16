import logging

from pymodbus.client import ModbusTcpClient


logger = logging.getLogger('feeding')


class PLCModbusClient:
    def __init__(self, host, port=502):
        self.client = ModbusClientPool.get_client(host, port)
        self._cache = {}

    def read_all(self, start, count):
        logger.info('start real_all')
        rr = self.client.read_holding_registers(address=start, count=count)
        if rr.isError():
            logger.error('error')
            return None
        self._cache = {start + i: v for i, v in enumerate(rr.registers)}
        logger.info(f'end real_all {self._cache}')
        return self._cache

    def get(self, address):
        return self._cache.get(address)

    def write_registers(self, address: int, values: list):
        return self.client.write_registers(address, values)


class ModbusClientPool:
    _clients = {}

    @classmethod
    def get_client(cls, host, port):
        key = (host, port)
        if key not in cls._clients:
            cls._clients[key] = ModbusTcpClient(host, port=port)
        return cls._clients[key]
