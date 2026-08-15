# Issues

## 1. A zero-width scrollbar collapses MarkdownViewer

`MarkdownViewer { scrollbar-size: 0 0; }` lays the document out at width 0 and
nothing renders; the status line is the only thing left on screen.
`scrollbar-size-vertical: 0` alone does the same. The viewer sets
`scrollbar-gutter: stable`, and a zero-sized bar appears to leave the gutter
arithmetic with no width to hand the child.

The workaround is `scrollbar-size-vertical: 1` with the bar's background set to
`ansi_default` and its handle to `ansi_bright_black`, which is a thin rule rather
than an absent one. Setting the size back to 0 to tidy this away brings the blank
screen straight back.

## 2. A message handler cannot be overridden by subclassing

`Viewer.go()` exists because overriding `_on_markdown_link_clicked` does not
replace the base handler. Textual dispatches a message to every class in the
MRO that defines a handler of that name, so both ran: the subclass navigated to
`docs/architecture.md` and then `MarkdownViewer`'s own handler navigated again
from there, asking for `docs/docs/architecture.md`. `message.stop()` does not help,
since it stops bubbling to other widgets and not dispatch within one.

The link logic therefore lives in `go()`, which is an ordinary method and does
override. Moving it back into a handler reintroduces the double navigation.

## 3. Clicking a link could crash the app

`MarkdownViewer.go()` resolves a relative link against `Navigator.location`,
which is `Path(".")` until the stack has something in it, so every relative link
resolved against the process's cwd rather than the document's directory, and
`Markdown.load` raised `FileNotFoundError` out of a worker and took the app down.
`Jkl.on_mount` seeds the navigator with the document's path, and `Viewer.go`
checks `is_file()` before loading and reports a miss in the status line.

`open_links` is off for the same reason: with it on, `Markdown`'s own handler
hands every href to `App.open_url`, so clicking a relative path opened a browser
as well as loading the file. `Viewer.go` calls `open_url` itself, only for an
`http`, `https`, or `mailto` scheme.
