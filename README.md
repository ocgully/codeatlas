# codemap

A layered, AI-friendly codemap CLI. Produces structured views of a project's
code (systems → contracts → symbols → assets) under `.codemap/`, and — more
importantly — exposes a **query API** that agents use to pull minimal,
typed slices on demand instead of reading whole MD files.

**Design goals** (in order):

1. **Agents query the CLI; they don't read `.codemap/*.md` files.** A
   targeted `codemap query contract <system>` is orders of magnitude smaller
   than the equivalent rendered MD — less context consumed, faster
   answers, typed output.
2. **Zero-cost to keep current.** A post-commit hook incrementally regenerates
   only the slices affected by a commit. No manual refresh in the loop.
3. **Portable outputs.** No absolute paths in committed JSON; timestamps live
   in `meta.json` only. Safe to commit `.codemap/` and diff structural change
   over time.
4. **Graceful degradation.** If a stack or layer isn't implemented yet, the
   CLI says so with an actionable message. Agents relay the message; they
   don't invent answers.

## Install

```bash
pip install codemap
# or from source:
git clone https://github.com/ocgully/codemap
pip install -e codemap/
```

## Quick start

From a project root:

```bash
codemap init
```

Then — from any working directory inside the project — query:

```bash
codemap query systems                    # Layer 1, full view
codemap query deps <system>              # who depends on / is depended by
codemap query contract <system>          # Layer 2, public surface (Rust today)
codemap query symbol <name>              # Layer 3 def lookup
codemap query touches <path>             # which system owns this file?
codemap query system <name>              # composite: Layer 1 entry + deps + contract
```

Install the git hook so the map stays current:

```bash
codemap hooks install
```

After each commit, a post-commit hook runs `codemap refresh --files <changed>`
which regenerates only the systems whose files changed. No manual step.

## Boundaries (DMZs / forbidden edges)

Independent of what code currently does, the project declares **what the
code must never do**: view must not reach sim, domain must not reach
infrastructure, and so on. These rules live in `.codemap/boundaries.json`
(committed, architect-authored) and the CLI evaluates them against the
current dep graph every refresh.

```bash
codemap boundaries init         # scaffold a template with inline schema docs
codemap boundaries validate     # check selectors resolve to real systems
codemap query boundaries        # rule list + per-rule pass/fail
codemap query violations        # just the failing ones, with paths
codemap check                   # CI gate — exit 1 on error-severity
```

`boundaries.json` schema (example for a game engine):

```json
{
  "schema_version": "1",
  "layers": {
    "view": ["view_*", "ui_*"],
    "sim":  ["sim_*", "gameplay_*"]
  },
  "boundaries": [
    {
      "name": "View must not reach Simulation",
      "rationale": "Sim is headless / deterministic. View is presentation-only.",
      "severity": "error",
      "from": "view",
      "not_to": "sim",
      "transitive": true
    }
  ]
}
```

Selectors resolve in order: exact system name > layer name (from the `layers`
map) > glob pattern (`fnmatch`-style, e.g. `view_*`). `transitive: true` (the
default) flags paths through any number of intermediate systems; `false`
checks direct edges only.

Severity:
- `info` — factual, no action required
- `warning` — worth reviewing; **does not** fail CI
- `error` — fails `codemap check` (exit 1)

## Human-viewable visual output

`codemap refresh` regenerates two human-readable files alongside the JSON:

- `.codemap/graph.md` — mermaid diagrams of the dep graph and the DMZ overlay (forbidden edges dashed red, violations drawn prominently). Layers appear as mermaid subgraphs so grouping is visible at a glance.
- `.codemap/boundaries.md` — pass/fail table for every rule, resolved system sets, violation paths with rationales.

Both files render natively in GitHub, VS Code's markdown preview, Obsidian,
and any tool that understands mermaid code blocks — no LLM and no extra
install required. They are **derived outputs**: edit `boundaries.json`,
run `codemap refresh`, views regenerate deterministically.

Use `codemap render` to regenerate just the visual views without touching
Layer 1/2 JSON (useful when you've only edited `boundaries.json`).

## What you get under `.codemap/`

```
.codemap/
├── README.md                  pointer to this tool
├── meta.json                  stack, tool versions, last-refresh time, git HEAD
├── systems.json               Layer 1 (all systems + deps)
├── systems.md                 Layer 1 rendered (table + mermaid, ≤20 nodes)
├── contracts/
│   ├── {system}.json          Layer 2 per system (Rust today)
│   └── {system}.md            Layer 2 rendered (humans only)
├── symbols/                   Layer 3 is queried on demand; no persisted index yet
└── assets/                    Layer 4 stub
```

Committing `.codemap/` into the repo is recommended — structural-change
history over time is valuable, and the outputs are deterministic + free of
absolute paths.

## Supported stacks

| Stack | Detection | Layer 1 | Layer 2 | Layer 3 |
|-------|-----------|---------|---------|---------|
| Rust | `Cargo.toml` at root | `cargo metadata` | in-tree `pub`-item scanner | definition lookup (class/struct/trait/fn); refs need rust-analyzer |
| Unity | `Assets/` + `ProjectSettings/` + `Packages/manifest.json` | `.asmdef` files + `.cs` file walk (`.csproj` ignored — editor-generated, untrustworthy) | TBD | TBD |
| Dart/Flutter | `pubspec.yaml` at root | walk for nested `pubspec.yaml` (monorepo-aware) | TBD | TBD |
| TypeScript | `package.json` at root | TBD (#23) | TBD | TBD |
| Python | `pyproject.toml` / `setup.py` | TBD | TBD | TBD |
| Go | `go.mod` / `go.work` | TBD | TBD | TBD |

Unknown stacks exit with code 3 and a message listing what would unlock support.

## CLI reference

```
codemap init                       Detect stack, init .codemap/, run all implemented layers
codemap refresh                    Full regenerate
codemap refresh --files …          Incremental — regen only systems whose files changed
codemap info                       Project root, detected stack, meta.json
codemap hooks install              Install post-commit git hook
codemap hooks uninstall            Remove it
codemap render                     Regenerate visual views (.codemap/graph.md + boundaries.md)
codemap check                      CI gate — exit 1 on error-severity DMZ violation
codemap boundaries init            Scaffold a .codemap/boundaries.json template
codemap boundaries validate        Check selectors resolve to real systems
codemap query systems              Full Layer 1 JSON
codemap query deps <system>        Dependents + dependencies
codemap query contract <system>    Layer 2 per-system JSON
codemap query symbol <name>        Layer 3 def lookup (--kind, --kinds)
codemap query touches <path>       Which system owns this file
codemap query system <name>        Layer 1 entry + edges + Layer 2 combined
codemap query boundaries           DMZ rules + per-rule pass/fail
codemap query violations           Just the failing rules, with paths
codemap --help                     Full help
codemap --version                  Version + schema version
```

All `query` output is JSON; agents parse it directly. The `.md` files under
`.codemap/contracts/` and `.codemap/systems.md` exist for humans browsing the
repo and are deterministic (no timestamps) so diffs stay clean.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Usage error |
| 2 | Missing prerequisite (cargo, python, etc.) |
| 3 | Unsupported / unrecognised stack |
| 4 | Internal failure (parser crash, malformed input) |

## Installation options

Two ways agents can invoke the tool:

**No-install (default):**
```bash
codemap <cmd>
```

**Installed via pip (nicer `codemap` entry point):**
```bash
pip install -e codemap/
codemap <cmd>
```

Both paths share the same package; the launcher just adds `scripts/codemap/`
to `sys.path` before importing.

## Package layout

```
scripts/
├── codemap.py                      # launcher — no pip install required
└── codemap/
    ├── pyproject.toml              # for pip install -e .
    └── codemap/
        ├── __init__.py             # package version + schema version
        ├── __main__.py             # python -m codemap
        ├── cli.py                  # argparse + subcommand dispatch
        ├── paths.py                # project-root discovery
        ├── detect.py               # stack detection (Cargo.toml / asmdef / pubspec / …)
        ├── meta.py                 # meta.json I/O
        ├── refresh.py              # full + incremental refresh
        ├── query.py                # agent-facing query API
        ├── hooks.py                # post-commit git hook install/uninstall
        ├── stacks/
        │   ├── rust.py             # Layer 1 (cargo metadata) + 2 (pub-scan) + 3 (def lookup)
        │   ├── unity.py            # Layer 1 via .asmdef + .cs walk
        │   └── dart.py             # Layer 1 via pubspec walk
        └── render/
            ├── systems_md.py       # systems.json → systems.md (deterministic)
            └── contract_md.py      # contracts/{system}.json → {system}.md (deterministic)
```

## Integration with `/bootstrap-from-roadmap`

Every project migrated via `/bootstrap-from-roadmap` runs `codemap init`
during bootstrap. It also installs the post-commit hook. New projects land
with a populated `.codemap/` and an auto-refresh loop wired up.

## Integration with the `codemap-keeper` core agent

The `codemap-keeper` agent (core marketplace) is the librarian for this
data. When other agents need structural context — "does `view` reach `sim`?",
"what's the public surface of `core-engine`?", "which system owns this
file?" — they ask codemap-keeper, which invokes the CLI and returns a
structured, cited slice. Agents don't hand-search and they don't read
`.codemap/*.md`. The CLI is the interface.

## Regenerating manually

```bash
codemap refresh                                  # full regen
codemap refresh --files crates/foo/src/lib.rs    # incremental
```

Or delete `.codemap/` and re-run `init`. Outputs are deterministic.

## Known limitations (v1)

- **Rust Layer 2** — line-scans `pub` items at file top level. Misses items
  declared inside inline `mod { ... }` blocks and macro-generated items.
  Higher fidelity is available via `cargo install cargo-public-api` (nightly
  toolchain) — not yet wired into the CLI but on the roadmap.
- **Unity Layer 2/3** — not yet. Pending design of a suitable C# scanner.
- **Dart Layer 2/3** — not yet.
- **Call-site resolution** — `codemap query symbol` returns definitions only.
  Callers / references require rust-analyzer LSP integration, which is a
  future evolution.
- **YAML subset for pubspec** — we parse only the top-level keys and the
  `dependencies:` / `dev_dependencies:` / `dependency_overrides:` blocks.
  Flow-style YAML and anchors in those blocks aren't supported.
