"""One-shot migration from legacy storage dirs (`.mercator/`, `.codemap/`)
to `.codeatlas/`.

Consumer projects that adopted the tool pre-rename have a `.mercator/` (or
even older `.codemap/`) directory committed at the repo root. This module
implements:

    codeatlas migrate-from-mercator [--dry-run]
    codeatlas migrate              [--dry-run]   # alias

which renames the directory to `.codeatlas/`, rewrites any internal
references that hard-code the legacy path in generated JSON/MD files, and
updates a project-root `.claudeignore` so agents that are told to skip the
storage dir keep doing so.

Idempotent: if `.codeatlas/` already exists (and no legacy dir does), the
migration is a no-op. If both exist, we refuse to clobber and ask the user
to resolve — the tool never deletes user data.

The `.claudeignore` update is conservative: we only touch existing
entries like `.mercator/` (exact line) or `.mercator/*` — we don't add
a new entry if the project never ignored the legacy dir in the first
place.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import List, Optional, Tuple


# Order matters — first match wins when picking which legacy dir to migrate.
LEGACY_DIRS: Tuple[str, ...] = (".mercator", ".codemap")
NEW_DIR = ".codeatlas"


def _pick_legacy(project_root: Path) -> Optional[str]:
    for name in LEGACY_DIRS:
        if (project_root / name).is_dir():
            return name
    return None


def migrate(project_root: Path, *, dry_run: bool = False,
            legacy: Optional[str] = None) -> dict:
    """Rename a legacy storage dir to `.codeatlas/` and rewrite internal
    references.

    `legacy`, if given, forces a specific source dir (".mercator" or
    ".codemap"). Otherwise the first one found from `LEGACY_DIRS` is used.

    Returns a result dict with `status` in
    {"migrated", "already-migrated", "noop", "dry-run"} plus a `rewrites`
    list describing each file touched (or that would be touched).
    """
    new = project_root / NEW_DIR
    legacy_name = legacy if legacy is not None else _pick_legacy(project_root)

    if new.is_dir() and legacy_name is None:
        return {"status": "already-migrated", "from": None, "to": str(new), "rewrites": []}

    if legacy_name is None:
        return {"status": "noop", "from": None, "to": str(new), "rewrites": []}

    legacy_path = project_root / legacy_name

    if new.is_dir() and legacy_path.is_dir():
        raise RuntimeError(
            f"both {legacy_path} and {new} exist — refusing to clobber. "
            f"Move or delete one before re-running `codeatlas migrate-from-mercator`."
        )

    legacy_token = legacy_name + "/"   # e.g. ".mercator/"
    new_token = NEW_DIR + "/"          # ".codeatlas/"

    # Plan the text rewrites before touching anything on disk.
    rewrites: List[str] = []
    rewrite_plan: List[tuple] = []  # (path, old_text, new_text)
    for p in legacy_path.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in (".json", ".md"):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        new_text = text.replace(legacy_token, new_token)
        if new_text != text:
            rel = p.relative_to(legacy_path).as_posix()
            rewrites.append(rel)
            rewrite_plan.append((p, text, new_text))

    # `.claudeignore` rewrite (project-root-level only).
    ci_path = project_root / ".claudeignore"
    ci_rewrite: Optional[str] = None
    if ci_path.is_file():
        try:
            ci_text = ci_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            ci_text = None
        if ci_text is not None:
            new_ci = []
            changed = False
            for line in ci_text.splitlines():
                s = line.strip()
                if s in (legacy_name + "/", legacy_name,
                         legacy_name + "/*", legacy_name + "/**"):
                    new_ci.append(line.replace(legacy_name, NEW_DIR))
                    changed = True
                else:
                    new_ci.append(line)
            if changed:
                ci_rewrite = "\n".join(new_ci) + ("\n" if ci_text.endswith("\n") else "")
                rewrites.append(".claudeignore")

    if dry_run:
        return {
            "status": "dry-run",
            "from": str(legacy_path),
            "to": str(new),
            "rewrites": rewrites,
        }

    # Do it.
    # 1. Apply internal JSON/MD rewrites inside the legacy dir before the
    #    directory rename so individual-file mtimes stay correct.
    for p, _old, new_text in rewrite_plan:
        p.write_text(new_text, encoding="utf-8")

    # 2. Rename the directory. Use shutil.move for cross-filesystem safety.
    shutil.move(str(legacy_path), str(new))

    # 3. Rewrite .claudeignore (outside the renamed dir).
    if ci_rewrite is not None:
        ci_path.write_text(ci_rewrite, encoding="utf-8")

    return {
        "status": "migrated",
        "from": str(legacy_path),
        "to": str(new),
        "rewrites": rewrites,
    }
