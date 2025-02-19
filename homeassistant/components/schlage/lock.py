"""Platform for Schlage lock integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import LockData, SchlageConfigEntry, SchlageDataUpdateCoordinator
from .entity import SchlageEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SchlageConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Schlage WiFi locks based on a config entry."""
    coordinator = config_entry.runtime_data

    def _add_new_locks(locks: dict[str, LockData]) -> None:
        async_add_entities(
            SchlageLockEntity(coordinator=coordinator, device_id=device_id)
            for device_id in locks
        )

    _add_new_locks(coordinator.data.locks)
    coordinator.new_locks_callbacks.append(_add_new_locks)


class SchlageLockEntity(SchlageEntity, LockEntity):
    """Schlage lock entity."""

    _attr_name = None

    def __init__(
        self, coordinator: SchlageDataUpdateCoordinator, device_id: str
    ) -> None:
        """Initialize a Schlage Lock."""
        super().__init__(coordinator=coordinator, device_id=device_id)
        self._update_attrs()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.device_id in self.coordinator.data.locks:
            self._update_attrs()
        super()._handle_coordinator_update()

    def _update_attrs(self) -> None:
        """Update our internal state attributes."""
        self._attr_is_locked = self._lock.is_locked
        self._attr_is_jammed = self._lock.is_jammed
        self._attr_changed_by = self._lock.last_changed_by()

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the device."""
        await self.hass.async_add_executor_job(self._lock.lock)
        await self.coordinator.async_request_refresh()

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the device."""
        await self.hass.async_add_executor_job(self._lock.unlock)
        await self.coordinator.async_request_refresh()
