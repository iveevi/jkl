import sys
from pathlib import Path
from typing import Optional, Tuple

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import MarkdownViewer, Static


def short_path(path: Path) -> str:
    home = Path.home()
    if path == home:
        return "~"
    if home in path.parents:
        return f"~/{path.relative_to(home)}"
    return str(path)


def read_source(argument: Optional[str]) -> Tuple[str, str]:
    if argument is None:
        return sys.stdin.read(), "stdin"
    path = Path(argument).expanduser()
    return path.read_text(), short_path(path.resolve())


class Status(Static):
    def __init__(self, label: str) -> None:
        super().__init__(id="status")
        self.label = label
        self.ratio = 0.0

    def render(self) -> Text:
        left = f" {self.label}"
        right = f"{int(self.ratio * 100):3d}%   q quit   t contents "
        fill = max(0, self.size.width - len(left) - len(right))
        return Text(left + " " * fill + right)

    def set_ratio(self, ratio: float) -> None:
        self.ratio = ratio
        self.refresh()
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
    Markdown { padding: 1 3; width: 1fr; max-width: 96; }
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

    def __init__(self, source: str, label: str) -> None:
        super().__init__()
        self.source = source
        self.label = label

    def compose(self) -> ComposeResult:
        yield MarkdownViewer(self.source, show_table_of_contents=False)
        yield Status(self.label)

    @property
    def viewer(self) -> MarkdownViewer:
        return self.query_one(MarkdownViewer)

    def report(self) -> None:
        viewer = self.viewer
        limit = viewer.max_scroll_y
        ratio = viewer.scroll_offset.y / limit if limit else 1.0
        self.query_one(Status).set_ratio(ratio)
        return

    def on_mount(self) -> None:
        self.report()
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
    source, label = read_source(argument)
    if not sys.stdin.isatty():
        sys.stdin = open("/dev/tty")
    Jkl(source, label).run()
    return
