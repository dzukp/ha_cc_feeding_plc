import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from .const import DOMAIN, PLC_FEEDING_NUMBER, HAS_NH4_SENSOR

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME, default="Feeding PLC"): str,
    vol.Required(CONF_HOST): str,
    vol.Required(PLC_FEEDING_NUMBER): int,
    vol.Required(HAS_NH4_SENSOR, default=False): bool,
})

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)