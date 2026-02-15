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
        """
        Initializes the TUI application and command dispatch table.

        Creates a `CommandHandler` instance and builds a lookup mapping of  
        command names/aliases to bound handler methods for runtime dispatch.
        """
        super().__init__()
        self.handler = CommandHandler()

        # Map command names -> handler methods
        self.dispatch = self.handler.get_dispatch()



    def compose(self) -> ComposeResult:
        """
        Builds and yields the widget tree for the application screen.

        The layout contains a header, a scrollable rich log for output, 
        and a single-line command input used to submit commands.

        ### Returns
            - An iterable that yields the widgets to mount (`Header`, `Vertical`, `RichLog`, and `Input`).
        """
        yield Header()
        with Vertical():
            yield RichLog(id="log", wrap=True, highlight=True, markup=True)
            yield Input(placeholder="Type a command (e.g. help) …", id="cmd")
        # yield Footer()



    def on_mount(self) -> None:
        """
        Runs startup UI setup once the app is mounted.

        Focuses the command input so the user can type immediately 
        and writes an initial welcome/help hint to the output log.
        """
        self.query_one(Input).focus()
        self._log("[b]Welcome![/b] Type [i]help[/i] to see commands.")



    def _log(self, text: str) -> None:
        """
        Appends a message to the rich output log.

        ### Parameters
            - `text` ( *string* ) -- Markup-capable message text to write to the `RichLog`.
        """
        log = self.query_one(RichLog)
        log.write(text)



    def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Handles command submission from the input widget.

        Processing flow:
            1. Read and clear the input value.
            2. Ignore empty input.
            3. Echo the command to the log.
            4. Parse arguments using shell-like tokenization (`shlex.split`).
            5. Support shorthand help syntax (`<command>?`).
            6. Dispatch to the matched command handler.
            7. Log success/error output from the command result.

        ### Parameters
            - `event` ( *Input* ) -- Textual `Input.Submitted` event carrying the submitted text.
        """
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
