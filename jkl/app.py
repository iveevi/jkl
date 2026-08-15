import sys
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

from pygments.token import Token
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.highlight import ANSIDarkHighlightTheme
from textual.widgets import Markdown, MarkdownViewer, Static

REMOTE = ("http", "https", "mailto")
INTERVAL = 0.25

SYNTAX = {
    Token: "ansi_default",
    Token.Comment: "ansi_bright_black italic",
    Token.Error: "ansi_red",
    Token.Generic.Emph: "italic",
    Token.Generic.Error: "ansi_red",
    Token.Generic.Heading: "ansi_blue bold",
    Token.Generic.Strong: "bold",
    Token.Generic.Subheading: "ansi_blue",
    Token.Keyword: "ansi_blue",
    Token.Keyword.Type: "ansi_bright_cyan",
    Token.Name: "ansi_default",
    Token.Name.Builtin: "ansi_cyan",
    Token.Name.Builtin.Pseudo: "ansi_blue italic",
    Token.Name.Class: "ansi_bright_cyan",
    Token.Name.Constant: "ansi_bright_cyan",
    Token.Name.Decorator: "ansi_cyan",
    Token.Name.Exception: "ansi_bright_cyan",
    Token.Name.Function: "ansi_cyan",
    Token.Name.Tag: "ansi_blue",
    Token.Number: "ansi_magenta",
    Token.Operator: "ansi_blue",
    Token.Punctuation: "ansi_default",
    Token.String: "ansi_green",
    Token.String.Doc: "ansi_green italic",
    Token.String.Escape: "ansi_yellow",
    Token.String.Interpol: "ansi_default",
    Token.Whitespace: "",
}

ANSIDarkHighlightTheme.STYLES = SYNTAX


def stamp_of(path: Path) -> float:
    return path.stat().st_mtime


def short_path(path: Path) -> str:
    home = Path.home()
    if path == home:
        return "~"
    if home in path.parents:
        return f"~/{path.relative_to(home)}"
    return str(path)


def read_source(argument: Optional[str]) -> Tuple[str, Optional[Path]]:
    if argument is None:
        return sys.stdin.read(), None
    path = Path(argument).expanduser().resolve()
    return path.read_text(), path


class Status(Static):
    def __init__(self, label: str) -> None:
        super().__init__(id="status")
        self.label = label
        self.note = ""
        self.ratio = 0.0

    def render(self) -> Text:
        left = f" {self.note or self.label}"
        right = f"{int(self.ratio * 100):3d}%   q quit   t contents "
        fill = max(0, self.size.width - len(left) - len(right))
        line = Text(left + " " * fill + right)
        if self.note:
            line.stylize("bold", 0, len(left))
        return line

    def set_ratio(self, ratio: float) -> None:
        self.ratio = ratio
        self.refresh()
        return

    def set_label(self, label: str) -> None:
        self.label = label
        self.note = ""
        self.refresh()
        return

    def set_note(self, note: str) -> None:
        self.note = note
        self.refresh()
        return


class Viewer(MarkdownViewer):
    async def go(self, location) -> None:
        href = str(location)
        if urlparse(href).scheme in REMOTE:
            self.app.open_url(href)
            return
        path, anchor = Markdown.sanitize_location(href)
        if path == Path(".") and anchor:
            self.document.goto_anchor(anchor)
            return
        target = self.navigator.location.parent / path
        if not target.is_file():
            self.app.warn(f"no such file: {short_path(target)}")
            return
        await super().go(href)
        self.app.arrive(self.navigator.location)
        return


class Jkl(App):
    ansi_color = True

    BINDINGS = [
        Binding("q,escape", "quit", "quit"),
        Binding("t", "contents", "contents"),
        Binding("j,down", "line(1)", "down", show=False),
        Binding("k,up", "line(-1)", "up", show=False),
        Binding("ctrl+d,space", "half(1)", "half down", show=False),
        Binding("ctrl+u", "half(-1)", "half up", show=False),
        Binding("g,home", "top", "top", show=False),
        Binding("G,end", "bottom", "bottom", show=False),
        Binding("b,backspace,super+left,alt+left", "back", "back", show=False),
        Binding("super+right,alt+right", "forward", "forward", show=False),
    ]

    CSS = """
    Screen { background: ansi_default; color: ansi_default; }
    Screen > .screen--selection {
        background: ansi_blue;
        color: ansi_bright_white;
    }
    MarkdownViewer {
        background: ansi_default;
        scrollbar-size-vertical: 1;
        scrollbar-background: ansi_default;
        scrollbar-background-hover: ansi_default;
        scrollbar-background-active: ansi_default;
        scrollbar-color: ansi_bright_black;
        scrollbar-color-hover: ansi_bright_black;
        scrollbar-color-active: ansi_blue;
    }
    Markdown { padding: 1 3; width: 1fr; }
    MarkdownBlock { padding: 0; background: ansi_default; }
    MarkdownHeader {
        background: ansi_default;
        color: ansi_bright_white;
        text-style: bold;
        content-align: left middle;
        width: 1fr;
        margin: 2 0 1 0;
    }
    MarkdownH1 {
        color: ansi_bright_white;
        border-bottom: solid ansi_bright_black;
        margin: 0 0 1 0;
    }
    MarkdownH2 { color: ansi_blue; }
    MarkdownH3 { color: ansi_cyan; }
    MarkdownH4, MarkdownH5, MarkdownH6 {
        color: ansi_default;
        margin: 1 0 0 0;
    }
    MarkdownHorizontalRule {
        border-bottom: solid ansi_bright_black;
        margin: 1 0;
        padding: 0;
    }
    MarkdownFence {
        background: ansi_default;
        border-left: outer ansi_bright_black;
        margin: 1 0;
        padding: 0;
        max-height: 24;
    }
    MarkdownFence > Label { padding: 0 2; }
    MarkdownBlockQuote {
        background: ansi_default;
        border-left: outer ansi_yellow;
        margin: 1 0;
        padding: 0 2;
    }
    MarkdownBlockQuote > BlockQuote { margin: 0; }
    MarkdownBullet { color: ansi_bright_black; }
    MarkdownTable { background: ansi_default; margin: 1 0; }
    MarkdownTableContent { keyline: thin ansi_bright_black; }
    MarkdownTableContent > .header {
        color: ansi_bright_white;
        text-style: bold;
        padding: 0 1;
    }
    MarkdownTableContent > .cell { color: ansi_default; padding: 0 1; }
    MarkdownBlock, MarkdownTableCellContents {
        link-color: ansi_cyan;
        link-style: underline;
        link-color-hover: ansi_bright_white;
        link-background-hover: ansi_cyan;
    }
    MarkdownTableOfContents {
        width: 32;
        background: ansi_default;
        border-right: solid ansi_bright_black;
    }
    MarkdownTableOfContents > Tree {
        background: ansi_default;
        padding: 1 1;
    }
    #status {
        dock: bottom;
        height: 1;
        color: ansi_bright_black;
        background: ansi_default;
    }
    """

    def __init__(self, source: str, path: Optional[Path]) -> None:
        super().__init__()
        self.source = source
        self.path = path
        self.stamp = 0.0

    def compose(self) -> ComposeResult:
        yield Viewer(self.source, show_table_of_contents=False, open_links=False)
        yield Status(short_path(self.path) if self.path else "stdin")

    @property
    def viewer(self) -> Viewer:
        return self.query_one(Viewer)

    @property
    def status(self) -> Status:
        return self.query_one(Status)

    def report(self) -> None:
        viewer = self.viewer
        limit = viewer.max_scroll_y
        ratio = viewer.scroll_offset.y / limit if limit else 1.0
        self.status.set_ratio(ratio)
        return

    def arrive(self, path: Path) -> None:
        self.stamp = stamp_of(path) if path.is_file() else 0.0
        self.status.set_label(short_path(path))
        self.report()
        return

    def warn(self, note: str) -> None:
        self.status.set_note(note)
        return

    def on_mount(self) -> None:
        if self.path:
            self.viewer.navigator.go(self.path)
            self.stamp = stamp_of(self.path)
            self.set_interval(INTERVAL, self.poll)
        self.report()
        return

    async def poll(self) -> None:
        path = self.viewer.navigator.location
        if not path.is_file():
            return
        stamp = stamp_of(path)
        if stamp == self.stamp:
            return
        self.stamp = stamp
        offset = self.viewer.scroll_offset.y
        await self.viewer.document.update(path.read_text())
        self.viewer.scroll_to(y=offset, animate=False)
        self.report()
        return

    async def action_back(self) -> None:
        viewer = self.viewer
        await viewer.back()
        self.arrive(viewer.navigator.location)
        return

    async def action_forward(self) -> None:
        viewer = self.viewer
        await viewer.forward()
        self.arrive(viewer.navigator.location)
        return

    def action_contents(self) -> None:
        viewer = self.viewer
        viewer.show_table_of_contents = not viewer.show_table_of_contents
        return

    def action_line(self, direction: int) -> None:
        self.viewer.scroll_relative(y=direction, animate=False)
        self.report()
        return

    def action_half(self, direction: int) -> None:
        step = max(1, self.viewer.size.height // 2)
        self.viewer.scroll_relative(y=direction * step, animate=False)
        self.report()
        return

    def action_top(self) -> None:
        self.viewer.scroll_home(animate=False)
        self.report()
        return

    def action_bottom(self) -> None:
        self.viewer.scroll_end(animate=False)
        self.report()
        return


def main() -> None:
    argument = sys.argv[1] if len(sys.argv) > 1 else None
    source, path = read_source(argument)
    if not sys.stdin.isatty():
        sys.stdin = open("/dev/tty")
    Jkl(source, path).run()
    return
