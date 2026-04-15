# SaveMGR - Game save management system

A command-line utility to centralize, version, and transfer game save files across machines.

**SaveMGR** lets you back up save files from one or more directories per game into a single versioned folder, which can then be synchronized between computers using a tool like [Syncthing](https://syncthing.net/).

---

## How it works

SaveMGR keeps everything — the tool itself, its configuration, and all snapshots — inside a single root directory. This directory is the unit of synchronization: move or sync it, and everything moves with it.

```
savemgr/                        ← root directory (sync this with Syncthing)
├── games.toml                  ← game registry
└── saves/
    ├── celeste/
    │   ├── 20260114_183000-windows/
    │   │   ├── .meta.json
    │   │   ├── Saves/
    │   │   └── Backups/
    │   └── 20250114_190000-windows_autosave/
    └── witcher3/
        └── 20250115_091244-linux.zip
```

---

## Requirements

- [Python 3.11](https://www.python.org/) or higher
- [uv](https://github.com/astral-sh/uv) for dependency and environment management

---

## Installation

Clone or copy the repository, then install the package in editable mode:

```bash
git clone https://github.com/relhamdi/savemgr.git
cd savemgr
uv pip install -e .
```

The `-e` flag installs the project in editable mode: changes to the source files are reflected immediately without reinstalling.

Verify the installation:

```bash
uv run savemgr --help
```

---

## Syncing between machines

SaveMGR does not handle synchronization itself. The intended workflow is to use an external tool such as [Syncthing](https://syncthing.net/) to keep the root `savemgr/` directory in sync between your machines.

**Recommended setup:**

1. Install SaveMGR on your machine
2. Point Syncthing to the root `savemgr/` directory and sync it accross your machines
3. Syncthing will keep `games.toml` and all snapshots in sync automatically

> **Note:** `games.toml` stores paths per platform (`windows`, `linux`, `macos`). Each machine will resolve only the paths relevant to its own OS, so a single config file works correctly across different operating systems.

---

## Configuration

Games are registered in `games.toml` at the root of the savemgr directory. You can edit this file manually or use `savemgr game add`.

### Path variables

Paths support environment variable expansion and `~`:

| Syntax           | Platform      | Example                         |
| ---------------- | ------------- | ------------------------------- |
| `%USERPROFILE%`  | Windows       | `C:\Users\john`                 |
| `%APPDATA%`      | Windows       | `C:\Users\john\AppData\Roaming` |
| `%LOCALAPPDATA%` | Windows       | `C:\Users\john\AppData\Local`   |
| `$HOME`          | Linux / macOS | `/home/john`                    |
| `~`              | All           | Expands to home directory       |

### Example `games.toml`

```toml
[games.celeste]
name = "Celeste"

[games.celeste.sources]
windows = [
  "%LOCALAPPDATA%\\Celeste\\Saves",
  "%LOCALAPPDATA%\\Celeste\\Backups"
]
linux = [
  "$HOME/.local/share/Celeste/Saves"
]

[games.witcher3]
name = "The Witcher 3"

[games.witcher3.sources]
windows = [
  "%USERPROFILE%\\Documents\\The Witcher 3\\gamesaves"
]
linux = [
  "$HOME/.local/share/witcher3/saves"
]
macos = [
  "$HOME/Library/Application Support/witcher3/saves"
]
```

---

## Commands

### `game` — manage registered games

```bash
# Register a new game (interactive)
savemgr game add <slug>

# List all registered games
savemgr game list

# Remove a game from the registry (snapshots are not deleted)
savemgr game remove <slug>
savemgr game remove <slug> --force

# Lock a game (prevents backup and restore)
savemgr game lock <slug>

# Unlock a game
savemgr game unlock <slug>
```

### `backup` — create a snapshot

```bash
# Back up a game's save files
savemgr backup <slug>
savemgr backup <slug> --force      # bypass lock

# Preview what would be copied without doing anything
savemgr backup <slug> --dry-run

# Back up and compress the snapshot into a zip file
savemgr backup <slug> --compress

# Back up and add a comment about the snapshot
savemgr backup <slug> --comment "before final boss"

```

Snapshots are named using the format `YYYYMMDD_HHMMSS-{platform}`, for example:

```
20260114_183000-windows
20260114_183000-linux
```

### `restore` — restore a snapshot

```bash
# Restore the most recent snapshot
savemgr restore <slug>
savemgr restore <slug> --force     # bypass lock

# Restore a specific snapshot by timestamp
savemgr restore <slug> <timestamp>

# Preview what would be restored without doing anything
savemgr restore <slug> --dry-run
savemgr restore <slug> <timestamp> --dry-run
```

**Restore behavior:**

- The destination directory is **wiped before copying**, so the restored state is identical to what was saved — no leftover files from a later session survive.
- Before wiping, SaveMGR automatically creates an **autosave** snapshot of the current state, so nothing is lost.
- If a destination path does not exist (e.g. game not yet installed), no autosave is created for that path. A warning is displayed and a confirmation is required before proceeding.

> Note: Autosave snapshots are named `YYYYMMDD_HHMMSS-{platform}_autosave` and appear in `save list` alongside manual snapshots.

### `import` — import an external save

```bash
# Import a save file or directory into the versioning system
savemgr import <slug> <path>
savemgr import <slug> <path> --compress
savemgr import <slug> <path> --comment "from nexusmods"
```


### `save` — manage snapshots

```bash
# List all snapshots for a game
savemgr save list <slug>

# Delete a specific snapshot
savemgr save delete <slug> <timestamp>
savemgr save delete <slug> <timestamp> --force
```

---

## Snapshot format

Each snapshot is either a folder or a `.zip` file (when created with `--compress`).

A snapshot folder contains:
- `.meta.json` — metadata written at backup time
- One subfolder per configured source path, named after the last segment of the source path

### `.meta.json` example

```json
{
  "game_slug": "celeste",
  "timestamp": "20260114_183000",
  "platform": "windows",
  "compressed": false,
  "autosave": false
}
```

---

## Typical workflow

### First machine

```bash
# Register a game
savemgr game add celeste

# Back up its saves
savemgr backup celeste

# Check the result
savemgr save list celeste
```

### Second machine (after Syncthing sync)

```bash
# The game is already in games.toml — no need to re-register
savemgr save list celeste

# Restore the latest snapshot
savemgr restore celeste
```

---

## Dry-run example

```
$ savemgr backup celeste --dry-run

[DRY-RUN] Backup de "Celeste" (windows)
  Source(s)  : %LOCALAPPDATA%\Celeste\Saves, %LOCALAPPDATA%\Celeste\Backups
  Dest       : saves/celeste/20260114_183000-windows

[DRY-RUN] Files that would be copied:
  + Saves/    (12 files, 1.2 MB)
  + Backups/  (4 files, 0.4 MB)

[DRY-RUN] No action taken.
```

---

## Running tests

```bash
uv run pytest
```
