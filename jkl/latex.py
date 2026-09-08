import hashlib
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import flatlatex
from PIL import Image as Picture

from .mermaid import CACHE

DOCUMENT = r"""\documentclass[preview,border=2pt]{standalone}
\usepackage{amsmath,amssymb}
\begin{document}
$\displaystyle %s$
\end{document}
"""

DPI = 300
EM = 6.8
FOREGROUND = "rgb 1 1 1"
TIMEOUT = 20

OPERATORS = re.compile(
    r"\\(log|ln|exp|sin|cos|tan|arcsin|arccos|arctan|sinh|cosh|tanh|max|min|"
    r"sup|inf|lim|arg|det|dim|deg|gcd|mod|Pr)\b"
)

ALIASES = (
    r"\newcommand{\to}{\rightarrow}",
    r"\newcommand{\gets}{\leftarrow}",
    r"\newcommand{\le}{\leq}",
    r"\newcommand{\ge}{\geq}",
    r"\newcommand{\ne}{\neq}",
    r"\newcommand{\implies}{\Rightarrow}",
    r"\newcommand{\iff}{\Leftrightarrow}",
    r"\newcommand{\ldots}{\dots}",
    r"\newcommand{\langle}{⟨}",
    r"\newcommand{\rangle}{⟩}",
    r"\newcommand{\deg}{deg}",
    r"\newcommand{\text}[1]{#1}",
    r"\newcommand{\textrm}[1]{#1}",
    r"\newcommand{\textbf}[1]{#1}",
    r"\newcommand{\textit}[1]{#1}",
    r"\newcommand{\mathrm}[1]{#1}",
    r"\newcommand{\mathsf}[1]{#1}",
    r"\newcommand{\mathit}[1]{#1}",
    r"\newcommand{\mathbf}[1]{#1}",
    r"\newcommand{\operatorname}[1]{#1}",
    r"\newcommand{\top}{⊤}",
    r"\newcommand{\bot}{⊥}",
    r"\newcommand{\coprod}{∐}",
    r"\newcommand{\displaystyle}{}",
    r"\newcommand{\vartriangle}{△}",
    r"\newcommand{\triangledown}{▽}",
    r"\newcommand{\square}{□}",
    r"\newcommand{\sqcap}{⊓}",
    r"\newcommand{\sqcup}{⊔}",
    r"\newcommand{\sqsubseteq}{⊑}",
    r"\newcommand{\sqsupseteq}{⊒}",
    r"\newcommand{\rightharpoonup}{⇀}",
    r"\newcommand{\bigsqcup}{⨆}",
    r"\newcommand{\bigsqcap}{⨅}",
    r"\newcommand{\hookrightarrow}{↪}",
    r"\newcommand{\mapsto}{↦}",
    r"\newcommand{\emptyset}{∅}",
    r"\newcommand{\setminus}{∖}",
    r"\newcommand{\colon}{:}",
    r"\newcommand{\quad}{ }",
    r"\newcommand{\qquad}{  }",
)

LITERALS = (("\\{", "\ue000", "{"), ("\\}", "\ue001", "}"), ("\\|", "\ue002", "|"))

CONVERTER = flatlatex.converter()

for alias in ALIASES:
    CONVERTER.add_newcommand(alias)


def available() -> bool:
    return bool(shutil.which("latex") and shutil.which("dvipng"))


def inline(source: str) -> Optional[str]:
    text = OPERATORS.sub(r"\1", source)
    for escape, holder, _ in LITERALS:
        text = text.replace(escape, holder)
    try:
        text = CONVERTER.convert(text)
    except Exception:
        return None
    if "\\" in text:
        return None
    for _, holder, literal in LITERALS:
        text = text.replace(holder, literal)
    return text.strip() or None


def digest(source: str) -> str:
    seed = "\0".join([source, f"{DPI}"])
    return hashlib.sha256(seed.encode()).hexdigest()[:32]


def fit(path: Path, cell: Tuple[int, int], limit: int) -> Tuple[Path, int, int]:
    picture = Picture.open(path)
    factor = EM * cell[1] / DPI
    width = max(1, round(picture.width * factor))
    height = max(1, round(picture.height * factor))
    columns = max(1, -(-width // cell[0]))
    if limit and columns > limit:
        width = limit * cell[0]
        height = max(1, round(picture.height * width / picture.width))
        columns = limit
    rows = max(1, -(-height // cell[1]))
    target = path.with_name(f"{path.stem}-{columns}x{rows}-{cell[0]}x{cell[1]}.png")
    if not target.is_file():
        canvas = Picture.new("RGBA", (columns * cell[0], rows * cell[1]), (0, 0, 0, 0))
        scaled = picture.resize((width, height), Picture.Resampling.LANCZOS)
        canvas.paste(scaled, ((canvas.width - width) // 2, (canvas.height - height) // 2))
        canvas.save(target)
    return target, columns, rows


def complaint(output: str) -> str:
    lines = [line.rstrip() for line in output.splitlines()]
    for index, line in enumerate(lines):
        if line.startswith("!"):
            return line.lstrip("! ").strip() or "latex failed"
        if index > 0 and line.startswith("l."):
            return lines[index - 1].strip() or "latex failed"
    return "latex failed"


def render(source: str, scale: float = 1.0) -> Tuple[Optional[Path], str]:
    target = CACHE / f"{digest(source)}.png"
    if target.is_file():
        return target, ""
    CACHE.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as scratch:
        work = Path(scratch)
        (work / "math.tex").write_text(DOCUMENT % source)
        try:
            done = subprocess.run(
                ["latex", "-interaction=nonstopmode", "-halt-on-error", "math.tex"],
                cwd=work,
                capture_output=True,
                text=True,
                timeout=TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            return None, "latex timed out"
        if done.returncode != 0 or not (work / "math.dvi").is_file():
            return None, complaint(done.stdout)
        draft = work / "math.png"
        try:
            done = subprocess.run(
                [
                    "dvipng",
                    "-q",
                    "-T",
                    "tight",
                    "-bg",
                    "Transparent",
                    "-fg",
                    FOREGROUND,
                    "-D",
                    str(DPI),
                    "-o",
                    str(draft),
                    "math.dvi",
                ],
                cwd=work,
                capture_output=True,
                text=True,
                timeout=TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            return None, "dvipng timed out"
        if done.returncode != 0 or not draft.is_file():
            return None, "dvipng failed"
        shutil.move(draft, target)
    return target, ""


MATH = "math"

DELIMITERS = (("$$", "$$"), ("\\[", "\\]"), ("$", "$"), ("\\(", "\\)"))

DISPLAY = ("$$", "\\[")

FENCE = re.compile(r"^[ \t]*(`{3,}|~{3,}).*$", re.M)

TICKS = re.compile(r"`+")


def spans(text: str, index: int, close: int) -> bool:
    inner = text[index + 1 : close]
    if not inner or inner[0].isspace() or inner[-1].isspace():
        return False
    return not text[close + 1 : close + 2].isdigit()


def opening(text: str, index: int) -> Optional[Tuple[str, str]]:
    for start, end in DELIMITERS:
        if text.startswith(start, index):
            return start, end
    return None


def block(source: str) -> str:
    return f"\n```{MATH}\n{source.strip()}\n```\n"


def guard(source: str) -> str:
    text = inline(source)
    if text is not None:
        return text
    ticks = max((len(run) for run in TICKS.findall(source)), default=0)
    seal = "`" * (ticks + 1)
    pad = " " if source.startswith("`") or source.endswith("`") else ""
    return f"{seal}{pad}{source}{pad}{seal}"


def convert(text: str) -> str:
    out = []
    index = 0
    while index < len(text):
        character = text[index]
        if character == "`":
            rest = text[index:]
            run = len(rest) - len(rest.lstrip("`"))
            seal = text.find("`" * run, index + run)
            while seal != -1 and text[seal + run : seal + run + 1] == "`":
                seal = text.find("`" * run, seal + run + 1)
            if seal != -1:
                out.append(text[index : seal + run])
                index = seal + run
                continue
        pair = opening(text, index)
        if pair is None:
            out.append(character)
            index += 1
            continue
        start, end = pair
        close = text.find(end, index + len(start))
        if close == -1:
            out.append(character)
            index += 1
            continue
        if start == "$" and not spans(text, index, close):
            out.append(character)
            index += 1
            continue
        source = text[index + len(start) : close]
        out.append(block(source) if start in DISPLAY else guard(source))
        index = close + len(end)
    return "".join(out)


def typeset(document: str) -> str:
    out = []
    index = 0
    for match in FENCE.finditer(document):
        if match.start() < index:
            continue
        seal = re.compile(rf"^[ \t]*{match.group(1)[0]}{{{len(match.group(1))},}}[ \t]*$", re.M)
        end = seal.search(document, match.end())
        stop = end.end() if end else len(document)
        out.append(convert(document[index : match.start()]))
        out.append(document[match.start() : stop])
        index = stop
    out.append(convert(document[index:]))
    return "".join(out)
