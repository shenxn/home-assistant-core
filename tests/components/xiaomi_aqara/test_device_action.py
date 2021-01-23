"""The tests for Xiaomi Gateway (Aqara) device actions."""
import pytest
import voluptuous as vol
import voluptuous_serialize

from homeassistant.components import automation
from homeassistant.components.xiaomi_aqara import (
    ATTR_GW_MAC,
    ATTR_RINGTONE_ID,
    ATTR_RINGTONE_VOL,
    DOMAIN,
    SERVICE_PLAY_RINGTONE,
    SERVICE_STOP_RINGTONE,
)
from homeassistant.components.xiaomi_aqara.device_action import (
    ACTION_PLAY_RINGTONE,
    ACTION_STOP_RINGTONE,
    ACTION_TYPES,
    VALID_RINGTONE_ID,
    VALID_RINGTONE_VOL,
)
from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.device_registry import DeviceEntry, DeviceRegistry
from homeassistant.setup import async_setup_component

from tests.common import (
    MockConfigEntry,
    assert_lists_same,
    async_get_device_automation_capabilities,
    async_get_device_automations,
    async_mock_service,
    mock_device_registry,
)

SID = "xxxxxxxxxxxx"


@pytest.fixture
def device_reg(hass: HomeAssistant) -> DeviceRegistry:
    """Return an empty, loaded, registry."""
    return mock_device_registry(hass)


@pytest.fixture
async def gateway_entry(hass: HomeAssistant, device_reg: DeviceRegistry) -> DeviceEntry:
    """Return a device entry of a Xiaomi Aqara gateway."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)
    return device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, SID)},
    )


async def test_get_actions_gateway(
    hass: HomeAssistant, gateway_entry: DeviceEntry
) -> None:
    """Test we get the expected actions from a gateway."""
    expected_actions = [
        {
            "domain": DOMAIN,
            "type": action_type,
            "device_id": gateway_entry.id,
        }
        for action_type in ACTION_TYPES
    ]
    actions = await async_get_device_automations(hass, "action", gateway_entry.id)
    assert_lists_same(actions, expected_actions)


async def test_get_actions_subdevice(
    hass: HomeAssistant, device_reg: DeviceRegistry, gateway_entry: DeviceEntry
) -> None:
    """Test we don't get any action from a subdevice."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, "yyyyyyyyyyyy")},
        via_device=(DOMAIN, SID),
    )
    actions = await async_get_device_automations(hass, "action", device_entry.id)
    assert_lists_same(actions, [])


@pytest.mark.parametrize(
    "action_type,extra_fields",
    [
        (
            ACTION_PLAY_RINGTONE,
            {
                vol.Required(ATTR_RINGTONE_ID): VALID_RINGTONE_ID,
                vol.Optional(ATTR_RINGTONE_VOL): VALID_RINGTONE_VOL,
            },
        ),
        (ACTION_STOP_RINGTONE, {}),
    ],
)
async def test_get_action_capabilities(
    hass: HomeAssistant,
    gateway_entry: DeviceEntry,
    action_type: str,
    extra_fields: dict,
) -> None:
    """Test we get the expected action capabilities."""
    capabilities = await async_get_device_automation_capabilities(
        hass,
        "action",
        {
            CONF_DEVICE_ID: gateway_entry.id,
            CONF_DOMAIN: DOMAIN,
            CONF_TYPE: action_type,
        },
    )
    extra_fields = voluptuous_serialize.convert(
        vol.Schema(extra_fields), custom_serializer=cv.custom_serializer
    )
    assert capabilities == {"extra_fields": extra_fields}


@pytest.mark.parametrize(
    "action_type,extra_fields,service",
    [
        (ACTION_PLAY_RINGTONE, {ATTR_RINGTONE_ID: 5}, SERVICE_PLAY_RINGTONE),
        (
            ACTION_PLAY_RINGTONE,
            {ATTR_RINGTONE_ID: 3, ATTR_RINGTONE_VOL: 50},
            SERVICE_PLAY_RINGTONE,
        ),
        (ACTION_STOP_RINGTONE, {}, SERVICE_STOP_RINGTONE),
    ],
)
async def test_action(
    hass: HomeAssistant,
    gateway_entry: DeviceEntry,
    action_type: str,
    extra_fields: dict,
    service: str,
):
    """Test for the actions."""
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": f"test_event_{action_type}",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": gateway_entry.id,
                        "type": action_type,
                        **extra_fields,
                    },
                }
            ]
        },
    )

    service_calls = async_mock_service(hass, DOMAIN, service)
    hass.bus.async_fire(f"test_event_{action_type}")
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    service_call = service_calls[0]
    assert service_call.data[ATTR_GW_MAC] == SID
    for key, value in extra_fields.items():
        assert service_call.data[key] == value
