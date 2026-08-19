import unittest
from unittest import mock
import subprocess
import sys
from pathlib import Path

from scripts.soak_harness import run_soak, get_rss_mb, get_gpu_memory_mb


class SoakHarnessTests(unittest.TestCase):
    def test_harness_short_duration(self):
        ret = run_soak(duration_seconds=0.2, sample_interval=0.05)
        self.assertEqual(ret, 0)

    def test_get_rss_mb_returns_positive(self):
        rss = get_rss_mb()
        self.assertGreater(rss, 0)

    @mock.patch("subprocess.run")
    def test_get_gpu_memory_mb_mock(self, mock_run):
        mock_run.return_value = mock.Mock(returncode=0, stdout="1024\n")
        gpu_mem = get_gpu_memory_mb()
        self.assertEqual(gpu_mem, 1024.0)


if __name__ == "__main__":
    unittest.main()
