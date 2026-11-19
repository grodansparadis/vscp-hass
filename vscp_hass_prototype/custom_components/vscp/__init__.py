"""VSCP TCP/IP integration."""
import json
from pathlib import Path
from homeassistant.exceptions import ConfigEntryNotReady
from .const import DOMAIN, PLATFORMS
from .hub import Hub
from .protocol import VSCPError

async def async_setup_entry(hass, entry):
    hub = Hub(hass, entry)
    try:
        await hub.start()
    except (OSError, TimeoutError, VSCPError) as err:
        raise ConfigEntryNotReady from err
    # Entity mappings are deliberately explicit; no speculative automatic control.
    mapping_path = Path(hass.config.path('vscp_entities.json'))
    try:
        mappings = await hass.async_add_executor_job(lambda: json.loads(mapping_path.read_text())) if mapping_path.exists() else {}
    except (OSError, ValueError) as err:
        await hub.stop()
        raise ConfigEntryNotReady(f'Invalid VSCP mapping file: {err}') from err
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {'hub': hub, 'mappings': mappings}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass, entry):
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        await data['hub'].stop()
    return ok
