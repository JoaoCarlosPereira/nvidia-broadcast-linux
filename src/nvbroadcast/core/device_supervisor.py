# NVIDIA Broadcast for Linux
# Copyright (c) 2026 doczeus (https://github.com/Hkshoonya)
# Licensed under GPL-3.0 - see LICENSE file
"""Device enumeration, selection, and recovery policy.

The supervisor deliberately does not own GTK or GStreamer objects.  It owns
the device identity and health transitions while the application supplies the
callbacks that rebuild the active media components.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from nvbroadcast.audio.devices import list_microphones
from nvbroadcast.core.config import AppConfig, save_config
from nvbroadcast.core.state import EffectHealth
from nvbroadcast.video.virtual_camera import (
    clear_camera_probe_cache,
    is_usable_camera_device,
    list_camera_devices,
    persistent_camera_device,
    resolve_camera_device,
)


@dataclass(frozen=True)
class DeviceHealth:
    """Runtime health snapshot for a physical input."""

    health: EffectHealth = EffectHealth.OFF
    message: str = ""
    recovery_attempt: int = 0


class DeviceSupervisor:
    """Coordinate camera and microphone changes without process restarts."""

    def __init__(
        self,
        config: AppConfig,
        *,
        on_camera_switch: Callable[[str], None] | None = None,
        on_microphone_switch: Callable[[str], None] | None = None,
        on_health: Callable[[str, EffectHealth, str], None] | None = None,
        camera_list_fn: Callable[[], list[dict[str, str]]] = list_camera_devices,
        microphone_list_fn: Callable[[], list[dict[str, str]]] = list_microphones,
    ) -> None:
        self.config = config
        self._on_camera_switch = on_camera_switch
        self._on_microphone_switch = on_microphone_switch
        self._on_health = on_health
        self._camera_list_fn = camera_list_fn
        self._microphone_list_fn = microphone_list_fn
        self._health: dict[str, DeviceHealth] = {}

    def list_cameras(self) -> list[dict[str, str]]:
        return self._camera_list_fn()

    def list_microphones(self) -> list[dict[str, str]]:
        return self._microphone_list_fn()

    def stable_camera_id(self, device: str) -> str:
        """Prefer udev by-id, with by-path/device as the fallback."""
        return persistent_camera_device(device)

    def _set_health(
        self, device_kind: str, health: EffectHealth, message: str = "",
        recovery_attempt: int = 0,
    ) -> None:
        self._health[device_kind] = DeviceHealth(
            health=health,
            message=message,
            recovery_attempt=recovery_attempt,
        )
        if self._on_health is not None:
            self._on_health(device_kind, health, message)

    def health(self, device_kind: str) -> DeviceHealth:
        return self._health.get(device_kind, DeviceHealth())

    def switch_camera(self, device: str) -> str:
        """Persist a camera selection and ask the app to rebuild capture."""
        if not device:
            raise ValueError("camera device cannot be empty")
        selected = resolve_camera_device(device)
        if not selected or not is_usable_camera_device(selected):
            raise ValueError(f"camera device is unavailable: {device}")
        stable_id = self.stable_camera_id(selected)
        self.config.video.camera_device = selected
        self.config.video.camera_device_id = (
            stable_id if stable_id != selected else ""
        )
        save_config(self.config)
        self._set_health("camera", EffectHealth.RECOVERING, "Switching camera")
        if self._on_camera_switch is not None:
            self._on_camera_switch(selected)
        return selected

    def switch_microphone(self, device: str) -> str:
        """Persist a microphone selection and ask the app to rebuild audio."""
        self.config.audio.mic_device = device
        save_config(self.config)
        self._set_health("microphone", EffectHealth.RECOVERING, "Switching microphone")
        if self._on_microphone_switch is not None:
            self._on_microphone_switch(device)
        return device

    def mark_camera_failed(self, message: str) -> None:
        """Expose the failed/recovering transition to the UI."""
        self._set_health("camera", EffectHealth.FAILED, message)
        self._set_health("camera", EffectHealth.RECOVERING, message)

    def mark_microphone_failed(self, message: str) -> None:
        self._set_health("microphone", EffectHealth.FAILED, message)
        self._set_health("microphone", EffectHealth.RECOVERING, message)

    def recover_camera(self, *, max_attempts: int = 20) -> str | None:
        """Resolve the configured stable camera after a hotplug event."""
        clear_camera_probe_cache()
        stable_id = getattr(self.config.video, "camera_device_id", "")
        candidate = stable_id or self.config.video.camera_device
        if stable_id:
            if is_usable_camera_device(stable_id):
                return stable_id
            return None
        resolved = resolve_camera_device(candidate)
        if resolved and is_usable_camera_device(resolved):
            return resolved
        return None

