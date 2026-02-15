"""
tui/cmd.py

Command handling logic for the TUI.
"""
from tui.objs import CommandResult, CommandSpec
from typing import Callable, Dict, Iterable, Optional



def command(name: str, *, usage: Optional[str] = None, summary: str = "", aliases: Iterable[str] = ()) -> Callable[[Callable[..., CommandResult]], Callable[..., CommandResult]]:
    """
    Creates a decorator that attaches CLI metadata to a command method.

    The decorator normalizes command metadata (lowercased name/aliases and
    default usage text) and stores it on the decorated function as `_command_spec`.

    ### Parameters
        - `name` ( *string* ) -- Primary command name.
        - `usage` ( *string*, *optional* ) -- Usage string shown in help output. Defaults to `name` if not provided.
        - `summary` ( *string*, *optional* ) -- Short description for help listings.
        - `aliases` ( *tuple*/*list*, *optional* ) -- Alternate names that dispatch to the same command.

    ### Returns
        - A decorator that accepts a command function and returns that same function with an attached `CommandSpec`.
    """
    normalized_name = name.lower()
    normalized_usage = usage or normalized_name
    normalized_aliases = tuple(alias.lower() for alias in aliases)

    def decorator(function: Callable[..., CommandResult]) -> Callable[..., CommandResult]:
        """
        Attaches a normalized `CommandSpec` to the target function.

        ### Parameters
            - `function` ( *Callable* ) -- Command handler function to annotate.

        ### Returns
            - The same function instance with `_command_spec` metadata attached.
        """
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
    Fetches command metadata from a callable if present.

    ### Parameters
        - `method` ( *Callable* ) -- Callable that may have command metadata attached.

    ### Returns
        - The `CommandSpec` attached to `method`, or `None` if the callable is not a registered command.
    """
    return getattr(method, "_command_spec", None)



class CommandHandler:
    """
    Implements command/business logic and expose command metadata.

    Stores runtime state (such as current username),
    provides command handler methods (`cmd_*`), 
    and builds structures used for help output and command dispatch.
    """
    def __init__(self) -> None:
        """
        Initializes handler state and precomputes command specifications.
        """
        self.name = "anonymous"
        self._spec_by_name = self._build_specs()



    @command(
        name    = "help",
        aliases = ("h", "?"),
        usage   = "help <command>",
        summary = "Show command list or details for one command.",
    )
    def cmd_help(self, command_name: str = "") -> CommandResult:
        """
        Shows general help or detailed help for a specific command.

        If `command_name` is empty, returns a formatted list of all commands.
        If provided, resolves by command name first, then by alias.

        ### Parameters
            - `command_name` ( *string* ) -- Optional command/alias to inspect.

        ### Returns
            - `CommandResult` containing either: detailed help for one command, 
            the full command listing, or an error message if the command is unknown.
        """
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
        """
        Echos arbitrary text back to the caller.

        ### Parameters
            - `*args` ( *string* ) -- Tokens to join into a single output string.

        ### Returns
            - `CommandResult` with the joined text as the message.
        """
        return CommandResult(True, " ".join(args))



    @command(
        name    = "add",
        usage   = "add <a> <b>",
        summary = "Add two numbers."
    )
    def cmd_add(self, a: str, b: str) -> CommandResult:
        """
        Adds two numeric inputs and returns the computed sum.

        ### Parameters
            - `a` ( *string* ) -- First number (string form).
            - `b` ( *string*) -- Second number (string form).

        ### Returns
            - `CommandResult` with: success and the arithmetic result, or failure if either argument is not numeric.
        """
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
        """
        Sets the current in-memory username.

        ### Parameters
            - `name` ( *string* ) -- New username value.

        ### Returns
            - `CommandResult` confirming the updated username.
        """
        self.name = name
        return CommandResult(True, f"Name set to {self.name!r}")



    @command(
        name    = "whoami",
        summary = "Show your current username."
    )
    def cmd_whoami(self) -> CommandResult:
        """
        Fetches the current in-memory username.

        ### Returns
            - `CommandResult` containing the active username.
        """
        return CommandResult(True, f"You are {self.name!r}")




    def _build_specs(self) -> Dict[str, CommandSpec]:
        """
        Builds a mapping of canonical command names to `CommandSpec`.

        Scans this instance for callable attributes decorated with
        `@command` and indexes each discovered spec by its primary command name.

        ### Returns
            - Dictionary keyed by command name with `CommandSpec` values.
        """
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
        """
        Builds a dispatch table for commands and aliases.

        Each key is either a command name or alias,
        and each value is the bound handler method to execute.

        ### Returns
            - Dictionary mapping command tokens to bound command callables.
        """
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
