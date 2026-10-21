"""Config flow for myOpen: phone number -> SMS code -> door list."""
from __future__ import annotations

import uuid
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    MyOpenApiError,
    MyOpenAuthError,
    MyOpenClient,
    MyOpenError,
)
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
    F_IDACTIV,
    F_IDPROP,
)


class MyOpenConfigFlow(ConfigFlow, domain=DOMAIN):
    """Two-step flow mirroring the mobile app's activation."""

    VERSION = 1

    def __init__(self) -> None:
        self._tel: str = ""
        self._lang: str = DEFAULT_LANG
        self._verify_ssl: bool = False
        self._iddisp: str = ""
        self._idprop: str = ""
        self._idactiv: str = ""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the phone number and request the SMS code."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._tel = user_input[CONF_TEL].strip()
            self._lang = user_input.get(CONF_LANG, DEFAULT_LANG).strip() or DEFAULT_LANG
            self._verify_ssl = user_input.get(CONF_VERIFY_SSL, False)

            await self.async_set_unique_id(self._tel)
            self._abort_if_unique_id_configured()

            self._iddisp = str(uuid.uuid4())
            client = MyOpenClient(
                async_get_clientsession(self.hass),
                tel=self._tel,
                iddisp=self._iddisp,
                lang=self._lang,
                verify_ssl=self._verify_ssl,
            )
            try:
                ids = await client.solicitar_registro()
            except MyOpenAuthError as err:
                errors["base"] = "invalid_auth"
                self._set_desc(err)
            except MyOpenApiError as err:
                errors["base"] = "service_error"
                self._set_desc(err)
            except MyOpenError as err:
                errors["base"] = "cannot_connect"
                self._set_desc(err)
            else:
                self._idprop = ids[F_IDPROP]
                self._idactiv = ids[F_IDACTIV]
                return await self.async_step_sms()

        schema = vol.Schema(
            {
                vol.Required(CONF_TEL): str,
                vol.Optional(CONF_LANG, default=DEFAULT_LANG): str,
                vol.Optional(CONF_VERIFY_SSL, default=False): bool,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    async def async_step_sms(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the received SMS code and validate it."""
        errors: dict[str, str] = {}
        if user_input is not None:
            code = user_input[CONF_PIN].strip()
            client = MyOpenClient(
                async_get_clientsession(self.hass),
                tel=self._tel,
                iddisp=self._iddisp,
                lang=self._lang,
                verify_ssl=self._verify_ssl,
            )
            try:
                doors = await client.validar_registro(
                    idprop=self._idprop,
                    idactiv=self._idactiv,
                    codactiv=code,
                )
            except MyOpenAuthError as err:
                errors["base"] = "invalid_code"
                self._set_desc(err)
            except MyOpenApiError as err:
                errors["base"] = "service_error"
                self._set_desc(err)
            except MyOpenError as err:
                errors["base"] = "cannot_connect"
                self._set_desc(err)
            else:
                return self.async_create_entry(
                    title=f"myOpen ({self._tel})",
                    data={
                        CONF_TEL: self._tel,
                        CONF_IDDISP: self._iddisp,
                        CONF_IDPROP: self._idprop,
                        CONF_IDACTIV: self._idactiv,
                        CONF_PIN: code,
                        CONF_LANG: self._lang,
                        CONF_VERIFY_SSL: self._verify_ssl,
                    },
                )

        schema = vol.Schema({vol.Required(CONF_PIN): str})
        return self.async_show_form(
            step_id="sms",
            data_schema=schema,
            errors=errors,
            description_placeholders={"tel": self._tel},
        )

    def _set_desc(self, err: Exception) -> None:
        """Store last error text (shown via logs)."""
        self.context["last_error"] = str(err)
