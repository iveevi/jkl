# Architecture

jkl is a Textual application that renders one markdown document and lets you page
through it. There is no server, no watcher, and no state beyond the source string:
`main()` reads the document, hands it to the app, and runs.

## Source

`read_source()` takes the first argument as a path, or reads stdin when no
argument is given. When the document arrived over a pipe, stdin is exhausted and
is no longer a terminal, so `main()` reopens `/dev/tty` and rebinds `sys.stdin`
before starting the app. Textual reads keys from `sys.stdin`, so without this a
piped document renders and then rejects every keystroke.

## Widgets

The screen is a `MarkdownViewer` docked above a one-line `Status`. The viewer is
Textual's own composite: a `MarkdownTableOfContents` docked left plus a `Markdown`
document, inside a `VerticalScroll`. Its `show_table_of_contents` reactive is the
whole of the `t` binding.

`ansi_color` is set on the app and every colour in the CSS is an `ansi_*` name, so
the palette is whatever the terminal is themed with rather than a Textual theme.
This is also why code fences look right: `MarkdownFence` picks its highlight theme
from `App.native_ansi_color`, and under `ansi_color` it uses the ANSI theme whose
sixteen colours come from the terminal.

## Style

The look is flat and typographic. No block is boxed. Vertical rhythm comes from
margins, structure from colour and from left rails: `border-left: outer` on
fences and block quotes, `border-bottom: solid` under an h1 and on a horizontal
rule. Headings step h1 bright white, h2 blue, h3 cyan, and h4 down to h6 plain
bold, so the level is read from hue rather than from size.

`Markdown` carries `max-width: 96` so a wide terminal gives margins instead of
long lines.

## Links

`Viewer` subclasses `MarkdownViewer` for one method, `go()`, which every link
click reaches. It splits three ways: a remote scheme goes to `App.open_url`, a
bare anchor goes to `Markdown.goto_anchor`, and anything else is a file resolved
against the current document and loaded only if it exists. `open_links` is off,
so `Markdown` does not also route the href to a browser.

The navigator is a stack of paths, seeded at mount with the document's own path;
without that seed a relative link resolves against the process's cwd. It is a
browser history rather than a stack of one direction: `back` and `forward` move an
index within it, so `super+left` and `super+right` walk both ways over the same
list. Textual reports cmd as `super` only when the terminal speaks the kitty
keyboard protocol, so `alt+left` and `alt+right` are bound alongside.

## Scrolling

The bindings act on the viewer rather than on focus, since focus belongs to the
table of contents whenever it is open. `report()` recomputes the percentage in
the status line from `scroll_offset.y` over `max_scroll_y` after every movement.
