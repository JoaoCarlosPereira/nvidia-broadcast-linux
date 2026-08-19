# NVIDIA Broadcast for Linux
# Copyright (c) 2026 doczeus (https://github.com/Hkshoonya)
# Licensed under GPL-3.0 - see LICENSE file
"""Session orchestrator implementation separating runtime logic from GTK window UI."""

from typing import Dict, Optional, Callable
from nvbroadcast.core.state import AppState, EffectHealth, SessionOrchestrator
from nvbroadcast.core.config import AppConfig, save_config
from nvbroadcast.core.device_supervisor import DeviceSupervisor


class DefaultSessionOrchestrator:
    """Default implementation of SessionOrchestrator protocol."""

    def __init__(self, config: AppConfig,
                 start_fn: Optional[Callable[[], bool]] = None,
                 stop_fn: Optional[Callable[[], None]] = None,
                 set_effect_fn: Optional[Callable[[str, bool], EffectHealth]] = None,
                 switch_cam_fn: Optional[Callable[[str], None]] = None,
                 switch_mic_fn: Optional[Callable[[str], None]] = None,
                 device_supervisor: DeviceSupervisor | None = None):
        self._config = config
        self._state = AppState(
            streaming=False,
            camera_device=config.video.camera_device,
            camera_device_id=getattr(config.video, "camera_device_id", ""),
            microphone_device=config.audio.mic_device,
            speaker_device=config.audio.speaker_device,
        )
        self._start_fn = start_fn
        self._stop_fn = stop_fn
        self._set_effect_fn = set_effect_fn
        self._switch_cam_fn = switch_cam_fn
        self._switch_mic_fn = switch_mic_fn
        self._device_supervisor = device_supervisor

    @property
    def state(self) -> AppState:
        return self._state

    def snapshot(self) -> AppState:
        return AppState(
            streaming=self._state.streaming,
            camera_device=self._state.camera_device,
            camera_device_id=self._state.camera_device_id,
            microphone_device=self._state.microphone_device,
            speaker_device=self._state.speaker_device,
            effects_health=dict(self._state.effects_health),
            status_message=self._state.status_message,
        )

    def start_broadcast(self) -> bool:
        if self._start_fn:
            success = self._start_fn()
            self._state.streaming = bool(success)
            return success
        self._state.streaming = True
        return True

    def stop_broadcast(self) -> None:
        if self._stop_fn:
            self._stop_fn()
        self._state.streaming = False

    def set_effect(self, effect_id: str, enabled: bool) -> EffectHealth:
        if effect_id in ("room_echo", "studio_voice"):
            health = EffectHealth.UNAVAILABLE
            self._state.effects_health[effect_id] = health
            return health
        if self._set_effect_fn:
            health = self._set_effect_fn(effect_id, enabled)
        else:
            health = EffectHealth.OK if enabled else EffectHealth.OFF
        self._state.effects_health[effect_id] = health
        return health

    def switch_camera(self, device_id: str) -> None:
        if self._device_supervisor is not None:
            device_id = self._device_supervisor.switch_camera(device_id)
        self._state.camera_device = device_id
        self._state.camera_device_id = getattr(
            self._config.video, "camera_device_id", ""
        )
        if self._switch_cam_fn:
            self._switch_cam_fn(device_id)

    def switch_microphone(self, device_id: str) -> None:
        if self._device_supervisor is not None:
            device_id = self._device_supervisor.switch_microphone(device_id)
        self._state.microphone_device = device_id
        if self._switch_mic_fn:
            self._switch_mic_fn(device_id)
