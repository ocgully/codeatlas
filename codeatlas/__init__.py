"""codeatlas — layered, AI-friendly codemap for agent consumption.

Previously shipped as `codemap`, then `mercator`. Renamed to `codeatlas` to
make the purpose immediately obvious from the name. The legacy `mercator`
and `codemap` CLI entry points remain as deprecation shims that print a
warning and forward to `codeatlas`.

Public API (for agents that import the package rather than invoking the CLI):

    from codeatlas.query import systems, contract, symbol, deps, touches, system

Each returns a JSON-serialisable dict. See `codeatlas.cli` for the command
surface. Schema version is "1" — consumers check `meta.json.schema_version`.
"""
__version__ = "0.6.0"
SCHEMA_VERSION = "1"
