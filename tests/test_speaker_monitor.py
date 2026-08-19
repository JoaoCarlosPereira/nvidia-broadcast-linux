import unittest
from unittest import mock

from nvbroadcast.audio.monitor import SpeakerMonitor


class SpeakerMonitorRoutingTests(unittest.TestCase):
    @mock.patch("nvbroadcast.audio.monitor.resolve_speaker_sink", return_value="alsa_output.demo")
    @mock.patch("nvbroadcast.audio.monitor.resolve_speaker_monitor_name",
                return_value="alsa_output.demo.monitor")
    @mock.patch("nvbroadcast.audio.monitor.Gst.ElementFactory.find")
    def test_prefers_pulse_backends_when_available(self, element_find, _monitor_name, _sink):
        element_find.side_effect = lambda name: object() if name in {"pulsesrc", "pulsesink"} else None

        monitor = SpeakerMonitor()
        monitor.configure(speaker_device="alsa_output.demo")

        self.assertEqual(
            monitor._select_capture_backend(),
            ("pulsesrc", "alsa_output.demo.monitor"),
        )
        self.assertEqual(
            monitor._select_output_backend(),
            ("pulsesink", "alsa_output.demo"),
        )

    @mock.patch("nvbroadcast.audio.monitor.resolve_speaker_sink", return_value="alsa_output.demo")
    @mock.patch("nvbroadcast.audio.monitor.resolve_speaker_monitor", return_value="228")
    @mock.patch("nvbroadcast.audio.monitor.Gst.ElementFactory.find")
    def test_falls_back_to_pipewire_when_pulse_missing(self, element_find, _monitor_id, _sink):
        element_find.side_effect = lambda name: object() if name in {"pipewiresrc", "pipewiresink"} else None

        monitor = SpeakerMonitor()
        monitor.configure(speaker_device="alsa_output.demo")

        self.assertEqual(
            monitor._select_capture_backend(),
            ("pipewiresrc", "228"),
        )
        self.assertEqual(
            monitor._select_output_backend(),
            ("pipewiresink", "alsa_output.demo"),
        )

    @mock.patch("nvbroadcast.audio.monitor.resolve_speaker_sink", return_value="alsa_output.same")
    @mock.patch("nvbroadcast.audio.monitor.resolve_speaker_monitor_name", return_value="alsa_output.same")
    @mock.patch("nvbroadcast.audio.monitor.Gst.ElementFactory.find")
    def test_refuses_loop_when_capture_equals_output_target(self, element_find, _monitor_name, _sink):
        element_find.side_effect = lambda name: object() if name in {"pulsesrc", "pulsesink"} else None
        monitor = SpeakerMonitor()
        monitor.configure(speaker_device="alsa_output.same")
        with self.assertRaises(ValueError):
            monitor.build()

    def test_teardown_does_not_call_remove_signal_watch(self):
        monitor = SpeakerMonitor()
        mock_bus = mock.Mock()
        monitor._pipeline = mock.Mock()
        monitor._bus = mock_bus
        monitor._teardown_pipeline()
        mock_bus.remove_signal_watch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
