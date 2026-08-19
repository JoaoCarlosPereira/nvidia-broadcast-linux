# NVIDIA Broadcast for Linux
# Copyright (c) 2026 doczeus (https://github.com/Hkshoonya)
# Licensed under GPL-3.0 - see LICENSE file
"""Runtime application state, effect health, and session orchestrator contract."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Protocol, Optional


class EffectHealth(str, Enum):
    OFF = "off"
    OK = "ok"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"
    RECOVERING = "recovering"


@dataclass
class AppState:
    streaming: bool = False
    camera_device: str = "/dev/video0"
    camera_device_id: str = ""
    microphone_device: str = ""
    speaker_device: str = ""
    effects_health: Dict[str, EffectHealth] = field(default_factory=dict)
    status_message: str = ""


class SessionOrchestrator(Protocol):
    def start_broadcast(self) -> bool: ...
    def stop_broadcast(self) -> None: ...
    def set_effect(self, effect_id: str, enabled: bool) -> EffectHealth: ...
    def switch_camera(self, device_id: str) -> None: ...
    def switch_microphone(self, device_id: str) -> None: ...
    def snapshot(self) -> AppState: ...
