import unittest
from nvbroadcast.core.config import AppConfig
from nvbroadcast.core.state import AppState, EffectHealth
from nvbroadcast.core.orchestrator import DefaultSessionOrchestrator


class SessionOrchestratorTests(unittest.TestCase):
    def test_orchestrator_snapshot_and_state(self):
        config = AppConfig()
        config.video.camera_device = "/dev/video0"
        orchestrator = DefaultSessionOrchestrator(config)

        state = orchestrator.snapshot()
        self.assertIsInstance(state, AppState)
        self.assertFalse(state.streaming)
        self.assertEqual(state.camera_device, "/dev/video0")

    def test_start_and_stop_broadcast(self):
        config = AppConfig()
        orchestrator = DefaultSessionOrchestrator(config)

        self.assertTrue(orchestrator.start_broadcast())
        self.assertTrue(orchestrator.snapshot().streaming)

        orchestrator.stop_broadcast()
        self.assertFalse(orchestrator.snapshot().streaming)

    def test_unavailable_effects_health(self):
        config = AppConfig()
        orchestrator = DefaultSessionOrchestrator(config)

        health_echo = orchestrator.set_effect("room_echo", True)
        self.assertEqual(health_echo, EffectHealth.UNAVAILABLE)

        health_voice = orchestrator.set_effect("studio_voice", True)
        self.assertEqual(health_voice, EffectHealth.UNAVAILABLE)

        state = orchestrator.snapshot()
        self.assertEqual(state.effects_health["room_echo"], EffectHealth.UNAVAILABLE)
        self.assertEqual(state.effects_health["studio_voice"], EffectHealth.UNAVAILABLE)

    def test_switch_camera_and_microphone(self):
        config = AppConfig()
        switched_cam = []
        switched_mic = []

        orchestrator = DefaultSessionOrchestrator(
            config,
            switch_cam_fn=lambda dev: switched_cam.append(dev),
            switch_mic_fn=lambda dev: switched_mic.append(dev),
        )

        orchestrator.switch_camera("/dev/video2")
        self.assertEqual(switched_cam, ["/dev/video2"])
        self.assertEqual(orchestrator.snapshot().camera_device, "/dev/video2")

        orchestrator.switch_microphone("alsa_input.pci")
        self.assertEqual(switched_mic, ["alsa_input.pci"])
        self.assertEqual(orchestrator.snapshot().microphone_device, "alsa_input.pci")


if __name__ == "__main__":
    unittest.main()
