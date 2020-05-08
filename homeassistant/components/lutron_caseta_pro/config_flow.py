"""Config flow for lutron_caseta_pro integration."""
import logging

import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_HOST, CONF_MAC
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN  # pylint:disable=unused-import

_LOGGER = logging.getLogger(__name__)

CONF_INTEGRATION_REPORT = "integration_report"

DATA_SCHEMA = vol.Schema({CONF_HOST: str, CONF_MAC: str})


class PlaceholderHub:
    """Placeholder class to make tests pass.

    TODO Remove this placeholder class and replace with things from your PyPI package.
    """

    def __init__(self, host):
        """Initialize."""
        self.host = host

    async def authenticate(self, username, password) -> bool:
        """Test if we can authenticate with the host."""
        return True


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    # TODO validate the data can be used to set up a connection.

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data["username"], data["password"]
    # )

    hub = PlaceholderHub(data["host"])

    if not await hub.authenticate(data["username"], data["password"]):
        raise InvalidAuth

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    # Return info that you want to store in the config entry.
    return {"title": "Name of the device"}


class LutronCasetaProConfig():

    def __init__(self, host, mac):
        self.host = host
        self.mac = mac


class LutronCasetaProConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for lutron_caseta_pro."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    def __init__(self):
        """Initialize the config flow."""
        self.config = None

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                host = user_input.get(CONF_HOST)
                mac = user_input.get(CONF_MAC)
                self.config = LutronCasetaProConfig(host, mac)
                return await self.async_step_integration()

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    async def async_step_integration(self, user_input=None):
        errors = {}
        if user_input is not None:
            integration_report = user_input.get(CONF_INTEGRATION_REPORT)
            pass

        return self.async_show_form(
            step_id="integration", data_schema=vol.Schema({CONF_INTEGRATION_REPORT: str}), errors=errors
        )

    async def async_step_zeroconf(self, discovery_info: DiscoveryInfoType):
        """Handle the zeroconf discovery."""
        _LOGGER.debug("discovered: %s", discovery_info)
        host = discovery_info['host']
        mac = discovery_info['properties']['MACADDR']
        self.config = LutronCasetaProConfig(host, mac)
        await self.async_set_unique_id(mac)
        self._abort_if_unique_id_configured()

        return await self.async_step_integration()



class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
