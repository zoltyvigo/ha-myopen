"""Constants for the myOpen (itsoft) integration."""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "myopen"

# --- API ---------------------------------------------------------------
# Base endpoint of the itsoft "Operaciones" web service. The ASMX methods
# read the raw JSON request body and return raw JSON (top-level `code`).
BASE_URL = "https://quencher.itsoft.es/Operaciones.asmx"

EP_GENERAR = "/GenerarCodigoActivacion"   # request SMS activation code
EP_VALIDAR = "/ValidarCodigoActivacion"   # validate SMS code -> door list
EP_ABRIR = "/AbrirPuerta"                 # open a door

# Fixed request fields (see PeticionConCamposPorDefecto in the app).
INFO_DISPOSITIVO = "android"              # TIPO_TERMINAL_PARAM_WS
APP_VERSION = "APP:2.6-S.O.:13-SDK:33"    # getVersionApp() format
DEFAULT_LANG = "es"

HTTP_TIMEOUT = 40  # seconds, matches TIMEOUT_CONEXIONES_MS (40000)

# JSON field names (tags) used by the service.
F_IDPROP = "idprop"
F_TEL = "tel"
F_IDDISP = "iddisp"
F_INFODISP = "infodisp"
F_IDACTIV = "idactiv"
F_CODACTIV = "codactiv"
F_IDECOBOX = "idecobox"
F_LANG = "lang"
F_APPV = "appv"

# Response tags.
R_CODE = "code"
R_ERROR = "error"
R_LIST = "listecobox"
R_ECOBOX_ID = "id"
R_ECOBOX_NAME = "nombre"

# --- Config entry data keys -------------------------------------------
CONF_TEL = "tel"
CONF_IDDISP = "iddisp"
CONF_IDPROP = "idprop"
CONF_IDACTIV = "idactiv"
CONF_PIN = "pin"            # the SMS code, reused for every later call
CONF_LANG = "lang"
CONF_VERIFY_SSL = "verify_ssl"
CONF_DOORS = "doors"       # cached list [{id, nombre}] from validation

# How often to refresh the door list (ValidarCodigoActivacion).
SCAN_INTERVAL = timedelta(hours=6)
