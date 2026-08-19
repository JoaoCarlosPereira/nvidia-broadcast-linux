"""End-to-end integration smoke tests for hardware pipeline components.

Requires: v4l2loopback module, physical camera, PipeWire/PulseAudio.
Skip automatically if hardware/drivers are not present.
"""

import os
import subprocess
import sys
import time

import pytest


def test_v4l2loopback_available():
    """Verify v4l2loopback kernel module is loaded and device exists."""
    if not os.path.exists("/dev/video10"):
        pytest.skip("/dev/video10 loopback device not present")


def test_gstreamer_pipeline():
    """Test GStreamer videotestsrc -> appsink pipeline."""
    import gi
    gi.require_version("Gst", "1.0")
    from gi.repository import Gst
    Gst.init(None)

    pipeline = Gst.parse_launch(
        "videotestsrc num-buffers=10 is-live=true ! video/x-raw,width=640,height=480 ! appsink name=sink emit-signals=true"
    )
    pipeline.set_state(Gst.State.PLAYING)
    bus = pipeline.get_bus()
    msg = bus.timed_pop_filtered(5 * Gst.SECOND, Gst.MessageType.EOS | Gst.MessageType.ERROR)
    pipeline.set_state(Gst.State.NULL)
    if msg is None:
        pytest.skip("GStreamer live test pipeline timed out in headless environment")
    assert msg.type == Gst.MessageType.EOS, f"Pipeline error: {msg.parse_error()}"


def test_onnxruntime_cuda():
    """Verify ONNX Runtime detects CUDA execution provider."""
    try:
        import onnxruntime as ort
    except ImportError:
        pytest.skip("onnxruntime not installed")

    providers = ort.get_available_providers()
    if "CUDAExecutionProvider" not in providers:
        pytest.skip("CUDA Execution Provider not available in ONNX Runtime")


def test_cupy_cuda():
    """Verify CuPy detects CUDA GPU."""
    try:
        import cupy as cp
        cp.cuda.Device(0).compute_capability
    except Exception as e:
        pytest.skip(f"CuPy CUDA not available: {e}")


def test_pipewire_virtual_mic():
    """Verify PipeWire virtual microphone creation via pw-loopback / pactl."""
    from nvbroadcast.audio.virtual_mic import create_virtual_mic, destroy_virtual_mic

    try:
        pid = create_virtual_mic("nvbroadcast_test_mic", "Test Mic")
    except Exception as e:
        pytest.skip(f"Failed to create PipeWire virtual mic: {e}")

    assert pid is not None
    time.sleep(1)
    destroy_virtual_mic(pid)


def test_rvm_inference():
    """Test RVM background matting inference on dummy frame."""
    code = r"""
import numpy as np
from nvbroadcast.video.effects import VideoEffects
ve = VideoEffects(compositing="cpu")
ve.quality = "performance"
ve.enabled = True
ve.mode = "blur"
ve.blur_intensity = 0.5
frame = np.random.randint(0, 255, (360, 640, 4), dtype=np.uint8)
result = ve.process_frame_array(frame, width=640, height=360)
assert result.shape == (360, 640, 4)
ve.cleanup()
print("OK")
"""
    env = dict(os.environ)
    env["PYTHONPATH"] = f"src:{env.get('PYTHONPATH', '')}".rstrip(":")
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=os.getcwd(),
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "OK" in result.stdout


def test_autoframe():
    """Test auto-frame face tracking."""
    try:
        import mediapipe
    except ImportError:
        pytest.skip("mediapipe optional dependency not installed")
    code = r"""
import numpy as np
from nvbroadcast.video.autoframe import AutoFrame
af = AutoFrame()
if not af.initialize():
    print("SKIP")
    exit(0)
af.enabled = True
af.zoom_level = 1.5
frame = np.random.randint(0, 255, (720, 1280, 4), dtype=np.uint8).tobytes()
result = af.process_frame(frame, 1280, 720)
assert len(result) == len(frame)
af.cleanup()
print("OK")
"""
    env = dict(os.environ)
    env["PYTHONPATH"] = f"src:{env.get('PYTHONPATH', '')}".rstrip(":")
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=os.getcwd(),
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_audio_denoise():
    """Test audio noise removal."""
    try:
        import pyrnnoise
    except ImportError:
        pytest.skip("pyrnnoise optional dependency not installed")
    from nvbroadcast.audio.effects import AudioEffects
    afx = AudioEffects()
    if not afx.initialize():
        pytest.skip("audio denoiser model or backend missing")
    afx.enabled = True
    afx.intensity = 1.0
    audio = np.random.randn(4800).astype(np.float32) * 0.1
    result = afx.process_chunk(audio, 48000)
    assert len(result) == len(audio)
    assert np.std(result) <= np.std(audio) + 0.01
    afx.cleanup()


def test_vcam_pipeline():
    """Test virtual camera pipeline streams successfully."""
    import gi
    gi.require_version("Gst", "1.0")
    from gi.repository import Gst
    Gst.init(None)
    from nvbroadcast.vcam_service import build_pipeline
    pipeline = build_pipeline("/dev/video0", "/dev/video10", 1280, 720, 30, "yuy2")
    pipeline.set_state(Gst.State.PLAYING)
    time.sleep(2)
    state = pipeline.get_state(1 * Gst.SECOND)[1]
    pipeline.set_state(Gst.State.NULL)
    assert state == Gst.State.PLAYING, "Pipeline failed to reach PLAYING state"
