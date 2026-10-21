"""Thin async client for the itsoft myOpen web service."""
from __future__ import annotations

import json
import logging
from typing import Any

import aiohttp

from .const import (
    APP_VERSION,
    BASE_URL,
    EP_ABRIR,
    EP_GENERAR,
    EP_VALIDAR,
    F_APPV,
    F_CODACTIV,
    F_IDACTIV,
    F_IDDISP,
    F_IDECOBOX,
    F_IDPROP,
    F_INFODISP,
    F_LANG,
    F_TEL,
    HTTP_TIMEOUT,
    INFO_DISPOSITIVO,
    R_CODE,
    R_ECOBOX_ID,
    R_ECOBOX_NAME,
    R_ERROR,
    R_LIST,
)

_LOGGER = logging.getLogger(__name__)


class MyOpenError(Exception):
    """Base error."""


class MyOpenAuthError(MyOpenError):
    """Registration / activation is no longer valid (code <= -1000)."""


class MyOpenApiError(MyOpenError):
    """The service returned a non-successful result."""

    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(message)
        self.code = code


def _unwrap(raw: str) -> dict[str, Any]:
    """Parse the response body into a dict.

    The ASMX methods normally return raw JSON with `code` at the top level,
    but we defensively handle the ASP.NET `{"d": ...}` envelope and a
    double-encoded JSON string, just in case.
    """
    data: Any = json.loads(raw)
    if isinstance(data, dict) and set(data.keys()) == {"d"}:
        data = data["d"]
    if isinstance(data, str):
        data = json.loads(data)
    if not isinstance(data, dict):
        raise MyOpenApiError(f"Unexpected response payload: {raw[:200]!r}")
    return data


class MyOpenClient:
    """Calls the three operations used by the mobile app."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        *,
        tel: str,
        iddisp: str,
        lang: str,
        verify_ssl: bool = False,
    ) -> None:
        self._session = session
        self._tel = tel
        self._iddisp = iddisp
        self._lang = lang
        self._verify_ssl = verify_ssl

    def _base_payload(self) -> dict[str, Any]:
        return {
            F_TEL: self._tel,
            F_IDDISP: self._iddisp,
            F_INFODISP: INFO_DISPOSITIVO,
            F_LANG: self._lang,
            F_APPV: APP_VERSION,
        }

    async def _post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{BASE_URL}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        }
        timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)
        try:
            async with self._session.post(
                url,
                data=json.dumps(payload),
                headers=headers,
                timeout=timeout,
                ssl=self._verify_ssl,
            ) as resp:
                text = await resp.text()
        except aiohttp.ClientError as err:
            raise MyOpenError(f"Connection error calling {endpoint}: {err}") from err

        data = _unwrap(text)
        return data

    @staticmethod
    def _result_code(data: dict[str, Any]) -> int:
        try:
            return int(str(data.get(R_CODE)))
        except (TypeError, ValueError):
            return -3  # ESTADO_ERROR_GENERICO

    def _raise_for_result(self, data: dict[str, Any]) -> None:
        code = self._result_code(data)
        if code > 0:
            return
        message = data.get(R_ERROR) or f"Service returned code {code}"
        # <= -1000 means the registration/activation is invalid -> reauth.
        if code <= -1000:
            raise MyOpenAuthError(message)
        raise MyOpenApiError(message, code)

    # --- Operations ----------------------------------------------------
    async def solicitar_registro(self) -> dict[str, str]:
        """GenerarCodigoActivacion: triggers the SMS. Returns idprop/idactiv."""
        data = await self._post(EP_GENERAR, self._base_payload())
        self._raise_for_result(data)
        return {
            F_IDPROP: str(data.get(F_IDPROP, "")),
            F_IDACTIV: str(data.get(F_IDACTIV, "")),
        }

    async def validar_registro(
        self, *, idprop: str, idactiv: str, codactiv: str
    ) -> list[dict[str, str]]:
        """ValidarCodigoActivacion: validates the code and returns the doors."""
        payload = self._base_payload()
        payload[F_IDPROP] = idprop
        payload[F_IDACTIV] = idactiv
        payload[F_CODACTIV] = codactiv
        data = await self._post(EP_VALIDAR, payload)
        self._raise_for_result(data)
        doors: list[dict[str, str]] = []
        for item in data.get(R_LIST, []) or []:
            doors.append(
                {
                    "id": str(item.get(R_ECOBOX_ID, "")),
                    "nombre": str(item.get(R_ECOBOX_NAME, "")),
                }
            )
        return doors

    async def abrir_puerta(
        self, *, idprop: str, idactiv: str, codactiv: str, idecobox: str
    ) -> None:
        """AbrirPuerta: opens the given door."""
        payload = self._base_payload()
        payload[F_IDPROP] = idprop
        payload[F_IDACTIV] = idactiv
        payload[F_CODACTIV] = codactiv
        payload[F_IDECOBOX] = idecobox
        data = await self._post(EP_ABRIR, payload)
        self._raise_for_result(data)
