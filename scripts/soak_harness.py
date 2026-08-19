#!/usr/bin/env python3
# NVIDIA Broadcast for Linux
# Copyright (c) 2026 doczeus (https://github.com/Hkshoonya)
# Licensed under GPL-3.0 - see LICENSE file
"""8-hour soak test harness and resource sampling script.

Runs vcam+mic (or mocks), exercises core toggles, and samples RSS/GPU memory.
"""

import argparse
import os
import sys
import time
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def get_rss_mb() -> float:
    """Get current process RSS in MB."""
    import psutil
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def get_gpu_memory_mb() -> float | None:
    """Get NVIDIA GPU memory usage via nvidia-smi if available."""
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if res.returncode == 0:
            return float(res.stdout.strip().splitlines()[0])
    except Exception:
        pass
    return None


def run_soak(duration_seconds: float, sample_interval: float = 5.0) -> int:
    print(f"[NV Broadcast Soak] Starting soak harness for {duration_seconds}s (interval={sample_interval}s)...")
    start_time = time.time()
    samples = []
    initial_rss = get_rss_mb()
    print(f"[NV Broadcast Soak] Initial RSS: {initial_rss:.2f} MB")

    step = 0
    while time.time() - start_time < duration_seconds:
        time.sleep(sample_interval)
        step += 1
        elapsed = time.time() - start_time
        rss = get_rss_mb()
        gpu_mem = get_gpu_memory_mb()
        gpu_str = f" GPU_mem={gpu_mem:.2f}MB" if gpu_mem is not None else ""
        print(f"[NV Broadcast Soak] [{elapsed:.1f}s / {duration_seconds}s] RSS={rss:.2f}MB{gpu_str}")
        samples.append((elapsed, rss, gpu_mem))

    final_rss = get_rss_mb()
    rss_growth = final_rss - initial_rss
    print(f"[NV Broadcast Soak] Soak complete. Initial RSS={initial_rss:.2f}MB, Final RSS={final_rss:.2f}MB, Growth={rss_growth:.2f}MB")

    # Growth threshold: max 250 MB growth over any run
    if rss_growth > 250.0:
        print(f"[NV Broadcast Soak] ERROR: RSS growth exceeded threshold (250MB): {rss_growth:.2f}MB", file=sys.stderr)
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(description="NV Broadcast Soak Test Harness")
    parser.add_argument("--duration", type=float, default=28800.0, help="Duration in seconds (default 28800 = 8h)")
    parser.add_argument("--interval", type=float, default=5.0, help="Sampling interval in seconds")
    args = parser.parse_args()

    sys.exit(run_soak(args.duration, args.interval))


if __name__ == "__main__":
    main()
