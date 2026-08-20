import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

PACKAGE = "@mermaid-js/mermaid-cli"
THEME = "dark"
BACKGROUND = "transparent"
SCALE = "1"
PUPPETEER = '{"args": ["--no-sandbox"]}'
FONT = "CaskaydiaCove Nerd Font"
CONFIG = json.dumps({"theme": THEME, "themeVariables": {"fontFamily": FONT}})
TIMEOUT = 120

CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "jkl"


def digest(code: str) -> str:
    seed = "\0".join([code, CONFIG, BACKGROUND, SCALE])
    return hashlib.sha256(seed.encode()).hexdigest()[:32]


def command(
    source: Path, target: Path, settings: Path, config: Path
) -> Optional[List[str]]:
    options = [
        "-i",
        str(source),
        "-o",
        str(target),
        "-c",
        str(config),
        "-b",
        BACKGROUND,
        "-s",
        SCALE,
        "-p",
        str(settings),
    ]
    binary = shutil.which("mmdc")
    if binary:
        return [binary] + options
    npx = shutil.which("npx")
    if npx:
        return [npx, "--yes", PACKAGE] + options
    return None


def complaint(output: str) -> str:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    faults = [line for line in lines if "error" in line.lower()]
    return faults[0] if faults else "mermaid failed"


def render(code: str) -> Tuple[Optional[Path], str]:
    target = CACHE / f"{digest(code)}.png"
    if target.is_file():
        return target, ""
    CACHE.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as scratch:
        source = Path(scratch) / "diagram.mmd"
        source.write_text(code)
        draft = Path(scratch) / "diagram.png"
        settings = Path(scratch) / "puppeteer.json"
        settings.write_text(PUPPETEER)
        config = Path(scratch) / "config.json"
        config.write_text(CONFIG)
        line = command(source, draft, settings, config)
        if line is None:
            return None, "mermaid needs mmdc or npx on PATH"
        try:
            done = subprocess.run(line, capture_output=True, text=True, timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            return None, "mermaid timed out"
        if done.returncode != 0 or not draft.is_file():
            return None, complaint(done.stderr)
        shutil.move(draft, target)
    return target, ""
