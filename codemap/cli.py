"""codemap CLI — one argparse entry point, many subcommands.

Exit codes (contract for scripts + CI):
    0  success
    1  usage error
    2  missing prerequisite (cargo, python version, etc.)
    3  unsupported / unrecognised stack
    4  internal failure (parser crash, malformed input)

All `query` subcommands emit JSON by default. Pass `--format md` for the
human-friendly rendered view. Agents should prefer JSON — it's smaller
and typed. Humans reading `.codemap/*.md` files directly is still fine,
but those files are derived, not authoritative.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from codemap import __version__, SCHEMA_VERSION, paths, hooks, meta
from codemap import boundaries as boundaries_mod
from codemap.detect import detect
from codemap import query as query_mod
from codemap import refresh as refresh_mod
from codemap.render import graph_md, boundaries_md


def _project_root(args) -> Path:
    if getattr(args, "project_root", None):
        return Path(args.project_root).resolve()
    return paths.find_project_root()


def _print_json(data) -> None:
    sys.stdout.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# init / refresh
# ---------------------------------------------------------------------------

def cmd_init(args) -> int:
    root = _project_root(args)
    try:
        result = refresh_mod.refresh(root)
    except RuntimeError as exc:
        print(f"codemap: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"codemap: {exc}", file=sys.stderr)
        return 3
    if not args.quiet:
        print(
            f"Initialized .codemap/ — stack={result['stack']}, "
            f"{result['systems_count']} systems, {result['contracts_written']} contract files."
        )
        print(f"  {paths.codemap_dir(root)}")
    return 0


def cmd_refresh(args) -> int:
    root = _project_root(args)
    affected = None
    if args.files:
        affected = refresh_mod.files_to_affected_systems(root, args.files)
        if not affected and not args.full_on_empty:
            if not args.quiet:
                print("codemap: no affected systems for the given files; skipping refresh.")
            return 0
    try:
        result = refresh_mod.refresh(root, affected=affected)
    except RuntimeError as exc:
        print(f"codemap: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"codemap: {exc}", file=sys.stderr)
        return 3
    if not args.quiet:
        scope = f"incremental: {sorted(affected)}" if affected else "full"
        print(
            f"Refreshed .codemap/ ({scope}) — stack={result['stack']}, "
            f"{result['systems_count']} systems, {result['contracts_written']} contract files written."
        )
    return 0


# ---------------------------------------------------------------------------
# query subcommands
# ---------------------------------------------------------------------------

def cmd_query(args) -> int:
    root = _project_root(args)
    try:
        if args.subject == "systems":
            data = query_mod.systems(root)
        elif args.subject == "deps":
            if not args.name:
                print("codemap: `query deps` requires <name>", file=sys.stderr)
                return 1
            data = query_mod.deps(root, args.name)
        elif args.subject == "contract":
            if not args.name:
                print("codemap: `query contract` requires <name>", file=sys.stderr)
                return 1
            data = query_mod.contract(root, args.name)
        elif args.subject == "symbol":
            if not args.name:
                print("codemap: `query symbol` requires <name>", file=sys.stderr)
                return 1
            kinds = "any"
            if args.kind != "any":
                kinds = {args.kind}
            if args.kinds:
                kinds = {k.strip() for k in args.kinds.split(",") if k.strip()}
            data = query_mod.symbol(root, args.name, kinds)
        elif args.subject == "touches":
            if not args.name:
                print("codemap: `query touches` requires <path>", file=sys.stderr)
                return 1
            data = query_mod.touches(root, args.name)
        elif args.subject == "system":
            if not args.name:
                print("codemap: `query system` requires <name>", file=sys.stderr)
                return 1
            data = query_mod.system(root, args.name)
        elif args.subject == "boundaries":
            data = query_mod.boundaries(root)
        elif args.subject == "violations":
            data = query_mod.violations(root)
        else:
            print(f"codemap: unknown query subject '{args.subject}'", file=sys.stderr)
            return 1
    except FileNotFoundError as exc:
        print(f"codemap: {exc}", file=sys.stderr)
        return 4

    _print_json(data)
    return 0


# ---------------------------------------------------------------------------
# hooks
# ---------------------------------------------------------------------------

def cmd_hooks(args) -> int:
    root = _project_root(args)
    if args.action == "install":
        launcher = Path(__file__).resolve().parents[2] / "codemap.py"
        try:
            hp = hooks.install(root, launcher_path=launcher if launcher.is_file() else None)
        except RuntimeError as exc:
            print(f"codemap: {exc}", file=sys.stderr)
            return 2
        if not args.quiet:
            print(f"Installed post-commit hook at {hp}")
        return 0
    if args.action == "uninstall":
        ok = hooks.uninstall(root)
        if not args.quiet:
            print("Uninstalled." if ok else "No codemap hook found.")
        return 0
    print(f"codemap: unknown hooks action '{args.action}'", file=sys.stderr)
    return 1


# ---------------------------------------------------------------------------
# info / version
# ---------------------------------------------------------------------------

def cmd_check(args) -> int:
    """CI-friendly: exit 0 clean, exit 1 on any error-severity violation."""
    root = _project_root(args)
    try:
        import json as _json
        sys_doc = _json.loads((paths.codemap_dir(root) / "systems.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        print("codemap: no .codemap/systems.json — run `codemap init` first", file=sys.stderr)
        return 4
    try:
        bnd_doc = boundaries_mod.load(root)
    except ValueError as exc:
        print(f"codemap: boundaries file error — {exc}", file=sys.stderr)
        return 4
    if not bnd_doc:
        if not args.quiet:
            print("codemap: no .codemap/boundaries.json — nothing to check. PASS by default.")
        return 0
    vs = boundaries_mod.evaluate(sys_doc, bnd_doc)
    errors = [v for v in vs if v["severity"] == "error"]
    warnings = [v for v in vs if v["severity"] == "warning"]
    infos = [v for v in vs if v["severity"] == "info"]
    if args.format == "json":
        _print_json({
            "check": "boundaries",
            "error_count": len(errors),
            "warning_count": len(warnings),
            "info_count": len(infos),
            "violations": vs,
            "pass": len(errors) == 0,
        })
    else:
        if not vs:
            if not args.quiet:
                print("codemap check: PASS — no boundary violations.")
            return 0
        print(f"codemap check: {len(errors)} error, {len(warnings)} warning, {len(infos)} info")
        for v in vs:
            arrow = " -> ".join(v["path"])
            print(f"  [{v['severity'].upper():7}] {v['rule_name']}")
            print(f"            {arrow}")
            if v.get("rationale"):
                print(f"            ({v['rationale']})")
    return 1 if errors else 0


def cmd_render(args) -> int:
    """Regenerate visual views (graph.md + boundaries.md) — deterministic."""
    root = _project_root(args)
    cmdir = paths.codemap_dir(root)
    systems_path = cmdir / "systems.json"
    if not systems_path.is_file():
        print("codemap: no .codemap/systems.json — run `codemap init` first", file=sys.stderr)
        return 4
    import json as _json
    sys_doc = _json.loads(systems_path.read_text(encoding="utf-8"))
    try:
        bnd_doc = boundaries_mod.load(root)
    except ValueError as exc:
        print(f"codemap: boundaries file error — {exc}", file=sys.stderr)
        return 4

    (cmdir / "graph.md").write_text(graph_md.render(sys_doc, bnd_doc), encoding="utf-8")
    (cmdir / "boundaries.md").write_text(boundaries_md.render(sys_doc, bnd_doc), encoding="utf-8")
    if not args.quiet:
        print(f"Rendered {cmdir / 'graph.md'}")
        print(f"Rendered {cmdir / 'boundaries.md'}")
        print("Open in any markdown viewer (GitHub, VS Code, Obsidian) — mermaid blocks render natively.")
    return 0


def cmd_boundaries(args) -> int:
    """Scaffold or validate .codemap/boundaries.json."""
    root = _project_root(args)
    cmdir = paths.codemap_dir(root)
    path = cmdir / "boundaries.json"

    if args.action == "init":
        if path.is_file() and not args.force:
            print(f"codemap: {path} already exists. Use --force to overwrite.", file=sys.stderr)
            return 1
        cmdir.mkdir(parents=True, exist_ok=True)
        path.write_text(boundaries_mod.SCAFFOLD_JSON, encoding="utf-8")
        if not args.quiet:
            print(f"Scaffolded {path}")
            print("Edit it to declare forbidden edges. Rerun `codemap check` to see violations.")
        return 0

    if args.action == "validate":
        try:
            doc = boundaries_mod.load(root)
        except ValueError as exc:
            print(f"codemap: {exc}", file=sys.stderr)
            return 4
        if not doc:
            print("codemap: no .codemap/boundaries.json to validate.")
            return 0
        sys_doc = json.loads((cmdir / "systems.json").read_text(encoding="utf-8"))
        rules = boundaries_mod.summarise_rules(sys_doc, doc)
        # Flag rules whose selectors resolve to empty sets (probably typo'd).
        empty = [r for r in rules if not r["resolved_from"] or not r["resolved_not_to"]]
        if empty:
            print(f"codemap: {len(empty)} rule(s) resolve to empty system set — check selectors:", file=sys.stderr)
            for r in empty:
                print(f"  - {r['name']}: from={r['from_selector']!r} → {r['resolved_from']}, "
                      f"not_to={r['not_to_selector']!r} → {r['resolved_not_to']}", file=sys.stderr)
            return 4
        if not args.quiet:
            print(f"codemap: {len(rules)} rule(s) OK")
        return 0
    print(f"codemap: unknown boundaries action '{args.action}'", file=sys.stderr)
    return 1


def cmd_info(args) -> int:
    root = _project_root(args)
    stack = detect(root)
    m = meta.read(paths.codemap_dir(root))
    _print_json({
        "codemap_version": __version__,
        "schema_version": SCHEMA_VERSION,
        "project_root": str(root),
        "detected_stack": stack,
        "initialized": bool(m),
        "meta": m,
    })
    return 0


# ---------------------------------------------------------------------------
# parser
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="codemap",
        description="Layered, AI-friendly codemap — agent-consumable via JSON queries.",
    )
    p.add_argument("--version", action="version", version=f"codemap {__version__} (schema {SCHEMA_VERSION})")
    p.add_argument("--project-root", help="Override project-root detection")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("init", help="Initialize .codemap/ and run all implemented layers")
    sp.add_argument("--quiet", action="store_true")
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("refresh", help="Regenerate layers. `--files` for incremental.")
    sp.add_argument("--files", nargs="*", default=None, help="Changed files (relative to project root) — only affected systems regen")
    sp.add_argument("--full-on-empty", action="store_true", help="If --files resolves to zero affected systems, do a full refresh anyway")
    sp.add_argument("--quiet", action="store_true")
    sp.set_defaults(func=cmd_refresh)

    sp = sub.add_parser("query", help="Query a slice. JSON by default.")
    sp.add_argument("subject", choices=["systems", "deps", "contract", "symbol", "touches", "system", "boundaries", "violations"])
    sp.add_argument("name", nargs="?", help="Name/path argument for the query")
    sp.add_argument("--kind", default="any",
                    choices=["any", "fn", "struct", "enum", "trait", "type", "const", "static", "mod"],
                    help="(symbol) Restrict to one kind")
    sp.add_argument("--kinds", default=None, help="(symbol) Comma-separated kind set (overrides --kind)")
    sp.set_defaults(func=cmd_query)

    sp = sub.add_parser("hooks", help="Git hook management")
    sp.add_argument("action", choices=["install", "uninstall"])
    sp.add_argument("--quiet", action="store_true")
    sp.set_defaults(func=cmd_hooks)

    sp = sub.add_parser("check", help="CI-friendly: exit 1 on any boundary violation of severity 'error'")
    sp.add_argument("--format", choices=["text", "json"], default="text")
    sp.add_argument("--quiet", action="store_true")
    sp.set_defaults(func=cmd_check)

    sp = sub.add_parser("render", help="Regenerate .codemap/graph.md + boundaries.md (human-viewable via mermaid)")
    sp.add_argument("--quiet", action="store_true")
    sp.set_defaults(func=cmd_render)

    sp = sub.add_parser("boundaries", help="Scaffold or validate .codemap/boundaries.json")
    sp.add_argument("action", choices=["init", "validate"])
    sp.add_argument("--force", action="store_true", help="(init) Overwrite existing boundaries.json")
    sp.add_argument("--quiet", action="store_true")
    sp.set_defaults(func=cmd_boundaries)

    sp = sub.add_parser("info", help="Show project root, detected stack, and meta.json")
    sp.set_defaults(func=cmd_info)

    return p


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\ncodemap: interrupted", file=sys.stderr)
        return 130
