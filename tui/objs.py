"""
tui/objs.py

Objects used in the TUI definition.
"""
from dataclasses import dataclass



@dataclass
class CommandResult:
    """
    Represents the outcome of executing a command handler.

    ### Attributes
        - `ok` ( *bool* ) -- Indicates whether the command completed successfully.
        - `message` ( *string* ) -- User-facing output to display in the log.
    """
    ok: bool
    message: str = ""


@dataclass(frozen=True)
class CommandSpec:
    """
    Defines immutable metadata for a registered command.

    Used by the command system for help text generation and dispatch table construction.

    ### Attributes
        - `name` ( *string* ) -- Canonical command name used for primary lookup.
        - `usage` ( *string* ) -- Usage text shown in help output.
        - `summary` ( *string* ) -- Short one-line description of the command.
        - `aliases` ( *tuple[string, ...]* ) -- Alternate names that map to the same command.
    """
    name: str
    usage: str
    summary: str
    aliases: tuple[str, ...] = ()
