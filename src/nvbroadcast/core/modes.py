# NVIDIA Broadcast for Linux
# Copyright (c) 2026 doczeus (https://github.com/Hkshoonya)
# Licensed under GPL-3.0 - see LICENSE file
"""Camera mode mappings and status messages."""

# (profile, compositing, use_tensorrt, use_fused_kernel, use_nvdec)
MODE_MAP = {
    "doczeus":      ("max_quality", "cupy", False, True,  False),
    "cuda_max":     ("max_quality", "cupy", False, False, False),
    "cuda_balanced": ("balanced",   "cupy", False, False, False),
    "zeus":         ("balanced",    "cupy", True,  False, False),
    "killer":       ("performance", "cupy", True,  True,  True),
    "cuda_perf":    ("performance", "cupy", False, True,  False),
    "cpu_quality":  ("max_quality", "cpu",  False, False, False),
    "cpu_light":    ("performance", "cpu",  False, False, False),
    "cpu_low":      ("potato",      "cpu",  False, False, False),
}

def mode_status_message(mode_key: str) -> str:
    messages = {
        "auto": "Auto: adapt to the current device and step down when live FPS stays low",
        "doczeus": "DocZeus: best GPU quality for background replacement",
        "cuda_max": "CUDA High Quality: strong quality without fused compositing",
        "cuda_balanced": "CUDA Balanced: good quality with lighter GPU load",
        "zeus": "Zeus: fast GPU mode with TensorRT and edge refine",
        "killer": "Killer: fastest GPU mode, softer edges under motion",
        "cuda_perf": "CUDA Fast: fused compositor with fresher 480p replace matting",
        "cpu_quality": "CPU High Quality: most compatible, highest CPU cost",
        "cpu_light": "CPU Fast: reduced CPU cost with lower quality",
        "cpu_low": "CPU Low: minimal CPU cost for basic background removal",
    }
    return messages.get(mode_key, "Custom mode selected")
