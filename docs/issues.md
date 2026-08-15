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
