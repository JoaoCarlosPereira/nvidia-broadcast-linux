import unittest
from unittest import mock

from nvbroadcast.core.config import AppConfig


class ShutdownTests(unittest.TestCase):
    def test_do_shutdown_cleans_up_all_subsystems(self):
        from nvbroadcast.app import NVBroadcastApp

        app = NVBroadcastApp.__new__(NVBroadcastApp)
        app.config = AppConfig()

        mock_video_pipe = mock.Mock()
        mock_audio_pipe = mock.Mock()
        mock_tray = mock.Mock()
        mock_speaker = mock.Mock()
        mock_transcriber = mock.Mock()
        mock_video_effects = mock.Mock()

        app._hotkey_manager = mock.Mock()
        app._vcam_monitor = mock.Mock()
        app._tray = mock_tray
        app._meeting_capture = mock.Mock()
        app._video_pipeline = mock_video_pipe
        app._pipeline_teardown = None
        app._audio_pipeline = mock_audio_pipe
        app._speaker_monitor = mock_speaker
        app._transcriber = mock_transcriber
        app._video_effects = mock_video_effects
        app._autoframe = mock.Mock()
        app._beautifier = mock.Mock()
        app._perf_monitor = mock.Mock()

        # Mock GLib timers
        app._vcam_consumer_check_source_id = 1
        app._auto_tune_source_id = 2
        app._idle_wake_source_id = 3
        app._restart_source_id = 4
        app._camera_recovery_source_id = 5
        app._camera_watchdog_source_id = 6

        with mock.patch("gi.repository.GLib.source_remove") as mock_source_remove, \
             mock.patch("nvbroadcast.core.config.save_config") as mock_save_config, \
             mock.patch("gi.repository.Adw.Application.do_shutdown"):
            app.do_shutdown()

        self.assertEqual(mock_source_remove.call_count, 6)
        mock_video_pipe.shutdown_sync.assert_called_once()
        mock_audio_pipe.stop.assert_called_once()
        mock_tray.shutdown.assert_called_once()
        mock_speaker.stop.assert_called_once()
        mock_transcriber.cleanup.assert_called_once()
        mock_video_effects.cleanup.assert_called_once()


if __name__ == "__main__":
    unittest.main()
