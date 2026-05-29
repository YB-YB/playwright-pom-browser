"""Tests for browser detection and priority logic."""

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from framework.utils._browser_detect import (
    BrowserInfo,
    DetectionResult,
    _extract_version,
    detect_system_browsers,
    get_playwright_channel,
)


class TestBrowserInfo(unittest.TestCase):
    def test_display_available(self):
        info = BrowserInfo(name="Google Chrome", channel="chrome", executable="/usr/bin/chrome", version="125.0.6422", available=True)
        self.assertIn("Google Chrome", info.display)
        self.assertIn("125.0.6422", info.display)

    def test_display_not_available(self):
        info = BrowserInfo(name="Firefox", channel="firefox", available=False)
        self.assertIn("not found", info.display)


class TestDetectionResult(unittest.TestCase):
    def test_has_any_true(self):
        browsers = [
            BrowserInfo(name="Chrome", channel="chrome", available=True),
            BrowserInfo(name="Edge", channel="msedge", available=False),
        ]
        result = DetectionResult(browsers=browsers)
        self.assertTrue(result.has_any)

    def test_has_any_false(self):
        browsers = [
            BrowserInfo(name="Chrome", channel="chrome", available=False),
        ]
        result = DetectionResult(browsers=browsers)
        self.assertFalse(result.has_any)

    def test_get_best_returns_first_available(self):
        browsers = [
            BrowserInfo(name="Chrome", channel="chrome", available=True, version="125.0"),
            BrowserInfo(name="Edge", channel="msedge", available=True, version="124.0"),
        ]
        result = DetectionResult(browsers=browsers)
        best = result.get_best()
        self.assertEqual(best.name, "Chrome")

    def test_get_best_returns_none_when_empty(self):
        result = DetectionResult(browsers=[])
        self.assertIsNone(result.get_best())


class TestExtractVersion(unittest.TestCase):
    def test_standard_version(self):
        self.assertEqual(_extract_version("Google Chrome 125.0.6422.76"), "125.0.6422.76")

    def test_firefox_version(self):
        self.assertEqual(_extract_version("Mozilla Firefox 126.0"), "126.0")

    def test_no_version(self):
        self.assertEqual(_extract_version("no version here"), "")

    def test_edge_version(self):
        self.assertEqual(_extract_version("Microsoft Edge 124.0.2478.80"), "124.0.2478.80")


class TestGetPlaywrightChannel(unittest.TestCase):
    def test_chrome_returns_channel(self):
        info = BrowserInfo(name="Chrome", channel="chrome", available=True)
        self.assertEqual(get_playwright_channel(info), "chrome")

    def test_edge_returns_channel(self):
        info = BrowserInfo(name="Edge", channel="msedge", available=True)
        self.assertEqual(get_playwright_channel(info), "msedge")

    def test_firefox_returns_none(self):
        info = BrowserInfo(name="Firefox", channel="firefox", available=True)
        self.assertIsNone(get_playwright_channel(info))


class TestDetectSystemBrowsers(unittest.TestCase):
    @mock.patch("framework.utils._browser_detect.is_windows", return_value=True)
    @mock.patch("framework.utils._browser_detect.is_macos", return_value=False)
    @mock.patch("framework.utils._browser_detect.is_linux", return_value=False)
    @mock.patch("framework.utils._browser_detect._detect_windows")
    def test_windows_detection_called(self, mock_detect, *_):
        mock_detect.return_value = [
            BrowserInfo(name="Chrome", channel="chrome", available=True, version="125.0"),
        ]
        result = detect_system_browsers()
        mock_detect.assert_called_once()
        self.assertTrue(result.has_any)

    @mock.patch("framework.utils._browser_detect.is_windows", return_value=False)
    @mock.patch("framework.utils._browser_detect.is_macos", return_value=True)
    @mock.patch("framework.utils._browser_detect.is_linux", return_value=False)
    @mock.patch("framework.utils._browser_detect._detect_macos")
    def test_macos_detection_called(self, mock_detect, *_):
        mock_detect.return_value = [
            BrowserInfo(name="Chrome", channel="chrome", available=True),
        ]
        result = detect_system_browsers()
        mock_detect.assert_called_once()
        self.assertTrue(result.has_any)

    @mock.patch("framework.utils._browser_detect.is_windows", return_value=False)
    @mock.patch("framework.utils._browser_detect.is_macos", return_value=False)
    @mock.patch("framework.utils._browser_detect.is_linux", return_value=True)
    @mock.patch("framework.utils._browser_detect._detect_linux")
    def test_linux_detection_called(self, mock_detect, *_):
        mock_detect.return_value = []
        result = detect_system_browsers()
        mock_detect.assert_called_once()
        self.assertFalse(result.has_any)


class TestBrowserPriority(unittest.TestCase):
    """验证浏览器优先级：Chrome > Edge > Firefox。"""

    def test_chrome_preferred_over_edge(self):
        browsers = [
            BrowserInfo(name="Google Chrome", channel="chrome", available=True),
            BrowserInfo(name="Microsoft Edge", channel="msedge", available=True),
            BrowserInfo(name="Firefox", channel="firefox", available=True),
        ]
        result = DetectionResult(browsers=browsers)
        best = result.get_best()
        self.assertEqual(best.channel, "chrome")

    def test_edge_preferred_when_no_chrome(self):
        browsers = [
            BrowserInfo(name="Google Chrome", channel="chrome", available=False),
            BrowserInfo(name="Microsoft Edge", channel="msedge", available=True),
            BrowserInfo(name="Firefox", channel="firefox", available=True),
        ]
        result = DetectionResult(browsers=browsers)
        best = result.get_best()
        self.assertEqual(best.channel, "msedge")

    def test_firefox_only_when_no_chromium_browsers(self):
        browsers = [
            BrowserInfo(name="Google Chrome", channel="chrome", available=False),
            BrowserInfo(name="Microsoft Edge", channel="msedge", available=False),
            BrowserInfo(name="Firefox", channel="firefox", available=True),
        ]
        result = DetectionResult(browsers=browsers)
        best = result.get_best()
        self.assertEqual(best.channel, "firefox")
        # Firefox 不支持 channel 模式
        self.assertIsNone(get_playwright_channel(best))


if __name__ == "__main__":
    unittest.main()
