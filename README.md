# myOpen para Home Assistant

Integración no oficial para el servicio **myOpen** de itsoft
(`com.itsoft.myopen`), que permite abrir puertas/porteros ("ecoboxes")
desde Home Assistant. Reproduce exactamente el protocolo de la app Android.

## Qué hace

- **Alta por SMS** desde la propia interfaz de Home Assistant (config flow):
  1. Introduces tu **número de móvil** → se solicita el código y lo recibes por SMS.
  2. Introduces el **código SMS** → el servicio devuelve tu lista de puertas.
- Crea una **entidad `button` por cada puerta**. Pulsarla (o dispararla desde
  una automatización) ejecuta la apertura (`AbrirPuerta`).
- Refresca la lista de puertas periódicamente (cada 6 h).

El registro es persistente: tras validar una vez, se guardan `idprop`,
`idactiv` y el código, y se reutilizan para abrir sin pedir más SMS (igual que
la app). Si el servicio invalida el registro (códigos ≤ -1000), Home Assistant
pedirá reconfigurar.

## Protocolo (extraído de la app v2.6)

Endpoint base: `https://quencher.itsoft.es/Operaciones.asmx`
Los métodos aceptan un cuerpo **JSON** por POST y devuelven **JSON** con
`code` (>0 = éxito), `error`, y en la validación `listecobox`.

Campos comunes en cada petición: `tel`, `iddisp` (UUID generado una vez),
`infodisp="android"`, `lang`, `appv`.

| Operación | Endpoint | Campos extra | Respuesta |
|-----------|----------|--------------|-----------|
| Solicitar código | `/GenerarCodigoActivacion` | — | `idprop`, `idactiv` |
| Validar código | `/ValidarCodigoActivacion` | `idprop`, `idactiv`, `codactiv` | `listecobox[]` → `{id, nombre}` |
| Abrir puerta | `/AbrirPuerta` | `idprop`, `idactiv`, `codactiv`, `idecobox` | `code` |

> El certificado del servidor puede no validar correctamente (la app original
> desactiva la verificación TLS). Por eso la integración **no verifica SSL por
> defecto**; puedes activarlo con la casilla "Verificar certificado SSL" al dar
> de alta si tu servidor tiene un certificado válido.

## Instalación

### Opción A — HACS (recomendada, con actualizaciones)

> HACS **solo soporta GitHub**. El repo debe estar en GitHub para que HACS
> pueda detectar nuevas versiones.

1. En Home Assistant: **HACS → ⋮ (arriba a la derecha) → Repositorios
   personalizados**.
2. Pega la URL de este repositorio (`https://github.com/zoltyvigo/ha-myopen`)
   y en "Categoría" elige **Integration**. Pulsa **Añadir**.
3. Busca **"myOpen"** en HACS, ábrelo y pulsa **Descargar**.
4. **Reinicia Home Assistant**.
5. **Ajustes → Dispositivos y servicios → Añadir integración → "myOpen"** y
   sigue los dos pasos (teléfono y código SMS).

Las actualizaciones aparecerán en HACS cada vez que publiques una nueva
**Release** en GitHub (ver "Publicar versiones" más abajo).

### Opción B — Manual

1. Copia la carpeta `custom_components/myopen` dentro de la carpeta
   `config/custom_components/` de tu instalación de Home Assistant.
2. Reinicia Home Assistant.
3. **Ajustes → Dispositivos y servicios → Añadir integración → "myOpen"**.
4. Sigue los dos pasos (teléfono y código SMS).

## Icono / logo de la integración

Desde **Home Assistant 2026.3** las integraciones personalizadas pueden incluir
su propio icono directamente, sin pasar por el repositorio `home-assistant/brands`
(que ya **no acepta** iconos de integraciones personalizadas). El icono va en una
carpeta `brand/` dentro de la integración y tiene prioridad sobre la CDN:

```
custom_components/myopen/brand/icon.png      (256x256)
custom_components/myopen/brand/icon@2x.png   (512x512)
```

Como el icono de myOpen es cuadrado, solo se incluye el icono (no hace falta
`logo.png`). No requiere ningún cambio en `manifest.json`. Se muestra tras
reiniciar Home Assistant.

> Requiere HA 2026.3 o superior. En versiones anteriores este método no existe
> y se vería "icon not available"; la integración funciona igual en cualquier
> caso (las entidades de puerta usan `mdi:door-open`).

## Publicar versiones (para que HACS detecte actualizaciones)

HACS usa las **Releases/tags de GitHub**, no el número del `manifest.json`.
Para publicar una actualización:

1. Sube tus cambios y **sube también** el `version` del `manifest.json`
   (por ejemplo `1.0.1`).
2. Crea una release en GitHub con un tag igual, p. ej. `v1.0.1`
   (o `1.0.1`). Desde la web: **Releases → Draft a new release**, o por consola:
   ```bash
   git tag v1.0.1 && git push origin v1.0.1
   ```
3. En unas horas (o forzando refresco en HACS) aparecerá el botón de
   actualizar en la tarjeta de la integración dentro de HACS.

## Uso en automatizaciones

Cada puerta es un `button.<nombre_puerta>`. Para abrir desde una automatización:

```yaml
action:
  - service: button.press
    target:
      entity_id: button.portal
```

Y una pulsación del botón puede usarse como *disparador* de otras
automatizaciones con el trigger de estado del botón.

## Aviso

Software de interoperabilidad hecho a partir de la app propia del usuario. No
está afiliado a itsoft. Úsalo solo con tu propia cuenta y puertas autorizadas.
