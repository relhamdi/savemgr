from dataclasses import dataclass, field


@dataclass
class GameSource:
    """Backup paths for each platform."""

    windows: list[str] = field(default_factory=list)
    linux: list[str] = field(default_factory=list)
    macos: list[str] = field(default_factory=list)


@dataclass
class Game:
    slug: str
    name: str
    locked: bool = False
    sources: GameSource = field(default_factory=GameSource)

    def get_sources_for_platform(self, platform: str) -> list[str]:
        """List the paths for a given platform.

        Args:
            platform (str): Platform name.

        Returns:
            list[str]: List of paths found.
        """
        return getattr(self.sources, platform, [])
