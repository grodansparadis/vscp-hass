"""Mapped VSCP switches."""
from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN
from .entity import VSCPBase
from .protocol import Event

async def async_setup_entry(hass, entry, async_add_entities):
    d = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VSCPSwitch(d['hub'], m) for m in d['mappings'].get('switches', [])])

class VSCPSwitch(VSCPBase, SwitchEntity):
    def __init__(self, hub, mapping):
        super().__init__(hub, mapping)
        self._attr_is_on = None

    @property
    def available(self):
        return self.hub.connected

    def on_event(self, event):
        for value, spec in ((True, self.mapping['state_on']), (False, self.mapping['state_off'])):
            if self.match(event, spec):
                self._attr_is_on = value
                self.async_write_ha_state()
                return

    async def _send(self, spec):
        event = Event(spec.get('head', 0), spec['class'], spec['type'],
                      0, 0, spec.get('guid', self.mapping['guid']).lower(),
                      tuple(spec.get('data', [])))
        await self.hub.send(event)
        # State changes only when the node reports the corresponding event.

    async def async_turn_on(self, **kwargs):
        await self._send(self.mapping['command_on'])

    async def async_turn_off(self, **kwargs):
        await self._send(self.mapping['command_off'])
