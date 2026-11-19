"""Mapped VSCP sensors; integer byte and IEEE754 float32 decoding."""
import struct
from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN
from .entity import VSCPBase

async def async_setup_entry(hass, entry, async_add_entities):
    d = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VSCPSensor(d['hub'], m) for m in d['mappings'].get('sensors', [])])

class VSCPSensor(VSCPBase, SensorEntity):
    def __init__(self, hub, mapping):
        super().__init__(hub, mapping)
        self._attr_native_value = None
        self._attr_native_unit_of_measurement = mapping.get('unit')

    @property
    def available(self):
        return self.hub.connected

    def on_event(self, event):
        if not self.match(event, self.mapping['event']):
            return
        spec = self.mapping
        offset = spec.get('offset', 0)
        try:
            if spec.get('encoding', 'uint8') == 'float32be':
                value = struct.unpack('>f', bytes(event.data[offset:offset+4]))[0]
            elif spec.get('encoding') == 'int16be':
                value = int.from_bytes(bytes(event.data[offset:offset+2]), 'big', signed=True)
            else:
                value = event.data[offset]
        except (IndexError, ValueError, struct.error):
            return
        self._attr_native_value = value * spec.get('scale', 1) + spec.get('add', 0)
        self.async_write_ha_state()
