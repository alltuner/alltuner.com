# /// script
# dependencies = [
#   "typer",
#   "pillow",
#   "httpx",
# ]
# ///

"""Prepare a PNG logo for the carousel.

- Removes background color (auto-detected from image borders)
- Trims whitespace around the logo
- Resizes to target height (default 192px = 3x retina for h-16/64px CSS)
- Generates light and dark variants (recolors non-transparent pixels)
"""

from collections import Counter
from io import BytesIO
from pathlib import Path
from typing import Annotated
from urllib.parse import urlparse

import httpx
import typer
from PIL import Image


def _border_pixels(img: Image.Image) -> list[tuple[int, ...]]:
    """Sample pixels along the image border."""
    w, h = img.size
    pixels: list[tuple[int, ...]] = []
    for x in range(w):
        pixels.append(img.getpixel((x, 0)))
        pixels.append(img.getpixel((x, h - 1)))
    for y in range(h):
        pixels.append(img.getpixel((0, y)))
        pixels.append(img.getpixel((w - 1, y)))
    return pixels


def _has_transparent_background(img: Image.Image, threshold: float = 0.5) -> bool:
    """Check if the majority of border pixels are already transparent."""
    transparent = sum(1 for p in _border_pixels(img) if p[3] < 10)
    total = 2 * (img.width + img.height)
    return (transparent / total) >= threshold


def _detect_bg_color(img: Image.Image) -> tuple[int, ...]:
    """Detect background color by sampling border pixels."""
    border = _border_pixels(img)

    # Quantize to reduce near-identical colors (group within ±5 per channel)
    def quantize(c: tuple[int, ...]) -> tuple[int, ...]:
        return tuple(round(v / 5) * 5 for v in c[:3])

    counts = Counter(quantize(p) for p in border)
    dominant = counts.most_common(1)[0][0]
    return dominant


def _remove_background(img: Image.Image, tolerance: int) -> Image.Image:
    """Replace background color with transparency."""
    img = img.convert("RGBA")
    bg_rgb = _detect_bg_color(img)

    typer.echo(f"Detected background color: RGB{bg_rgb}")

    pixels = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if all(abs(c1 - c2) <= tolerance for c1, c2 in zip((r, g, b), bg_rgb)):
                pixels[x, y] = (0, 0, 0, 0)

    return img


def _recolor(img: Image.Image, color: tuple[int, int, int]) -> Image.Image:
    """Recolor all non-transparent pixels to a single color, preserving alpha."""
    img = img.copy()
    pixels = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            _, _, _, a = pixels[x, y]
            if a > 0:
                pixels[x, y] = (*color, a)
    return img


def _trim(img: Image.Image) -> Image.Image:
    """Crop to the bounding box of non-transparent pixels."""
    bbox = img.split()[3].getbbox()  # alpha channel bounds
    if bbox:
        return img.crop(bbox)
    return img


def _parse_hex(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _default_name(source: str) -> str:
    """Derive a logo name from a file path or URL."""
    if source.startswith(("http://", "https://")):
        filename = Path(urlparse(source).path).stem
    else:
        filename = Path(source).stem
    return filename


def main(
    source: Annotated[str, typer.Argument(help="Input PNG file path or URL")],
    output_dir: Annotated[Path, typer.Argument(help="Output directory")],
    name: Annotated[str | None, typer.Option(help="Logo name (defaults to input filename stem)")] = None,
    height: Annotated[int, typer.Option(help="Target height in pixels")] = 192,
    tolerance: Annotated[int, typer.Option(help="Color tolerance for background removal (0-255)")] = 30,
    bg_color: Annotated[str | None, typer.Option(help="Background color to remove as hex (e.g. '#ffffff'), auto-detects if omitted")] = None,
    light_color: Annotated[str, typer.Option(help="Hex color for light variant (dark logo on light bg)")] = "#2c2826",
    dark_color: Annotated[str, typer.Option(help="Hex color for dark variant (light logo on dark bg)")] = "#f0ece9",
    no_variants: Annotated[bool, typer.Option(help="Skip generating light/dark variants")] = False,
):
    """Prepare a PNG logo: remove background, trim whitespace, resize, generate variants."""
    logo_name = name or _default_name(source)

    # Check outputs don't already exist
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / f"{logo_name}.png"
    light_path = output_dir / f"{logo_name}-light.png"
    dark_path = output_dir / f"{logo_name}-dark.png"

    paths_to_check = [dest]
    if not no_variants:
        paths_to_check += [light_path, dark_path]
    existing = [p for p in paths_to_check if p.exists()]
    if existing:
        for p in existing:
            typer.echo(f"Error: {p} already exists", err=True)
        raise typer.Exit(1)

    # Load from URL or file
    if source.startswith(("http://", "https://")):
        typer.echo(f"Downloading {source}...")
        resp = httpx.get(source, follow_redirects=True)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content))
    else:
        path = Path(source)
        if not path.exists():
            typer.echo(f"Error: {path} not found", err=True)
            raise typer.Exit(1)
        img = Image.open(path)

    img = img.convert("RGBA")
    typer.echo(f"Original size: {img.width}x{img.height}")

    if _has_transparent_background(img):
        typer.echo("Background is already transparent, skipping removal.")
    elif bg_color:
        bg_rgb = _parse_hex(bg_color)
        typer.echo(f"Using specified background color: RGB{bg_rgb}")
        pixels = img.load()
        w, h = img.size
        for y in range(h):
            for x in range(w):
                r, g, b, a = pixels[x, y]
                if all(abs(c1 - c2) <= tolerance for c1, c2 in zip((r, g, b), bg_rgb)):
                    pixels[x, y] = (0, 0, 0, 0)
    else:
        img = _remove_background(img, tolerance)

    img = _trim(img)
    typer.echo(f"After trim: {img.width}x{img.height}")

    aspect = img.width / img.height
    new_w = round(height * aspect)
    img = img.resize((new_w, height), Image.LANCZOS)
    typer.echo(f"Resized to: {new_w}x{height}")

    img.save(dest, "PNG", optimize=True)
    typer.echo(f"Done: {dest}")

    if not no_variants:
        light = _recolor(img, _parse_hex(light_color))
        light.save(light_path, "PNG", optimize=True)
        typer.echo(f"Light variant: {light_path}")

        dark = _recolor(img, _parse_hex(dark_color))
        dark.save(dark_path, "PNG", optimize=True)
        typer.echo(f"Dark variant: {dark_path}")


if __name__ == "__main__":
    typer.run(main)
