"""
tui/app.py

Main code for the TUI.
"""
import shlex
from typing import List
from tui.cmd import CommandHandler
from textual.binding import Binding
from textual.containers import Vertical
from textual.app import App, ComposeResult
from textual.widgets import Header, Input, RichLog



class TUI(App):
    TITLE = "enteliSCRIPT"
    SUB_TITLE = "v1.0"

    CSS_PATH = "style.tcss"

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
    ]


    def __init__(self) -> None:
        super().__init__()
        self.handler = CommandHandler()

        # Map command names -> handler methods
        self.dispatch = self.handler.get_dispatch()



    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield RichLog(id="log", wrap=True, highlight=True, markup=True)
            yield Input(placeholder="Type a command (e.g. help) …", id="cmd")
        # yield Footer()



    def on_mount(self) -> None:
        self.query_one(Input).focus()
        self._log("[b]Welcome![/b] Type [i]help[/i] to see commands.")



    def _log(self, text: str) -> None:
        log = self.query_one(RichLog)
        log.write(text)



    def on_input_submitted(self, event: Input.Submitted) -> None:
        raw = event.value.strip()
        event.input.value = ""  # clear input

        if not raw:
            return

        self._log(f"[cyan]>[/cyan] {raw}")

        # Parse like a shell: quotes supported
        try:
            parts: List[str] = shlex.split(raw)
        except ValueError as e:
            self._log(f"[red]Parse error:[/red] {e}")
            return
        
        # Support shorthand help: `whoami?` => `help whoami`
        if len(parts) == 1 and parts[0].endswith("?") and len(parts[0]) > 1:
            target = parts[0][:-1].lower()
            help_func = self.dispatch.get("help")
            if help_func is None:
                self._log("[red]Help command not available.[/red]")
                return
            result = help_func(target)
            if result.message:
                if result.ok:
                    self._log(result.message)
                else:
                    self._log(f"[red]{result.message}[/red]")
            return

        cmd, *args = parts
        func = self.dispatch.get(cmd.lower())
        if func is None:
            self._log(f"[red]Unknown command:[/red] {cmd!r} (try 'help')")
            return

        # Call the handler method
        try:
            result = func(*args)
        except TypeError as e:
            # Usually wrong arg count
            self._log(f"[red]Usage error:[/red] {e}")
            return
        except Exception as e:
            self._log(f"[red]Command crashed:[/red] {type(e).__name__}: {e}")
            return

        if result.message:
            if result.ok:
                self._log(result.message)
            else:
                self._log(f"[red]{result.message}[/red]")
