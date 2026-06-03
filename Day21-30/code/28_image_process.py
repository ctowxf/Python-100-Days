"""
Day 28 - Python Image Processing with Pillow
=============================================

Demonstrates image manipulation, filters, drawing, and enterprise utilities
(batch resizer, watermark tool) using the Pillow library.

Python Pillow vs C++ OpenCV
---------------------------
Pillow (PIL fork):
  - Pure Python, easy to install, great for basic image manipulation
  - Supports JPEG, PNG, BMP, GIF, TIFF, WebP and more
  - Ideal for batch processing, thumbnails, watermarks, format conversion
  - Limited computer-vision capabilities

OpenCV (C++ / Python bindings):
  - High-performance C++ library with Python bindings (cv2)
  - Real-time video processing, feature detection, object tracking
  - GPU acceleration via CUDA for heavy workloads
  - Steeper learning curve, heavier dependency

Rule of thumb: use Pillow for everyday image editing and batch tasks;
switch to OpenCV when you need real-time processing, object detection,
or advanced computer-vision algorithms.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
Size = Tuple[int, int]
Color = Tuple[int, int, int] | Tuple[int, int, int, int]
Box = Tuple[int, int, int, int]


# ---------------------------------------------------------------------------
# Basic image operations
# ---------------------------------------------------------------------------

def image_info(path: str | Path) -> dict[str, object]:
    """Return basic metadata for an image file.

    Args:
        path: Path to the image file.

    Returns:
        A dict with keys: format, size, mode, filename.
    """
    img: Image.Image = Image.open(path)
    return {
        "format": img.format,
        "size": img.size,
        "mode": img.mode,
        "filename": str(path),
    }


def crop_image(
    source: str | Path,
    box: Box,
    dest: Optional[str | Path] = None,
) -> Image.Image:
    """Crop an image to the given bounding box.

    Args:
        source: Path to the source image.
        box: A 4-tuple (left, upper, right, lower).
        dest: Optional path to save the cropped result.

    Returns:
        The cropped Image object.
    """
    img: Image.Image = Image.open(source)
    cropped: Image.Image = img.crop(box)
    if dest:
        cropped.save(dest)
    return cropped


def resize_image(
    source: str | Path,
    size: Size,
    dest: Optional[str | Path] = None,
    keep_aspect: bool = True,
) -> Image.Image:
    """Resize an image, optionally preserving aspect ratio via thumbnail.

    Args:
        source: Path to the source image.
        size: Target (width, height).
        dest: Optional path to save the resized result.
        keep_aspect: If True, shrink to fit inside *size* while keeping
            the aspect ratio (like Image.thumbnail).  If False, force
            the exact dimensions (like Image.resize).

    Returns:
        The resized Image object.
    """
    img: Image.Image = Image.open(source)
    if keep_aspect:
        img.thumbnail(size)
    else:
        img = img.resize(size)
    if dest:
        img.save(dest)
    return img


def rotate_image(
    source: str | Path,
    angle: float,
    dest: Optional[str | Path] = None,
) -> Image.Image:
    """Rotate an image by *angle* degrees (counter-clockwise).

    Args:
        source: Path to the source image.
        angle: Rotation angle in degrees.
        dest: Optional path to save the result.

    Returns:
        The rotated Image object.
    """
    img: Image.Image = Image.open(source)
    rotated: Image.Image = img.rotate(angle, expand=True)
    if dest:
        rotated.save(dest)
    return rotated


def flip_image(
    source: str | Path,
    horizontal: bool = True,
    dest: Optional[str | Path] = None,
) -> Image.Image:
    """Flip an image horizontally or vertically.

    Args:
        source: Path to the source image.
        horizontal: True for left-right flip, False for top-bottom flip.
        dest: Optional path to save the result.

    Returns:
        The flipped Image object.
    """
    img: Image.Image = Image.open(source)
    method = Image.FLIP_LEFT_RIGHT if horizontal else Image.FLIP_TOP_BOTTOM
    flipped: Image.Image = img.transpose(method)
    if dest:
        flipped.save(dest)
    return flipped


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

AVAILABLE_FILTERS: dict[str, ImageFilter.Filter] = {
    "blur": ImageFilter.BLUR,
    "contour": ImageFilter.CONTOUR,
    "detail": ImageFilter.DETAIL,
    "edge_enhance": ImageFilter.EDGE_ENHANCE,
    "edge_enhance_more": ImageFilter.EDGE_ENHANCE_MORE,
    "emboss": ImageFilter.EMBOSS,
    "find_edges": ImageFilter.FIND_EDGES,
    "sharpen": ImageFilter.SHARPEN,
    "smooth": ImageFilter.SMOOTH,
    "smooth_more": ImageFilter.SMOOTH_MORE,
}


def apply_filter(
    source: str | Path,
    filter_name: str,
    dest: Optional[str | Path] = None,
) -> Image.Image:
    """Apply a named Pillow filter to an image.

    Args:
        source: Path to the source image.
        filter_name: One of the keys in AVAILABLE_FILTERS.
        dest: Optional path to save the result.

    Returns:
        The filtered Image object.

    Raises:
        ValueError: If *filter_name* is not a recognised filter.
    """
    if filter_name not in AVAILABLE_FILTERS:
        raise ValueError(
            f"Unknown filter '{filter_name}'. "
            f"Choose from: {', '.join(AVAILABLE_FILTERS)}"
        )
    img: Image.Image = Image.open(source)
    filtered: Image.Image = img.filter(AVAILABLE_FILTERS[filter_name])
    if dest:
        filtered.save(dest)
    return filtered


# ---------------------------------------------------------------------------
# Drawing utilities
# ---------------------------------------------------------------------------

def draw_demo(
    width: int = 800,
    height: int = 600,
    dest: Optional[str | Path] = None,
    font_path: Optional[str | Path] = None,
) -> Image.Image:
    """Create a demo image with text, shapes, and lines.

    Mirrors the drawing example from the Day 28 lesson.

    Args:
        width: Canvas width in pixels.
        height: Canvas height in pixels.
        dest: Optional path to save the result.
        font_path: Path to a TrueType font file. Falls back to Pillow
            default if not provided or not found.

    Returns:
        The composed Image object.
    """
    import random

    def random_color() -> Color:
        return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    image: Image.Image = Image.new("RGB", (width, height), (255, 255, 255))
    drawer: ImageDraw.ImageDraw = ImageDraw.Draw(image)

    # -- text --
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont
    if font_path and Path(font_path).is_file():
        font = ImageFont.truetype(str(font_path), 32)
    else:
        font = ImageFont.load_default()
    drawer.text((width // 2 - 100, 50), "Hello, Pillow!", fill=(255, 0, 0), font=font)

    # -- diagonal lines --
    drawer.line((0, 0, width, height), fill=(0, 0, 255), width=2)
    drawer.line((width, 0, 0, height), fill=(0, 0, 255), width=2)

    # -- center rectangle --
    cx, cy = width // 2, height // 2
    drawer.rectangle(
        (cx - 60, cy - 60, cx + 60, cy + 60),
        outline=(255, 0, 0),
        width=2,
    )

    # -- four random-coloured ellipses --
    for i in range(4):
        left = 150 + i * 120
        top = 220
        right = 310 + i * 120
        bottom = 380
        drawer.ellipse((left, top, right, bottom), outline=random_color(), width=8)

    if dest:
        image.save(dest)
    return image


# ---------------------------------------------------------------------------
# Enterprise utility: batch image resizer
# ---------------------------------------------------------------------------

def batch_resize(
    src_dir: str | Path,
    dest_dir: str | Path,
    max_size: Size = (800, 800),
    output_format: Optional[str] = None,
    quality: int = 85,
) -> list[Path]:
    """Resize every image in *src_dir* and write results to *dest_dir*.

    Args:
        src_dir: Directory containing source images.
        dest_dir: Directory for resized images (created if missing).
        max_size: Maximum (width, height) -- aspect ratio is preserved.
        output_format: e.g. "JPEG", "PNG".  None keeps the original format.
        quality: JPEG/WebP quality (1-100).

    Returns:
        List of paths to the resized images.
    """
    src = Path(src_dir)
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    suffixes = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
    results: list[Path] = []

    for file in sorted(src.iterdir()):
        if file.suffix.lower() not in suffixes:
            continue
        img: Image.Image = Image.open(file)
        img.thumbnail(max_size)
        if img.mode == "RGBA" and output_format and output_format.upper() == "JPEG":
            img = img.convert("RGB")
        ext = (("." + output_format.lower()) if output_format else file.suffix)
        out_name = file.stem + ext
        out_path = dest / out_name
        save_kwargs: dict[str, object] = {}
        if output_format:
            save_kwargs["format"] = output_format
        if output_format and output_format.upper() in ("JPEG", "WEBP"):
            save_kwargs["quality"] = quality
        img.save(out_path, **save_kwargs)
        results.append(out_path)

    return results


# ---------------------------------------------------------------------------
# Enterprise utility: watermark tool
# ---------------------------------------------------------------------------

def add_watermark(
    source: str | Path,
    text: str = "CONFIDENTIAL",
    dest: Optional[str | Path] = None,
    opacity: int = 80,
    font_size: int = 36,
    color: Color = (255, 255, 255),
    tile: bool = True,
    font_path: Optional[str | Path] = None,
) -> Image.Image:
    """Overlay a text watermark on an image.

    When *tile* is True the watermark text is repeated diagonally across
    the entire image -- common for document/proposal protection.

    Args:
        source: Path to the source image.
        text: Watermark text string.
        dest: Optional path to save the watermarked image.
        opacity: Opacity of the watermark (0-255).
        font_size: Font size in points.
        color: RGB colour of the watermark text.
        tile: If True, tile the text across the image; otherwise place
            a single instance in the bottom-right corner.
        font_path: Optional path to a TrueType font file.

    Returns:
        The watermarked Image object.
    """
    base: Image.Image = Image.open(source).convert("RGBA")
    overlay: Image.Image = Image.new("RGBA", base.size, (0, 0, 0, 0))
    drawer: ImageDraw.ImageDraw = ImageDraw.Draw(overlay)

    font: ImageFont.FreeTypeFont | ImageFont.ImageFont
    if font_path and Path(font_path).is_file():
        font = ImageFont.truetype(str(font_path), font_size)
    else:
        font = ImageFont.load_default()

    fill = (*color, opacity)

    if tile:
        # Place watermark text diagonally across the image
        w, h = base.size
        # Estimate text bounding box for spacing
        bbox = drawer.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        step_x = tw + 120
        step_y = th + 120
        for y in range(-h, h * 2, step_y):
            for x in range(-w, w * 2, step_x):
                drawer.text((x, y), text, font=font, fill=fill)
    else:
        bbox = drawer.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        w, h = base.size
        margin = 20
        pos = (w - tw - margin, h - th - margin)
        drawer.text(pos, text, font=font, fill=fill)

    watermarked: Image.Image = Image.alpha_composite(base, overlay)
    if dest:
        watermarked.convert("RGB").save(dest)
    return watermarked


def batch_watermark(
    src_dir: str | Path,
    dest_dir: str | Path,
    text: str = "CONFIDENTIAL",
    **kwargs: object,
) -> list[Path]:
    """Apply a watermark to every image in *src_dir*.

    Args:
        src_dir: Directory containing source images.
        dest_dir: Directory for watermarked images (created if missing).
        text: Watermark text string.
        **kwargs: Forwarded to :func:`add_watermark` (opacity, font_size,
            color, tile, font_path).

    Returns:
        List of paths to the watermarked images.
    """
    src = Path(src_dir)
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    suffixes = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
    results: list[Path] = []

    for file in sorted(src.iterdir()):
        if file.suffix.lower() not in suffixes:
            continue
        out_path = dest / file.name
        add_watermark(file, text=text, dest=out_path, **kwargs)
        results.append(out_path)

    return results


# ---------------------------------------------------------------------------
# Helper: create a small sample image for demos
# ---------------------------------------------------------------------------

def _create_sample_image(path: Path, size: Size = (400, 300)) -> None:
    """Generate a simple gradient sample image for demonstration."""
    img: Image.Image = Image.new("RGB", size)
    pixels = img.load()
    if pixels is None:
        return
    w, h = size
    for y in range(h):
        for x in range(w):
            r = int(255 * x / w)
            g = int(255 * y / h)
            b = 128
            pixels[x, y] = (r, g, b)
    img.save(path)


# ---------------------------------------------------------------------------
# Main demonstration
# ---------------------------------------------------------------------------

def main() -> None:
    """Run interactive demonstrations of all image processing features."""
    # Create a working directory for demo outputs
    out_dir = Path(__file__).resolve().parent / "image_output"
    out_dir.mkdir(exist_ok=True)

    # Generate a sample image so the demo is self-contained
    sample: Path = out_dir / "sample.png"
    if not sample.exists():
        _create_sample_image(sample)
        print(f"[+] Created sample image: {sample}")

    # -- 1. Image info -------------------------------------------------------
    print("\n=== Image Info ===")
    info = image_info(sample)
    for k, v in info.items():
        print(f"  {k}: {v}")

    # -- 2. Crop -------------------------------------------------------------
    print("\n=== Crop ===")
    cropped = crop_image(sample, (50, 50, 250, 200), dest=out_dir / "cropped.png")
    print(f"  Cropped size: {cropped.size} -> saved to cropped.png")

    # -- 3. Resize -----------------------------------------------------------
    print("\n=== Resize (thumbnail) ===")
    resized = resize_image(sample, (128, 128), dest=out_dir / "resized.png")
    print(f"  Resized size: {resized.size} -> saved to resized.png")

    # -- 4. Rotate -----------------------------------------------------------
    print("\n=== Rotate 45 degrees ===")
    rotated = rotate_image(sample, 45, dest=out_dir / "rotated.png")
    print(f"  Rotated size: {rotated.size} -> saved to rotated.png")

    # -- 5. Flip -------------------------------------------------------------
    print("\n=== Flip (horizontal) ===")
    flipped = flip_image(sample, horizontal=True, dest=out_dir / "flipped.png")
    print(f"  Flipped size: {flipped.size} -> saved to flipped.png")

    # -- 6. Filters ----------------------------------------------------------
    print("\n=== Filters ===")
    for name in ("blur", "contour", "emboss", "sharpen", "find_edges"):
        filtered = apply_filter(sample, name, dest=out_dir / f"filter_{name}.png")
        print(f"  Applied '{name}' -> {filtered.size}")

    # -- 7. Drawing demo -----------------------------------------------------
    print("\n=== Drawing Demo ===")
    draw_demo(dest=out_dir / "draw_demo.png")
    print(f"  Saved draw_demo.png (800x600)")

    # -- 8. Watermark --------------------------------------------------------
    print("\n=== Watermark ===")
    watermarked = add_watermark(
        sample,
        text="DRAFT",
        dest=out_dir / "watermarked.png",
        opacity=100,
        font_size=28,
    )
    print(f"  Watermarked size: {watermarked.size} -> saved to watermarked.png")

    # -- 9. Batch resizer demo -----------------------------------------------
    print("\n=== Batch Resize (image_output/) ===")
    resized_files = batch_resize(out_dir, out_dir / "thumbs", max_size=(64, 64))
    print(f"  Resized {len(resized_files)} image(s) into thumbs/")

    # -- Summary -------------------------------------------------------------
    print(f"\nAll outputs saved to: {out_dir}")
    print("Done.")


if __name__ == "__main__":
    main()
