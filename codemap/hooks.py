"""Git hook installer.

Writes a `post-commit` hook into the project's `.git/hooks/` that calls
`codemap refresh --files <changed>` so the map stays current automatically.

The hook is idempotent: installing it twice is a no-op. Uninstalling
removes only the block the installer added — a user's custom hook logic
(if any) is left alone.
"""
from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Optional

MARKER_BEGIN = "# --- codemap hook (managed; do not edit this block) ---"
MARKER_END = "# --- /codemap hook ---"

HOOK_BODY = """
# Regenerate affected slices of .codemap/ after each commit.
# Skip during rebase / merge / cherry-pick to avoid noisy refreshes.
if [ -z "$GIT_REFLOG_ACTION" ] || echo "$GIT_REFLOG_ACTION" | grep -qvE '^(rebase|merge|cherry-pick)'; then
  CHANGED=$(git diff-tree --no-commit-id --name-only -r HEAD 2>/dev/null)
  if [ -n "$CHANGED" ]; then
    # Use `codemap` if installed, else the launcher shipped with AgentFactory.
    if command -v codemap >/dev/null 2>&1; then
      codemap refresh --files $CHANGED --quiet || true
    elif [ -n "$CODEMAP_LAUNCHER" ] && [ -f "$CODEMAP_LAUNCHER" ]; then
      python "$CODEMAP_LAUNCHER" refresh --files $CHANGED --quiet || true
    fi
  fi
fi
"""


def _git_dir(project_root: Path) -> Optional[Path]:
    candidate = project_root / ".git"
    if candidate.is_dir():
        return candidate
    # git worktrees: .git is a file pointing to the worktree's git dir
    if candidate.is_file():
        content = candidate.read_text(encoding="utf-8").strip()
        if content.startswith("gitdir:"):
            return Path(content.split(":", 1)[1].strip()).resolve()
    return None


def _hook_path(project_root: Path) -> Path:
    gd = _git_dir(project_root)
    if gd is None:
        raise RuntimeError("not inside a git working tree (no .git directory found)")
    hooks_dir = gd / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    return hooks_dir / "post-commit"


def install(project_root: Path, launcher_path: Optional[Path] = None) -> Path:
    hp = _hook_path(project_root)
    existing = hp.read_text(encoding="utf-8") if hp.is_file() else ""

    if MARKER_BEGIN in existing:
        # Already installed — rewrite the block (idempotent).
        start = existing.index(MARKER_BEGIN)
        end = existing.index(MARKER_END, start) + len(MARKER_END)
        existing = existing[:start] + existing[end:]

    header = existing if existing.startswith("#!") else "#!/usr/bin/env bash\n"
    if existing and not existing.startswith("#!"):
        existing = header + existing
    elif not existing:
        existing = header

    launcher_env = ""
    if launcher_path is not None:
        launcher_env = f'export CODEMAP_LAUNCHER="{launcher_path.as_posix()}"\n'

    block = f"\n{MARKER_BEGIN}\n{launcher_env}{HOOK_BODY}\n{MARKER_END}\n"
    hp.write_text(existing + block, encoding="utf-8")

    # Mark executable on POSIX; no-op on Windows.
    try:
        mode = hp.stat().st_mode
        hp.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except (PermissionError, OSError):
        pass

    return hp


def uninstall(project_root: Path) -> bool:
    hp = _hook_path(project_root)
    if not hp.is_file():
        return False
    text = hp.read_text(encoding="utf-8")
    if MARKER_BEGIN not in text:
        return False
    start = text.index(MARKER_BEGIN)
    end = text.index(MARKER_END, start) + len(MARKER_END)
    new = text[:start].rstrip() + "\n" + text[end:].lstrip()
    if new.strip() in ("", "#!/usr/bin/env bash"):
        hp.unlink()
    else:
        hp.write_text(new, encoding="utf-8")
    return True
