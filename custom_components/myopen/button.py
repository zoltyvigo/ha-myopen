"""Button entities: one per door, pressing it opens the door."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MyOpenConfigEntry
from .api import MyOpenError
from .const import CONF_TEL, DOMAIN
from .coordinator import MyOpenCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MyOpenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create a button for every door returned by the service."""
    coordinator = entry.runtime_data
    known: set[str] = set()

    def _sync() -> None:
        new = []
        for door in coordinator.data or []:
            door_id = door["id"]
            if door_id and door_id not in known:
                known.add(door_id)
                new.append(MyOpenDoorButton(coordinator, door_id, door["nombre"]))
        if new:
            async_add_entities(new)

    _sync()
    entry.async_on_unload(coordinator.async_add_listener(_sync))


class MyOpenDoorButton(CoordinatorEntity[MyOpenCoordinator], ButtonEntity):
    """A door opener. Press = open (fires AbrirPuerta)."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:door-open"

    def __init__(
        self, coordinator: MyOpenCoordinator, door_id: str, name: str
    ) -> None:
        super().__init__(coordinator)
        self._door_id = door_id
        self._attr_name = name or f"Door {door_id}"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{door_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=f"myOpen ({coordinator.entry.data[CONF_TEL]})",
            manufacturer="itsoft",
            model="myOpen",
        )

    @property
    def name(self) -> str | None:
        """Keep the entity name in sync with the latest door name."""
        for door in self.coordinator.data or []:
            if door["id"] == self._door_id:
                return door["nombre"] or f"Door {self._door_id}"
        return self._attr_name

    @property
    def available(self) -> bool:
        return super().available and any(
            d["id"] == self._door_id for d in (self.coordinator.data or [])
        )

    async def async_press(self) -> None:
        """Open the door."""
        try:
            await self.coordinator.async_open_door(self._door_id)
        except MyOpenError as err:
            raise HomeAssistantError(f"Failed to open door: {err}") from err
