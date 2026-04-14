import sys

WINDOWS = "windows"
LINUX = "linux"
MACOS = "macos"

SUPPORTED_PLATFORMS = [WINDOWS, LINUX, MACOS]


def get_current_platform() -> str:
    """Return the current platform as a normalized string.

    Raises:
        RuntimeError: Raised if unsupported platform is found.

    Returns:
        str: Normalized platform string.
    """
    if sys.platform == "win32":
        return WINDOWS
    elif sys.platform == "darwin":
        return MACOS
    elif sys.platform.startswith("linux"):
        return LINUX
    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")
