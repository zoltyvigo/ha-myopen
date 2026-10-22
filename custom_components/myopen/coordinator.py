"""Coordinator: keeps the door list in sync via ValidarCodigoActivacion."""
from __future__ import annotations

import asyncio
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

# Seconds to wait before the single retry on a transient open failure.
OPEN_RETRY_DELAY = 3


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
        """Open a door by its ecobox id.

        Retries once after a short wait on transient failures (server/door
        connectivity). Does not retry when the registration is invalid
        (MyOpenAuthError), since that needs re-validation. Raises
        MyOpenApiError / MyOpenError on failure; callers format the message.
        """
        try:
            await self._abrir(door_id)
            return
        except MyOpenAuthError:
            raise
        except MyOpenError as first_err:
            _LOGGER.debug(
                "Open of door %s failed (%s); retrying once in %ss",
                door_id,
                first_err,
                OPEN_RETRY_DELAY,
            )

        await asyncio.sleep(OPEN_RETRY_DELAY)
        await self._abrir(door_id)

    async def _abrir(self, door_id: str) -> None:
        await self.client.abrir_puerta(
            idprop=self.entry.data[CONF_IDPROP],
            idactiv=self.entry.data[CONF_IDACTIV],
            codactiv=self.entry.data[CONF_PIN],
            idecobox=door_id,
        )
