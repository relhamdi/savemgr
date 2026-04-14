from dataclasses import dataclass


@dataclass
class Snapshot:
    game_slug: str
    timestamp: str
    platform: str
    compressed: bool
    autosave: bool = False

    @property
    def folder_name(self) -> str:
        suffix = f"{self.platform}_autosave" if self.autosave else self.platform
        return f"{self.timestamp}-{suffix}"
