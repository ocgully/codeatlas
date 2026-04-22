"""codemap — layered, AI-friendly codemap for agent consumption.

Public API (for agents that import the package rather than invoking the CLI):

    from codemap.query import systems, contract, symbol, deps, touches, system

Each returns a JSON-serialisable dict. See `codemap.cli` for the command
surface. Schema version is "1" — consumers check `meta.json.schema_version`.
"""
__version__ = "0.2.0"
SCHEMA_VERSION = "1"
