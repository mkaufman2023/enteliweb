"""
tui/objs.py

Objects used in the TUI definition.
"""
from dataclasses import dataclass



@dataclass
class CommandResult:
    ok: bool
    message: str = ""


@dataclass(frozen=True)
class CommandSpec:
    name: str
    usage: str
    summary: str
    aliases: tuple[str, ...] = ()
