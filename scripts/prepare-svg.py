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
- If single-color, replaces that color with currentColor for theme inheritance
- Multi-color SVGs are left as-is
"""

import re
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated

import typer
from bs4 import BeautifulSoup
from svgpathtools import svg2paths2


def _trim_viewbox(soup: BeautifulSoup) -> None:
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


def _collect_colors(soup: BeautifulSoup) -> set[str]:
    """Collect all unique fill/stroke colors used in the SVG (inline + CSS blocks)."""
    colors: set[str] = set()
    skip = {"none", "currentcolor", "inherit", "transparent"}

    # Colors from inline attributes
    for tag in soup.find_all(True):
        for attr in ("fill", "stroke"):
            val = tag.get(attr)
            if isinstance(val, str):
                val = val.strip().lower()
                if val and val not in skip:
                    colors.add(val)

        style = tag.get("style")
        if isinstance(style, str):
            for prop in ("fill", "stroke"):
                for part in style.split(";"):
                    part = part.strip()
                    if part.lower().startswith(f"{prop}:"):
                        color = part.split(":", 1)[1].strip().lower()
                        if color and color not in skip:
                            colors.add(color)

    # Colors from <style> CSS blocks
    for style_tag in soup.find_all("style"):
        if style_tag.string:
            for match in re.findall(r"(?:fill|stroke)\s*:\s*([^;}\s]+)", style_tag.string):
                color = match.strip().lower()
                if color and color not in skip:
                    colors.add(color)

    return colors


def _replace_fills(soup: BeautifulSoup) -> None:
    """If single-color SVG, replace that color with currentColor. Multi-color SVGs are left as-is."""
    colors = _collect_colors(soup)

    if not colors:
        return
    if len(colors) > 1:
        typer.echo(f"Multi-color SVG ({len(colors)} colors: {', '.join(sorted(colors))}), skipping recolor")
        return

    target = colors.pop()
    typer.echo(f"Single-color SVG, replacing {target} with currentColor")

    for tag in soup.find_all(True):
        for attr in ("fill", "stroke"):
            val = tag.get(attr)
            if isinstance(val, str) and val.strip().lower() == target:
                tag[attr] = "currentColor"

        style = tag.get("style")
        if isinstance(style, str):
            for prop in ("fill", "stroke"):
                style = style.replace(f"{prop}:{target}", f"{prop}:currentColor")
                style = style.replace(f"{prop}: {target}", f"{prop}:currentColor")
            tag["style"] = style

    # Replace in <style> CSS blocks
    for style_tag in soup.find_all("style"):
        if style_tag.string and target in style_tag.string.lower():
            style_tag.string = re.sub(
                re.escape(target), "currentColor", style_tag.string, flags=re.IGNORECASE
            )


def main(
    svg: Path,
    output_dir: Annotated[Path, typer.Argument(help="Output directory")],
    name: Annotated[str | None, typer.Option(help="Logo name (defaults to input filename stem)")] = None,
):
    """Prepare an SVG logo: trim whitespace and replace black fills with currentColor."""
    if not svg.exists():
        typer.echo(f"Error: {svg} not found", err=True)
        raise typer.Exit(1)

    logo_name = name or svg.stem
    dest = output_dir / f"{logo_name}.svg"

    if dest.exists():
        typer.echo(f"Error: {dest} already exists", err=True)
        raise typer.Exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    soup = BeautifulSoup(svg.read_text(), "xml")

    _trim_viewbox(soup)
    _replace_fills(soup)

    dest.write_text(str(soup))
    typer.echo(f"Done: {dest}")


if __name__ == "__main__":
    typer.run(main)
