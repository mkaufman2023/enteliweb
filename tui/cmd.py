"""
tui/cmd.py

Command handling logic for the TUI.
"""
from tui.objs import CommandResult, CommandSpec
from typing import Callable, Dict, Iterable, Optional



def command(name: str, *, usage: Optional[str] = None, summary: str = "", aliases: Iterable[str] = ()) -> Callable[[Callable[..., CommandResult]], Callable[..., CommandResult]]:
    """
    Attaches CLI metadata to a command method.
    """
    normalized_name = name.lower()
    normalized_usage = usage or normalized_name
    normalized_aliases = tuple(alias.lower() for alias in aliases)

    def decorator(function: Callable[..., CommandResult]) -> Callable[..., CommandResult]:
        function._command_spec = CommandSpec(
            name    = normalized_name,
            usage   = normalized_usage,
            summary = summary,
            aliases = normalized_aliases,
        )
        return function

    return decorator


def _get_command_spec(method: Callable[..., CommandResult]) -> Optional[CommandSpec]:
    """
    Returns the `CommandSpec` for a method, or `None` if it's not a command.
    """
    return getattr(method, "_command_spec", None)



class CommandHandler:
    """
    Put app/business logic methods here.
    """
    def __init__(self) -> None:
        self.name = "anonymous"
        self._spec_by_name = self._build_specs()



    @command(
        name    = "help",
        aliases = ("h", "?"),
        usage   = "help <command>",
        summary = "Show command list or details for one command.",
    )
    def cmd_help(self, command_name: str = "") -> CommandResult:
        name = command_name.strip().lower()
        if name:
            spec = self._spec_by_name.get(name)
            if spec is None:
                for candidate in self._spec_by_name.values():
                    if name in candidate.aliases:
                        spec = candidate
                        break
            if spec is None:
                return CommandResult(False, f"Unknown command {command_name!r}")

            aliases = f" (aliases: {', '.join(spec.aliases)})" if spec.aliases else ""
            details = [
                f"{spec.name}{aliases}",
                f"  usage: {spec.usage}",
            ]
            if spec.summary:
                details.append(f"  {spec.summary}")
            return CommandResult(True, "\n".join(details))

        lines = ["Commands:"]
        for spec in sorted(self._spec_by_name.values(), key=lambda s: s.name):
            alias_text = f" [{', '.join(spec.aliases)}]" if spec.aliases else ""
            summary = f" - {spec.summary}" if spec.summary else ""
            lines.append(f"  {spec.usage}{alias_text}{summary}")
        return CommandResult(True, "\n".join(lines))



    @command(
        name    = "echo", 
        usage   = "echo <text...>", 
        summary = "Print text back to the log."
    )
    def cmd_echo(self, *args: str) -> CommandResult:
        return CommandResult(True, " ".join(args))



    @command(
        name    = "add",
        usage   = "add <a> <b>",
        summary = "Add two numbers."
    )
    def cmd_add(self, a: str, b: str) -> CommandResult:
        try:
            x = float(a)
            y = float(b)
        except ValueError:
            return CommandResult(False, "add expects two numbers, e.g. `add 2 3`")
        return CommandResult(True, f"{x} + {y} = {x + y}")



    @command(
        name    = "setname",
        usage   = "setname <name>",
        summary = "Set your current username."
    )
    def cmd_setname(self, name: str) -> CommandResult:
        self.name = name
        return CommandResult(True, f"Name set to {self.name!r}")



    @command(
        name    = "whoami",
        summary = "Show your current username."
    )
    def cmd_whoami(self) -> CommandResult:
        return CommandResult(True, f"You are {self.name!r}")




    def _build_specs(self) -> Dict[str, CommandSpec]:
        specs: Dict[str, CommandSpec] = {}
        for attr_name in dir(self):
            method = getattr(self, attr_name)
            if not callable(method):
                continue
            spec = _get_command_spec(method)
            if spec is None:
                continue
            specs[spec.name] = spec
        return specs


    def get_dispatch(self) -> dict[str, Callable[..., CommandResult]]:
        dispatch: dict[str, Callable[..., CommandResult]] = {}
        for attr_name in dir(self):
            method = getattr(self, attr_name)
            if not callable(method):
                continue
            spec = _get_command_spec(method)
            if spec is None:
                continue
            dispatch[spec.name] = method
            for alias in spec.aliases:
                dispatch[alias] = method
        return dispatch