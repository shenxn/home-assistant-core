"""Provides device actions for Xiaomi Gateway (Aqara)."""
from typing import List, Optional

import voluptuous as vol

from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_TYPE
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import config_validation as cv, device_registry

from . import (
    ATTR_GW_MAC,
    ATTR_RINGTONE_ID,
    ATTR_RINGTONE_VOL,
    DOMAIN,
    RINGTONES,
    SERVICE_PLAY_RINGTONE,
    SERVICE_STOP_RINGTONE,
)

ACTION_PLAY_RINGTONE = "play_ringtone"
ACTION_STOP_RINGTONE = "stop_ringtone"

ACTION_TYPES = {
    ACTION_PLAY_RINGTONE,
    ACTION_STOP_RINGTONE,
}

VALID_RINGTONE_ID = vol.In(RINGTONES)
VALID_RINGTONE_VOL = vol.All(vol.Coerce(int), vol.Clamp(min=0, max=100))

CONF_SUBDEVICE_ID = "subdevice_id"

ACTION_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(ACTION_TYPES),
        vol.Optional(ATTR_RINGTONE_ID): VALID_RINGTONE_ID,
        vol.Optional(ATTR_RINGTONE_VOL): VALID_RINGTONE_VOL,
    }
)


async def _async_get_aqara_gateway_sid(
    hass: HomeAssistant, device_id: str
) -> Optional[str]:
    dr = await device_registry.async_get_registry(hass)
    registry_device = dr.async_get(device_id)
    if registry_device.via_device_id is not None:
        # This is not a gateway
        return None
    return list(list(registry_device.identifiers)[0])[1]


async def async_get_actions(hass: HomeAssistant, device_id: str) -> List[dict]:
    """List device actions for Xiaomi Gateway (Aqara) devices."""
    sid = await _async_get_aqara_gateway_sid(hass, device_id)
    if sid is None:
        return []

    return [
        {CONF_DEVICE_ID: device_id, CONF_DOMAIN: DOMAIN, CONF_TYPE: action}
        for action in ACTION_TYPES
    ]


async def async_get_action_capabilities(hass: HomeAssistant, config: dict) -> dict:
    """List action capabilities."""
    extra_fields = {}
    if config[CONF_TYPE] == ACTION_PLAY_RINGTONE:
        extra_fields = {
            vol.Required(ATTR_RINGTONE_ID): VALID_RINGTONE_ID,
            vol.Optional(ATTR_RINGTONE_VOL): VALID_RINGTONE_VOL,
        }
    else:
        return {}
    return {"extra_fields": vol.Schema(extra_fields)}


async def async_call_action_from_config(
    hass: HomeAssistant, config: dict, variables: dict, context: Optional[Context]
) -> None:
    """Execute a device action."""
    sid = await _async_get_aqara_gateway_sid(hass, config[CONF_DEVICE_ID])
    if sid is None:
        return
    service_data = {ATTR_GW_MAC: sid}

    if config[CONF_TYPE] == ACTION_PLAY_RINGTONE:
        service = SERVICE_PLAY_RINGTONE
        service_data[ATTR_RINGTONE_ID] = config[ATTR_RINGTONE_ID]
        if ATTR_RINGTONE_VOL in config:
            service_data[ATTR_RINGTONE_VOL] = config[ATTR_RINGTONE_VOL]
    elif config[CONF_TYPE] == ACTION_STOP_RINGTONE:
        service = SERVICE_STOP_RINGTONE
    else:
        return

    await hass.services.async_call(
        DOMAIN, service, service_data, blocking=True, context=context
    )
