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
| `b`               | back               |
| `q`               | quit               |

Links to other files are followed in place, relative to the document being read,
and `b` walks back. A link with an `http`, `https`, or `mailto` scheme opens in
the browser instead.

Colours come from the terminal palette, so the document follows whatever theme
the terminal is set to. [docs/architecture.md](docs/architecture.md) describes the
layout and the style.
