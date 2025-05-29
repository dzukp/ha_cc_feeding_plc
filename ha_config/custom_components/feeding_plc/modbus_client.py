import logging

from pymodbus.client import ModbusTcpClient


logger = logging.getLogger('feeding')


class PLCModbusClient:
    def __init__(self, host, port=502):
        self.client = ModbusClientPool.get_client(host, port)
        self._host = host
        self._cache = {}

    def read_all(self, start, count):
        logger.info(f'start read_all {self._host} {start}:{count}')
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
        logger.info(f'end real_all {self._host} {self._cache}')
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
            cls._clients[key] = ModbusTcpClient(host, port=port)
        return cls._clients[key]
