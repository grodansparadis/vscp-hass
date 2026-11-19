"""Shared VSCP entity helpers."""
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

class VSCPBase:
    _attr_has_entity_name = True
    def __init__(self, hub, mapping):
        self.hub = hub
        self.mapping = mapping
        self._attr_name = mapping['name']
        self._attr_unique_id = f"{hub.entry.entry_id}_{mapping['id']}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{hub.entry.entry_id}_{mapping['guid'].lower()}")},
            name=mapping.get('device_name', mapping['guid']),
            manufacturer='VSCP')

    def match(self, event, spec):
        return (event.guid == self.mapping['guid'].lower() and
                event.vscp_class == spec['class'] and
                event.vscp_type == spec['type'] and
                (not spec.get('data_prefix') or
                 list(event.data[:len(spec['data_prefix'])]) == spec['data_prefix']))

    async def async_added_to_hass(self):
        self.hub.listeners.append(self.on_event)

    async def async_will_remove_from_hass(self):
        if self.on_event in self.hub.listeners:
            self.hub.listeners.remove(self.on_event)
