import sys

import pytest

from savemgr.core.platform import (
    LINUX,
    MACOS,
    SUPPORTED_PLATFORMS,
    WINDOWS,
    get_current_platform,
)


def test_get_current_platform_returns_known_value():
    platform = get_current_platform()
    assert platform in SUPPORTED_PLATFORMS


def test_platform_windows(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    assert get_current_platform() == WINDOWS


def test_platform_linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert get_current_platform() == LINUX


def test_platform_macos(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    assert get_current_platform() == MACOS


def test_platform_unsupported(monkeypatch):
    monkeypatch.setattr(sys, "platform", "freebsd")
    with pytest.raises(RuntimeError):
        get_current_platform()
