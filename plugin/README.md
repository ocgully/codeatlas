# Mercator — Flotilla plugin contributions

When a downstream project runs `flotilla install mercator`, the Flotilla
CLI pip-installs Mercator and copies/symlinks this directory's
contributions into the consumer's `.claude/`.

See `flotilla.yaml` one level up for the manifest. See
[github.com/ocgully/flotilla](https://github.com/ocgully/flotilla) for
the CLI.

## What ships

- `agents/codemap-keeper.md` — the agent that maintains + queries the codemap
- `commands/mercator.md` — `/mercator` Claude Code command for structural context
