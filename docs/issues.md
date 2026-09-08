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

## 4. Textual's ANSI highlight theme is misspelt

`SYNTAX` replaces `ANSIDarkHighlightTheme.STYLES` wholesale, which is what
`MarkdownFence` reaches for under `ansi_color`. Three of the entries in the
shipped table name colours that do not exist, so `Style.parse` throws on them and
the token ends up unstyled: `Token.String` is `ansi_greenb`,
`Token.Name.Attribute` is `ansi_yelllow`, and `Token.Name.Function.Magic` is
`ansi_blow`. String literals losing their colour is most of why highlighting
looked wrong.

The other half is the fallback. `highlight()` walks a token up its ancestors
looking for a style and gives up at the root, and whatever is left over is
painted with the `$text` design token, which resolves to `#ffffff`: a hard white
that ignores the terminal palette. Punctuation has no entry at all, so every
bracket and colon in a fence glared. `SYNTAX` maps the root `Token` itself, which
terminates that walk with `ansi_default` and leaves nothing to fall through.

A tidy-up that drops the root `Token` entry, or the explicit `Token.Punctuation`,
brings the white back.

## 5. flatlatex converts `\bot` to ⊤

`converter().convert(r"\bot")` returns ⊤ and leaves `\top` unconverted, so every
bottom in a lattice document came out as a top: not a span that fails and falls
back to raw TeX, but one that succeeds and says the opposite of what it means.
`ALIASES` defines both symbols explicitly, which overrides the shipped table.

Subscripts have no such fix. flatlatex writes a subscript with no unicode form as
a bracket, so `$P_b$` is `P[b]`, since unicode has no latin letter b subscript.
Display maths is the way out of it: `$$` goes through real latex.
