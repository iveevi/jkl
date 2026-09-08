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
Code fences follow the same rule: `MarkdownFence` picks its highlight theme from
`App.native_ansi_color`, and under `ansi_color` it uses the ANSI theme, whose
sixteen colours come from the terminal.

That theme is `SYNTAX`, which the module installs over
`ANSIDarkHighlightTheme.STYLES`, since `MarkdownFence` looks the class up by name
inside the call and offers no hook to pass one in. It maps pygments tokens onto
the ANSI sixteen: keywords blue, strings green, functions cyan, types and class
names bright cyan, numbers magenta, comments bright black.

## Style

The look is flat and typographic. No block is boxed. Vertical rhythm comes from
margins, structure from colour and from left rails: `border-left: outer` on
fences and block quotes, `border-bottom: solid` under an h1 and on a horizontal
rule. Headings step h1 bright white, h2 blue, h3 cyan, and h4 down to h6 plain
bold, so the level is read from hue rather than from size.

Blocks take the full width of the terminal, less the document's own padding.

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

## Live reload

A timer started at mount polls the current document's mtime four times a second
and reparses it when it moves, keeping the scroll offset across the update so an
edit does not throw the reader back to the top. Polling a single stat is cheaper
than a dependency on an inotify library, and a pager only ever watches one file.

The timer is only started when the document came from a path, since there is
nothing to re-read for stdin. It follows the navigator rather than the file jkl
was opened on, so the document you are looking at is the one being watched. A
missing file is skipped rather than reported: a save that replaces the file
briefly leaves nothing at the path, and the next tick picks up the new one.

## Mermaid

`Fence` subclasses `MarkdownFence` and splits on the fence's info string: anything
but `mermaid` composes as Textual does, a `Label` of highlighted code, while a
mermaid fence composes a placeholder label and starts a threaded worker. The
worker calls `render()` and posts the result back, which either replaces the
label with a `textual_image` `Image` or writes the failure into it. `Document`
subclasses `Markdown` only to put `Fence` in `BLOCKS` under both fence tokens,
and `Viewer.compose` is overridden to build that document instead of a plain one.

`Fence.fit()` sizes the picture rather than letting the image widget size itself:
Textual's auto sizing stretches the image to the container and loses the aspect
ratio, so the cell box is computed from the PNG's own pixel dimensions over the
terminal's cell size, scaled down only when it is wider than the block. It runs
again on resize.

`render()` hashes the diagram source together with the renderer options and
returns the cached PNG under `~/.cache/jkl` when one exists. Otherwise it writes
the source and a puppeteer config into a temporary directory and runs `mmdc`, or
`npx --yes @mermaid-js/mermaid-cli` when `mmdc` is not installed, moving the
result into the cache only once the process has succeeded. The config sets the
diagram's font to CaskaydiaCove so the labels match the terminal's own type, so a cache entry is
never a half-written file. The puppeteer config passes `--no-sandbox`, without
which chrome refuses to launch on distributions that restrict unprivileged user
namespaces. Failures are reported as the first line of stderr mentioning an
error, since mermaid follows its message with a stack trace.

Being a worker rather than a blocking call is what keeps the pager usable: the
first `npx` run downloads a browser and takes minutes, and even a warm run is a
chrome launch. Live reload rebuilds blocks, so `_update_from_block` restores the
placeholder and redraws; the cache makes an unchanged diagram immediate.

## Maths

`typeset()` runs over the source before `Markdown` ever sees it, since markdown-it
otherwise eats the TeX: `\{`, `\}` and `\\` are consumed as markdown escapes, and
subscripts pair up as emphasis, so `$|\cdot|_\nu$ ... $|\bot_b|_\nu$` italicises
everything between the two spans.

It scans four delimiter pairs, `$$`, `\[`, `$` and `\(`. A display match becomes a
fence tagged `math`, which `Fence` draws exactly as it draws mermaid; an inline
match is converted to unicode by flatlatex and emitted as text. Fenced code blocks
are skipped whole and inline code spans are stepped over, so a `$` inside either is
left alone.

A single `$` is only maths when it looks like maths: no space just inside either
delimiter, and no digit just after the closing one, or `$4,650 and $4,680/oz`
reads as a span. A span flatlatex cannot convert, or converts only halfway, is
wrapped in backticks rather than emitted raw, which is what keeps the escapes and
the subscripts intact.

flatlatex is extended with `add_newcommand` for the commands it lacks, the order
theory ones among them, `\sqcap`, `\sqcup`, `\top`, `\bot` and the triangles, since
a document about lattices is mostly those. Font commands are defined as identity
and operator names such as `\log` are stripped to plain words by a regex first.

`\{`, `\}` and `\|` cannot be given a `newcommand`, so they are swapped for private
use characters before conversion and swapped back after. Left as they are,
flatlatex returns them with their backslashes still attached and the span is
rejected as unconverted; replaced with bare braces they would be read as grouping
and vanish.

Display maths goes through `latex` and `dvipng` at a fixed 300 DPI, cached under
`~/.cache/jkl` by a digest of the source and that resolution. A failure is
reported as the first `!` line of the latex log, since the rest is the file's own
trace. When `latex` or `dvipng` is missing, `Fence` falls back to composing the
block as ordinary highlighted code, so the TeX is still readable and still
unmangled.

DPI is a sharpness control and `fit()` is the size control: it scales the PNG by
`EM * cell.height / DPI`, so a formula's type is a fixed fraction of the
terminal's own, whatever the font size, and then pastes it onto a transparent
canvas whose dimensions are an exact multiple of the cell size. Without that
padding the terminal rescales each image to fill its cell box and the rounding
differs per image, so one formula's glyphs come out larger than the next one's and
none of them keep their aspect ratio. A formula wider than the block is scaled to
the block first. It runs again on resize, since the cell size can change.

## Scrolling

The bindings act on the viewer rather than on focus, since focus belongs to the
table of contents whenever it is open. `report()` recomputes the percentage in
the status line from `scroll_offset.y` over `max_scroll_y` after every movement.
