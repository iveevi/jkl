# jkl

A markdown pager for the terminal, built on Textual.

```
jkl README.md
cat README.md | jkl
```

| key               | action             |
| ----------------- | ------------------ |
| `j` `k`           | line down, line up |
| `ctrl+d` `ctrl+u` | half page          |
| `space`           | half page down     |
| `g` `G`           | top, bottom        |
| `t`               | table of contents  |
| `cmd+←` `cmd+→`   | back, forward      |
| `b`               | back               |
| `q`               | quit               |

Links to other files are followed in place, relative to the document being read,
and the history walks like a browser's. A link with an `http`, `https`, or
`mailto` scheme opens in the browser instead.

The document reloads by itself when the file changes on disk, keeping your place.

A ```` ```mermaid ```` fence is drawn as a picture rather than as code, so the
diagram appears inline in a terminal that speaks the kitty graphics or sixel
protocol. Drawing shells out to `mmdc`, or to `npx @mermaid-js/mermaid-cli` when
that is not installed, so node has to be on the path; results are cached under
`~/.cache/jkl`.

`cmd+←` reaches the app as `super+left`, which needs a terminal speaking the kitty
keyboard protocol; `alt+←` and `alt+→` are bound to the same actions for terminals
that do not.

Colours come from the terminal palette, so the document follows whatever theme
the terminal is set to. [docs/architecture.md](docs/architecture.md) describes the
layout and the style.
