# /// script
# dependencies = [
#   "typer",
#   "beautifulsoup4",
#   "lxml",
#   "svgpathtools",
# ]
# ///

"""Prepare a single-color SVG logo for the carousel.

- Trims whitespace by recalculating the viewBox to fit all paths/shapes
- Replaces black fills with currentColor for theme color inheritance
"""

from pathlib import Path
from tempfile import NamedTemporaryFile

import typer
from bs4 import BeautifulSoup
from svgpathtools import svg2paths2


def _trim_viewbox(soup: BeautifulSoup, svg_path: Path) -> None:
    """Adjust the SVG viewBox to tightly fit all paths and shapes."""
    svg_tag = soup.find("svg")
    if not svg_tag:
        return

    # svgpathtools needs a file; write a temp copy with currentColor replaced
    raw = str(soup).replace("currentColor", "#000000")
    with NamedTemporaryFile(mode="w", suffix=".svg", delete=False) as f:
        f.write(raw)
        tmp = Path(f.name)
    try:
        paths, attributes, _ = svg2paths2(str(tmp))
    finally:
        tmp.unlink(missing_ok=True)

    if not paths:
        typer.echo("Warning: no paths found in SVG, skipping trim", err=True)
        return

    # Compute bounding box across all paths
    xmin, xmax, ymin, ymax = float("inf"), float("-inf"), float("inf"), float("-inf")
    for path, attr in zip(paths, attributes):
        if not path:
            continue
        px_min, px_max, py_min, py_max = path.bbox()
        # Expand by half stroke-width if present
        sw = 0.0
        stroke_w = attr.get("stroke-width", "")
        if stroke_w:
            try:
                sw = float(stroke_w.replace("px", "")) / 2
            except ValueError:
                pass
        xmin = min(xmin, px_min - sw)
        xmax = max(xmax, px_max + sw)
        ymin = min(ymin, py_min - sw)
        ymax = max(ymax, py_max + sw)

    if xmin == float("inf"):
        typer.echo("Warning: all paths are empty, skipping trim", err=True)
        return

    w = xmax - xmin
    h = ymax - ymin

    # Tiny padding to avoid clipping at edges
    pad = max(w, h) * 0.005
    xmin -= pad
    ymin -= pad
    w += pad * 2
    h += pad * 2

    svg_tag["viewBox"] = f"{xmin:.2f} {ymin:.2f} {w:.2f} {h:.2f}"


def _replace_fills(soup: BeautifulSoup) -> None:
    """Replace black fills and strokes with currentColor."""
    black_values = {"#000", "#000000", "black"}

    for tag in soup.find_all(True):
        for attr in ("fill", "stroke"):
            val = tag.get(attr)
            if isinstance(val, str) and val.strip().lower() in black_values:
                tag[attr] = "currentColor"

        style = tag.get("style")
        if isinstance(style, str):
            for prop in ("fill", "stroke"):
                for black in black_values:
                    style = style.replace(f"{prop}:{black}", f"{prop}:currentColor")
                    style = style.replace(f"{prop}: {black}", f"{prop}:currentColor")
            tag["style"] = style


def main(svg: Path, output: Path | None = None, no_trim: bool = False, no_recolor: bool = False):
    """Prepare an SVG logo: trim whitespace and replace black fills with currentColor."""
    if not svg.exists():
        typer.echo(f"Error: {svg} not found", err=True)
        raise typer.Exit(1)

    soup = BeautifulSoup(svg.read_text(), "xml")

    if not no_trim:
        _trim_viewbox(soup, svg)

    if not no_recolor:
        _replace_fills(soup)

    dest = output or svg
    dest.write_text(str(soup))
    typer.echo(f"Done: {dest}")


if __name__ == "__main__":
    typer.run(main)
