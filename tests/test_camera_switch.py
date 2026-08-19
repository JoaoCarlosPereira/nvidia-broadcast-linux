"""Regression coverage for switching camera sources."""

from types import SimpleNamespace
import unittest
from unittest import mock

from nvbroadcast.app import NVBroadcastApp
from nvbroadcast.core.config import AppConfig
from nvbroadcast.core.device_supervisor import DeviceSupervisor
from nvbroadcast.core.state import EffectHealth
from nvbroadcast.ui.window import NVBroadcastWindow


class CameraSwitchTests(unittest.TestCase):
    @mock.patch("nvbroadcast.app.save_config")
    @mock.patch(
        "nvbroadcast.video.virtual_camera.select_camera_mode",
        return_value={
            "format": "mjpeg",
            "width": 1280,
            "height": 720,
            "fps": 60,
        },
    )
    def test_active_camera_switch_restarts_with_supported_mode(
        self, select_camera_mode, save_config
    ):
        app = NVBroadcastApp.__new__(NVBroadcastApp)
        app.config = AppConfig()
        app.config.video.camera_device = "/dev/video0"
        app.config.video.width = 1920
        app.config.video.height = 1080
        app.config.video.fps = 30
        app.config.video.output_format = "YUY2"
        app._streaming = True
        app._window = mock.Mock()
        app.start_pipeline = mock.Mock()

        app.switch_camera("/dev/video2")

        select_camera_mode.assert_called_once_with(
            "/dev/video2", 1920, 1080, 30
        )
        self.assertEqual(app.config.video.camera_device, "/dev/video2")
        self.assertEqual(app.config.video.width, 1280)
        self.assertEqual(app.config.video.height, 720)
        self.assertEqual(app.config.video.fps, 60)
        save_config.assert_called_once_with(app.config)
        app._window.sync_video_input_controls.assert_called_once_with(app.config)
        app.start_pipeline.assert_called_once_with("/dev/video2", "YUY2")

    def test_camera_selector_switches_application_camera(self):
        window = NVBroadcastWindow.__new__(NVBroadcastWindow)
        window._updating_ui = False
        window._app = SimpleNamespace(
            _restoring=False,
            switch_camera=mock.Mock(),
        )

        window._on_camera_changed(None, "/dev/video2")

        window._app.switch_camera.assert_called_once_with("/dev/video2")

    def test_camera_selector_ignores_programmatic_updates(self):
        window = NVBroadcastWindow.__new__(NVBroadcastWindow)
        window._updating_ui = True
        window._app = SimpleNamespace(
            _restoring=False,
            switch_camera=mock.Mock(),
        )

        window._on_camera_changed(None, "/dev/video2")

        window._app.switch_camera.assert_not_called()

    def test_capture_error_stops_pipeline_and_schedules_device_recovery(self):
        app = NVBroadcastApp.__new__(NVBroadcastApp)
        app.config = AppConfig()
        app.config.video.camera_device = "/dev/video2"
        app.config.video.camera_device_id = "/dev/v4l/by-id/test-camera"
        app.config.video.output_format = "YUY2"
        pipeline = mock.Mock()
        app._video_pipeline = pipeline
        app._window = mock.Mock()
        app.stop_pipeline = mock.Mock()
        app._schedule_camera_recovery = mock.Mock()

        result = app._on_capture_error(
            pipeline, "device vanished", "GstV4l2Src:v4l2src0"
        )

        self.assertFalse(result)
        app.stop_pipeline.assert_called_once_with(
            clear_pending_start=True, cancel_camera_recovery=False
        )
        app._schedule_camera_recovery.assert_called_once_with(
            "/dev/v4l/by-id/test-camera", "YUY2"
        )
        app._window.set_status.assert_called_with(
            "Camera disconnected - recovering..."
        )

    @mock.patch("nvbroadcast.video.virtual_camera.clear_camera_probe_cache")
    @mock.patch("nvbroadcast.video.virtual_camera.resolve_camera_device")
    @mock.patch(
        "nvbroadcast.video.virtual_camera.is_usable_camera_device",
        return_value=False,
    )
    def test_recovery_does_not_replace_missing_stable_camera(
        self, is_usable, resolve, clear_cache
    ):
        app = NVBroadcastApp.__new__(NVBroadcastApp)
        app.config = AppConfig()
        app.config.video.camera_device = "/dev/video2"
        app.config.video.camera_device_id = "/dev/v4l/by-id/test-camera"
        app._camera_recovery_attempts = 0
        app._camera_recovery_target = app.config.video.camera_device_id
        app._camera_recovery_format = "YUY2"
        app._camera_recovery_source_id = 42
        app._window = mock.Mock()

        result = app._camera_recovery_tick()

        self.assertTrue(result)
        resolve.assert_not_called()
        is_usable.assert_called_once_with(app.config.video.camera_device_id)
        self.assertEqual(app._camera_recovery_attempts, 1)

    @mock.patch("nvbroadcast.core.device_supervisor.save_config")
    @mock.patch(
        "nvbroadcast.core.device_supervisor.is_usable_camera_device",
        return_value=True,
    )
    @mock.patch(
        "nvbroadcast.core.device_supervisor.resolve_camera_device",
        return_value="/dev/video2",
    )
    @mock.patch(
        "nvbroadcast.core.device_supervisor.persistent_camera_device",
        return_value="/dev/v4l/by-id/usb-test",
    )
    def test_supervisor_persists_stable_id_and_rebuilds_without_quit(
        self, persistent_id, resolve, is_usable, save_config
    ):
        config = AppConfig()
        switch = mock.Mock()
        supervisor = DeviceSupervisor(config, on_camera_switch=switch)

        selected = supervisor.switch_camera("/dev/video2")

        self.assertEqual(selected, "/dev/video2")
        self.assertEqual(config.video.camera_device_id, "/dev/v4l/by-id/usb-test")
        switch.assert_called_once_with("/dev/video2")
        save_config.assert_called_once_with(config)
        self.assertEqual(supervisor.health("camera").health, EffectHealth.RECOVERING)


if __name__ == "__main__":
    unittest.main()
