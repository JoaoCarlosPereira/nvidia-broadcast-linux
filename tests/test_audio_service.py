import base64
import json
import unittest
from types import SimpleNamespace
from unittest import mock

from nvbroadcast.audio import service


class AudioServiceTests(unittest.TestCase):
    def test_zero_noise_intensity_bypasses_noise_model(self):
        fake_pipeline = mock.Mock()
        fake_pipeline.effects = SimpleNamespace()
        fake_pipeline.voice_fx = SimpleNamespace()

        with mock.patch("nvbroadcast.audio.service.AudioPipeline", return_value=fake_pipeline):
            result = service._build_pipeline({
                "noise_removal": True,
                "noise_intensity": 0.0,
            })

        self.assertIs(result, fake_pipeline)
        self.assertEqual(fake_pipeline.effects.intensity, 0.0)
        self.assertFalse(fake_pipeline.effects.enabled)
        fake_pipeline.build.assert_called_once_with()

    def test_service_stops_when_parent_pid_changes(self):
        state = base64.urlsafe_b64encode(
            json.dumps({"sample_rate": 48000}).encode("utf-8")
        ).decode("ascii")
        fake_pipeline = mock.Mock()
        fake_pipeline._running = True

        fake_event = mock.Mock()
        fake_event.wait.return_value = False

        with mock.patch("nvbroadcast.audio.service._build_pipeline", return_value=fake_pipeline), \
             mock.patch("nvbroadcast.audio.service.threading.Event", return_value=fake_event), \
             mock.patch("nvbroadcast.audio.service.os.getppid", return_value=999):
            rc = service.main(["--state-b64", state, "--parent-pid", "123"])

        self.assertEqual(rc, 0)
        fake_pipeline.start.assert_called_once_with()
        fake_pipeline.stop.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
