from pymodbus.client import ModbusTcpClient


class PLCModbusClient:
    def __init__(self, host, port=502, unit_id=1):
        self.client = ModbusTcpClient(host, port=port)
        self.unit_id = unit_id
        self._cache = {}

    def read_all(self, start=0, count=10):
        rr = self.client.read_holding_registers(start, count, unit=self.unit_id)
        if rr.isError():
            return None
        self._cache = {start + i: v for i, v in enumerate(rr.registers)}
        return self._cache

    def get(self, address):
        return self._cache.get(address)

    def write_register(self, address, value):
        return self.client.write_register(address, value, unit=self.unit_id)