"""Coordinator: keeps the door list in sync via ValidarCodigoActivacion."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MyOpenAuthError, MyOpenClient, MyOpenError
from .const import (
    CONF_IDACTIV,
    CONF_IDDISP,
    CONF_IDPROP,
    CONF_LANG,
    CONF_PIN,
    CONF_TEL,
    CONF_VERIFY_SSL,
    DEFAULT_LANG,
    DOMAIN,
    SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class MyOpenCoordinator(DataUpdateCoordinator[list[dict[str, str]]]):
    """Fetches and caches the list of doors (ecoboxes)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.entry = entry
        self.client = MyOpenClient(
            async_get_clientsession(hass),
            tel=entry.data[CONF_TEL],
            iddisp=entry.data[CONF_IDDISP],
            lang=entry.data.get(CONF_LANG, DEFAULT_LANG),
            verify_ssl=entry.data.get(CONF_VERIFY_SSL, False),
        )

    async def _async_update_data(self) -> list[dict[str, str]]:
        try:
            return await self.client.validar_registro(
                idprop=self.entry.data[CONF_IDPROP],
                idactiv=self.entry.data[CONF_IDACTIV],
                codactiv=self.entry.data[CONF_PIN],
            )
        except MyOpenAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except MyOpenError as err:
            raise UpdateFailed(str(err)) from err

    async def async_open_door(self, door_id: str) -> None:
        """Open a door by its ecobox id."""
        await self.client.abrir_puerta(
            idprop=self.entry.data[CONF_IDPROP],
            idactiv=self.entry.data[CONF_IDACTIV],
            codactiv=self.entry.data[CONF_PIN],
            idecobox=door_id,
        )
