"""UI setup for VSCP daemon."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_USERNAME, CONF_PASSWORD
from .const import DOMAIN, DEFAULT_PORT
from .protocol import Link, VSCPError

class VSCPConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            link = Link(user_input[CONF_HOST], user_input[CONF_PORT],
                        user_input[CONF_USERNAME], user_input[CONF_PASSWORD])
            try:
                await link.connect()
            except (OSError, TimeoutError, VSCPError):
                errors['base'] = 'cannot_connect'
            else:
                await self.async_set_unique_id(f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=f"VSCP {user_input[CONF_HOST]}", data=user_input)
            finally:
                await link.close()
        schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
        })
        return self.async_show_form(step_id='user', data_schema=schema, errors=errors)
