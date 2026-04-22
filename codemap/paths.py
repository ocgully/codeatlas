"""Project-root and `.codemap/` directory resolution.

The CLI walks upward from the current working directory looking for either an
existing `.codemap/` (post-init) or a recognised stack manifest (pre-init).
Whichever it finds first defines the project root.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional


# Files that mark the root of a stack-specific project.
STACK_MARKERS = (
    "Cargo.toml",              # Rust
    "package.json",            # TS/JS
    "pyproject.toml",          # Python
    "setup.py",                # Python (legacy)
    "go.mod",                  # Go
    "go.work",                 # Go workspace
    "pubspec.yaml",            # Dart/Flutter
)

# Directory markers (Unity has no single file; detect via multiple dirs).
UNITY_DIR_MARKERS = ("Assets", "ProjectSettings", "Packages")


def find_project_root(start: Optional[Path] = None) -> Path:
    """Walk upward from `start` (or cwd) to find the project root.

    Returns the first ancestor that has either `.codemap/` or any stack
    marker. Falls back to `start` itself if nothing matches (so `init` can
    still work on a bare directory with only an unusual marker).
    """
    start = (start or Path.cwd()).resolve()
    for candidate in (start, *start.parents):
        if (candidate / ".codemap").is_dir():
            return candidate
        if any((candidate / m).exists() for m in STACK_MARKERS):
            return candidate
        # Unity heuristic: all three markers present.
        if all((candidate / m).exists() for m in UNITY_DIR_MARKERS):
            return candidate
    return start


def codemap_dir(project_root: Path) -> Path:
    return project_root / ".codemap"


def ensure_codemap_dir(project_root: Path) -> Path:
    d = codemap_dir(project_root)
    d.mkdir(parents=True, exist_ok=True)
    (d / "contracts").mkdir(exist_ok=True)
    (d / "symbols").mkdir(exist_ok=True)
    (d / "assets").mkdir(exist_ok=True)
    return d
