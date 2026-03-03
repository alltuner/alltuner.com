# /// script
# dependencies = [
#   "typer",
#   "beautifulsoup4",
#   "lxml",
#   "svgpathtools",
# ]
# ///

"""Prepare an SVG logo for the carousel.

- Trims whitespace by recalculating the viewBox to fit all paths/shapes
- Single-color SVGs: replaces the color with currentColor
- Multi-color SVGs: replaces each color with currentColor at an opacity
  derived from its luminance, preserving relative brightness
"""

import re
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated

import typer
from bs4 import BeautifulSoup
from svgpathtools import Document as SvgDocument


def _trim_viewbox(soup: BeautifulSoup, original_text: str) -> None:
    """Adjust the SVG viewBox to tightly fit all paths and shapes."""
    svg_tag = soup.find("svg")
    if not svg_tag:
        return

    # svgpathtools needs a file; use the original file text (not str(soup))
    # because BeautifulSoup's XML parser may namespace <svg> as <svg:svg>.
    raw = original_text.replace("currentColor", "#000000")
    with NamedTemporaryFile(mode="w", suffix=".svg", delete=False) as f:
        f.write(raw)
        tmp = Path(f.name)
    try:
        # Document.paths_from_group returns paths with transforms already applied
        doc = SvgDocument(str(tmp))
        paths = doc.paths_from_group(doc.tree.getroot())
    finally:
        tmp.unlink(missing_ok=True)

    if not paths:
        typer.echo("Warning: no paths found in SVG, skipping trim", err=True)
        return

    # Compute bounding box across all transformed paths
    xmin, xmax, ymin, ymax = float("inf"), float("-inf"), float("inf"), float("-inf")
    for path in paths:
        if not path:
            continue
        px_min, px_max, py_min, py_max = path.bbox()
        xmin = min(xmin, px_min)
        xmax = max(xmax, px_max)
        ymin = min(ymin, py_min)
        ymax = max(ymax, py_max)

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


def _color_to_opacity(color: str) -> float:
    """Convert a hex color to an opacity value (darker → higher opacity)."""
    color = color.strip().lower()
    if color.startswith("#"):
        h = color[1:]
        if len(h) == 3:
            h = h[0] * 2 + h[1] * 2 + h[2] * 2
        if len(h) == 6:
            try:
                r = int(h[0:2], 16) / 255
                g = int(h[2:4], 16) / 255
                b = int(h[4:6], 16) / 255
                luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
                return round(1 - luminance, 3)
            except ValueError:
                pass
    return 1.0


def _parse_style(style: str) -> list[tuple[str, str]]:
    """Parse a CSS style string into an ordered list of (property, value) pairs."""
    props = []
    for part in style.split(";"):
        part = part.strip()
        if ":" in part:
            key, val = part.split(":", 1)
            props.append((key.strip(), val.strip()))
    return props


def _replace_fills(soup: BeautifulSoup) -> None:
    """Replace fill/stroke colors with currentColor.

    Single-color: simple replacement.
    Multi-color: each color maps to currentColor at an opacity derived from
    its luminance, preserving relative brightness.
    """
    colors = _collect_colors(soup)
    if not colors:
        return

    # Build opacity map: color → opacity (None means no opacity attr needed)
    opacity_map: dict[str, float | None]
    if len(colors) == 1:
        target = colors.pop()
        typer.echo(f"Single-color SVG, replacing {target} with currentColor")
        opacity_map = {target: None}
    else:
        opacity_map = {}
        typer.echo(f"Multi-color SVG ({len(colors)} colors), mapping to currentColor:")
        for c in sorted(colors):
            op = _color_to_opacity(c)
            opacity_map[c] = op
            typer.echo(f"  {c} → opacity {op}")

    # --- Inline fill/stroke attributes ---
    for tag in soup.find_all(True):
        for attr, op_attr in [("fill", "fill-opacity"), ("stroke", "stroke-opacity")]:
            val = tag.get(attr)
            if isinstance(val, str) and val.strip().lower() in opacity_map:
                opacity = opacity_map[val.strip().lower()]
                tag[attr] = "currentColor"
                if opacity is not None:
                    tag[op_attr] = str(opacity)

        # --- Inline style attributes ---
        style = tag.get("style")
        if not isinstance(style, str):
            continue

        props = _parse_style(style)
        opacity_updates: dict[str, float] = {}
        new_props: list[tuple[str, str]] = []

        for key, val in props:
            kl = key.strip().lower()
            vl = val.strip().lower()
            if kl in ("fill", "stroke") and vl in opacity_map:
                opacity = opacity_map[vl]
                new_props.append((key, "currentColor"))
                if opacity is not None:
                    opacity_updates[f"{kl}-opacity"] = opacity
            elif kl in opacity_updates:
                # Overwrite existing fill-opacity / stroke-opacity
                new_props.append((key, str(opacity_updates.pop(kl))))
            else:
                new_props.append((key, val))

        # Append opacity props that weren't already present
        for op_key, op_val in opacity_updates.items():
            new_props.append((op_key, str(op_val)))

        tag["style"] = ";".join(f"{k}:{v}" for k, v in new_props)

    # --- <style> CSS blocks ---
    for style_tag in soup.find_all("style"):
        if not style_tag.string:
            continue
        css = style_tag.string
        for color, opacity in opacity_map.items():
            for prop, op_prop in [("fill", "fill-opacity"), ("stroke", "stroke-opacity")]:
                if opacity is not None:
                    css = re.sub(
                        rf"({prop}\s*:\s*)" + re.escape(color),
                        rf"\1currentColor;{op_prop}:{opacity}",
                        css,
                        flags=re.IGNORECASE,
                    )
                else:
                    css = re.sub(
                        rf"({prop}\s*:\s*)" + re.escape(color),
                        r"\1currentColor",
                        css,
                        flags=re.IGNORECASE,
                    )
        style_tag.string = css


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

    original_text = svg.read_text()
    soup = BeautifulSoup(original_text, "xml")

    _trim_viewbox(soup, original_text)
    _replace_fills(soup)

    dest.write_text(str(soup))
    typer.echo(f"Done: {dest}")


if __name__ == "__main__":
    typer.run(main)
