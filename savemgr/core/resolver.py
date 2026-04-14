import os
from pathlib import Path


def resolve_path(raw_path: str) -> Path:
    """Resolve environment variables and ~ in a path.
    Ex:
        - "%APPDATA%\\saves" -> "C:\\Users\\john\\AppData\\Roaming\\saves"
        - "$HOME/.local/share/saves" -> "/home/john/.local/share/saves"

    Args:
        raw_path (str): Raw string path.

    Returns:
        Path: Resolved path.
    """
    expanded = os.path.expandvars(raw_path)
    resolved = Path(expanded).expanduser()
    return resolved
