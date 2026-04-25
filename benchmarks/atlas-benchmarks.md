# Mercator Atlas Benchmarks

Real-world numbers from running Mercator against six public repos covering Rust, C++, TypeScript, and Python — chosen to stress refresh-time scaling, atlas-size scaling, and detection accuracy on codebases Mercator has never seen before. Each repo is shallow-cloned (`--depth 1`), then `mercator init` and `mercator refresh` are run back-to-back against an out-of-tree storage dir (`--storage-dir`). All wall times use `time.perf_counter()`.

## Machine

```
=== Machine ===
OS:         Microsoft Windows 11 Home (10.0.26200)
System:     Micro-Star International MS-7B86
CPU:        AMD Ryzen 7 2700X (8 cores / 16 threads, Zen+ 12nm, 2018)
RAM:        32 GB

=== Storage (5 disks) ===
Primary work / repo disk: Samsung SSD 980 PRO with Heatsink 2TB (NVMe PCIe 4.0)
Secondary SSD:            Samsung SSD 850 EVO 500GB (SATA)
HDDs:                     SAMSUNG HD502HJ x2 (466 GB SATA), WDC WD30EZRZ 2.8TB (SATA)

=== Tooling ===
Python:     3.12.10
git:        2.37.3 (Git for Windows)
```

## Run metadata

- **Mercator:** `mercator 0.5.0 (schema 1)`
- **Commit:** `515a3a5c79285ccc24c87c2ca4317a9ad5c59082`
- **Timestamp (UTC):** `2026-04-25T04:34:09+00:00`

## Summary

| Repo | URL | Stack(s) | Clone | Init | Refresh | Projects | Σ Systems | Σ Contracts | Atlas KB | Storage KB |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `ripgrep` | <https://github.com/BurntSushi/ripgrep> | rust | 0.00s* | 11.90s | 6.17s | 11 | 11 | 11 | 678.2 | 781.4 |
| `bevy` | <https://github.com/bevyengine/bevy> | rust | 0.00s* | 137.08s | 107.43s | 83 | 83 | 83 | 7787.7 | 10278.9 |
| `vite` | <https://github.com/vitejs/vite> | — | 0.00s* | 14.84s | — | 0 | 0 | 0 | — | — |
| `aider` | <https://github.com/Aider-AI/aider> | python | 0.00s* | 11.31s | 4.17s | 1 | 7 | 7 | 145.0 | 346.5 |
| `opencode` | <https://github.com/sst/opencode> | rust, ts | 0.00s* | 69.35s | 27.05s | 23 | 42 | 42 | 3621.6 | 7116.9 |

`*` = clone time skipped because the working copy already existed (idempotent re-run).

## Per-repo detail

### `ripgrep` — Small Rust

- URL: <https://github.com/BurntSushi/ripgrep>
- Clone path: `C:\tmp\bench-clones\ripgrep`
- Storage dir: `C:\tmp\bench-atlases\ripgrep`
- Stacks: `['rust']`
- init: 11.90s (rc=0)
- refresh: 6.17s (rc=0)
- Projects detected: **11**
- Cross-project edges: 18
- atlas.html: 57,499 bytes + sub-atlases 636,947 bytes
- Total storage on disk: 800,135 bytes

Projects:

| id | name | stack | category | systems | contracts |
|---|---|---|---|---:|---:|
| `crates-cli` | grep-cli | rust | lib | 1 | 1 |
| `crates-globset` | globset | rust | lib | 1 | 1 |
| `crates-grep` | grep | rust | lib | 1 | 1 |
| `crates-ignore` | ignore | rust | lib | 1 | 1 |
| `crates-matcher` | grep-matcher | rust | lib | 1 | 1 |
| `crates-pcre2` | grep-pcre2 | rust | lib | 1 | 1 |
| `crates-printer` | grep-printer | rust | lib | 1 | 1 |
| `crates-regex` | grep-regex | rust | lib | 1 | 1 |
| `crates-searcher` | grep-searcher | rust | lib | 1 | 1 |
| `ripgrep` | ripgrep | rust | tool | 1 | 1 |
| `fuzz` | fuzz | rust | tool | 1 | 1 |

_Why this matters:_ ripgrep is the small-workspace anchor — a single Rust crate with a couple of helper crates. Init in 11.90s sets a floor for what 'fast' looks like; anything slower than this on a comparably-sized tree warrants a look at I/O, not algorithmic cost.

### `bevy` — Large Rust game engine

- URL: <https://github.com/bevyengine/bevy>
- Clone path: `C:\tmp\bench-clones\bevy`
- Storage dir: `C:\tmp\bench-atlases\bevy`
- Stacks: `['rust']`
- init: 137.08s (rc=0)
- refresh: 107.43s (rc=0)
- Projects detected: **83**
- Cross-project edges: 652
- atlas.html: 1,116,779 bytes + sub-atlases 6,857,781 bytes
- Total storage on disk: 10,525,590 bytes

Projects:

| id | name | stack | category | systems | contracts |
|---|---|---|---|---:|---:|
| `bevy` | bevy | rust | lib | 1 | 1 |
| `benches` | benches | rust | lib | 1 | 1 |
| `crates-bevy_a11y` | bevy_a11y | rust | lib | 1 | 1 |
| `crates-bevy_android` | bevy_android | rust | lib | 1 | 1 |
| `crates-bevy_animation` | bevy_animation | rust | lib | 1 | 1 |
| `crates-bevy_animation-macros` | bevy_animation_macros | rust | lib | 1 | 1 |
| `crates-bevy_anti_alias` | bevy_anti_alias | rust | lib | 1 | 1 |
| `crates-bevy_app` | bevy_app | rust | lib | 1 | 1 |
| `crates-bevy_asset` | bevy_asset | rust | lib | 1 | 1 |
| `crates-bevy_asset-macros` | bevy_asset_macros | rust | lib | 1 | 1 |
| `crates-bevy_audio` | bevy_audio | rust | lib | 1 | 1 |
| `crates-bevy_camera` | bevy_camera | rust | lib | 1 | 1 |
| `crates-bevy_camera_controller` | bevy_camera_controller | rust | lib | 1 | 1 |
| `crates-bevy_clipboard` | bevy_clipboard | rust | lib | 1 | 1 |
| `crates-bevy_color` | bevy_color | rust | lib | 1 | 1 |
| `crates-bevy_color-crates-gen_tests` | gen_tests | rust | lib | 1 | 1 |
| `crates-bevy_core_pipeline` | bevy_core_pipeline | rust | lib | 1 | 1 |
| `crates-bevy_derive` | bevy_derive | rust | lib | 1 | 1 |
| `crates-bevy_derive-compile_fail` | bevy_derive_compile_fail | rust | lib | 1 | 1 |
| `crates-bevy_dev_tools` | bevy_dev_tools | rust | lib | 1 | 1 |
| `crates-bevy_diagnostic` | bevy_diagnostic | rust | lib | 1 | 1 |
| `crates-bevy_dylib` | bevy_dylib | rust | lib | 1 | 1 |
| `crates-bevy_ecs` | bevy_ecs | rust | lib | 1 | 1 |
| `crates-bevy_ecs-compile_fail` | bevy_ecs_compile_fail | rust | lib | 1 | 1 |
| `crates-bevy_ecs-macros` | bevy_ecs_macros | rust | lib | 1 | 1 |
| `crates-bevy_encase_derive` | bevy_encase_derive | rust | lib | 1 | 1 |
| `crates-bevy_feathers` | bevy_feathers | rust | lib | 1 | 1 |
| `crates-bevy_gilrs` | bevy_gilrs | rust | lib | 1 | 1 |
| `crates-bevy_gizmos` | bevy_gizmos | rust | lib | 1 | 1 |
| `crates-bevy_gizmos-macros` | bevy_gizmos_macros | rust | lib | 1 | 1 |
| `crates-bevy_gizmos_render` | bevy_gizmos_render | rust | lib | 1 | 1 |
| `crates-bevy_gltf` | bevy_gltf | rust | lib | 1 | 1 |
| `crates-bevy_image` | bevy_image | rust | lib | 1 | 1 |
| `crates-bevy_input` | bevy_input | rust | lib | 1 | 1 |
| `crates-bevy_input_focus` | bevy_input_focus | rust | lib | 1 | 1 |
| `crates-bevy_internal` | bevy_internal | rust | lib | 1 | 1 |
| `crates-bevy_light` | bevy_light | rust | lib | 1 | 1 |
| `crates-bevy_log` | bevy_log | rust | lib | 1 | 1 |
| `crates-bevy_macro_utils` | bevy_macro_utils | rust | lib | 1 | 1 |
| `crates-bevy_material` | bevy_material | rust | lib | 1 | 1 |
| `crates-bevy_material-macros` | bevy_material_macros | rust | lib | 1 | 1 |
| `crates-bevy_math` | bevy_math | rust | lib | 1 | 1 |
| `crates-bevy_mesh` | bevy_mesh | rust | lib | 1 | 1 |
| `crates-bevy_pbr` | bevy_pbr | rust | lib | 1 | 1 |
| `crates-bevy_picking` | bevy_picking | rust | lib | 1 | 1 |
| `crates-bevy_platform` | bevy_platform | rust | lib | 1 | 1 |
| `crates-bevy_post_process` | bevy_post_process | rust | lib | 1 | 1 |
| `crates-bevy_ptr` | bevy_ptr | rust | lib | 1 | 1 |
| `crates-bevy_reflect` | bevy_reflect | rust | lib | 1 | 1 |
| `crates-bevy_reflect-compile_fail` | bevy_reflect_compile_fail | rust | lib | 1 | 1 |
| … | _33 more rows omitted_ | | | | |

_Why this matters:_ Bevy is the marquee large Rust monorepo — 83 crates, 83 systems. Init took 137.08s and refresh 107.43s; they should be near-identical because Mercator is fully deterministic and does not cache between runs. The atlas renders one card per crate plus per-crate sub-atlases — this is the run that proves whether atlas size scales linearly with project count or blows up.

### `vite` — TypeScript monorepo

- URL: <https://github.com/vitejs/vite>
- Clone path: `C:\tmp\bench-clones\vite`
- Storage dir: `C:\tmp\bench-atlases\vite`
- Stacks: `[]`
- init: 14.84s (rc=3)
- refresh: — (rc=None)
- Projects detected: **0**
- Cross-project edges: None
- atlas.html: 0 bytes + sub-atlases 0 bytes
- Total storage on disk: 0 bytes

**init stderr (tail):**

```
mercator: Unexpected UTF-8 BOM (decode using utf-8-sig): line 1 column 1 (char 0)
```

_Why this matters:_ Vite is a pnpm workspace — exactly the case the new TypeScript Layer 2 scanner targets. Mercator detected 0 packages totalling 0 systems. Refresh (—) vs init (14.84s) is the first real-world data point on whether the TS scanner has the same deterministic behaviour as the Rust/Python ones.

### `aider` — Python AI/LLM

- URL: <https://github.com/Aider-AI/aider>
- Clone path: `C:\tmp\bench-clones\aider`
- Storage dir: `C:\tmp\bench-atlases\aider`
- Stacks: `['python']`
- init: 11.31s (rc=0)
- refresh: 4.17s (rc=0)
- Projects detected: **1**
- Cross-project edges: 0
- atlas.html: 148,467 bytes + sub-atlases 0 bytes
- Total storage on disk: 354,780 bytes

Projects:

| id | name | stack | category | systems | contracts |
|---|---|---|---|---:|---:|
| `aider-chat` | aider-chat | python | tool | 7 | 7 |

_Why this matters:_ A real Python AI/LLM codebase — 7 systems across 1 project(s). The systems count reflects every directory with `__init__.py`, so deeply-nested packages can inflate it; treat the number as 'directories Mercator considered scope-worthy', not 'logical components'.

### `opencode` — TypeScript AI/LLM

- URL: <https://github.com/sst/opencode>
- Clone path: `C:\tmp\bench-clones\opencode`
- Storage dir: `C:\tmp\bench-atlases\opencode`
- Stacks: `['rust', 'ts']`
- init: 69.35s (rc=0)
- refresh: 27.05s (rc=0)
- Projects detected: **23**
- Cross-project edges: 28
- atlas.html: 672,092 bytes + sub-atlases 3,036,456 bytes
- Total storage on disk: 7,287,720 bytes

Projects:

| id | name | stack | category | systems | contracts |
|---|---|---|---|---:|---:|
| `opencode` | opencode | ts | app | 20 | 20 |
| `github` | github | ts | app | 1 | 1 |
| `packages-app` | @opencode-ai/app | ts | lib | 1 | 1 |
| `packages-console-app` | @opencode-ai/console-app | ts | lib | 1 | 1 |
| `packages-console-core` | @opencode-ai/console-core | ts | lib | 1 | 1 |
| `packages-console-function` | @opencode-ai/console-function | ts | lib | 1 | 1 |
| `packages-console-mail` | @opencode-ai/console-mail | ts | lib | 1 | 1 |
| `packages-console-resource` | @opencode-ai/console-resource | ts | lib | 1 | 1 |
| `packages-desktop` | @opencode-ai/desktop | ts | lib | 1 | 1 |
| `packages-desktop-electron` | @opencode-ai/desktop-electron | ts | lib | 1 | 1 |
| `packages-desktop-src-tauri` | opencode-desktop | rust | lib | 1 | 1 |
| `packages-enterprise` | @opencode-ai/enterprise | ts | lib | 1 | 1 |
| `packages-function` | @opencode-ai/function | ts | lib | 1 | 1 |
| `packages-opencode` | opencode | ts | lib | 1 | 1 |
| `packages-plugin` | @opencode-ai/plugin | ts | lib | 1 | 1 |
| `packages-script` | @opencode-ai/script | ts | lib | 1 | 1 |
| `packages-sdk-js` | @opencode-ai/sdk | ts | lib | 1 | 1 |
| `packages-shared` | @opencode-ai/shared | ts | lib | 1 | 1 |
| `packages-slack` | @opencode-ai/slack | ts | lib | 1 | 1 |
| `packages-storybook` | @opencode-ai/storybook | ts | lib | 1 | 1 |
| `packages-ui` | @opencode-ai/ui | ts | lib | 1 | 1 |
| `packages-web` | @opencode-ai/web | ts | lib | 1 | 1 |
| `sdks-vscode` | opencode | ts | lib | 1 | 1 |

_Why this matters:_ A TypeScript AI/LLM codebase — 23 package(s), 42 system(s). Useful as a sanity check that the TS scanner doesn't choke on AI-tooling repos which often mix TS source, generated code, and bundled vendor scripts.

## Detection rough edges

- `vite`: init returned non-zero (3); see per-repo stderr.

## Notes for re-running

```bash
python benchmarks/run_benchmarks.py
```

The runner is idempotent: it skips clones that already exist under `C:\tmp\bench-clones\`, but always rebuilds `.mercator/` storage in `C:\tmp\bench-atlases\<repo>\` from scratch.
