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
| `q`               | quit               |

Colours come from the terminal palette, so the document follows whatever theme
the terminal is set to. [docs/architecture.md](docs/architecture.md) describes the
layout and the style.
