"""Thumbnail generation using AI image generation + text overlays."""

from pathlib import Path
from dataclasses import dataclass

from config.settings import settings
from src.utils.image_gen import generate_image


@dataclass
class ThumbnailResult:
    file_path: Path
    width: int
    height: int


def add_text_overlay(image_path: str | Path, output_path: str | Path,
                      title: str, subtitle: str = "",
                      font_path: str | None = None) -> ThumbnailResult:
    """Add text overlay to thumbnail using Pillow."""
    from PIL import Image, ImageDraw, ImageFont

    output_path = Path(output_path)
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)

    w, h = img.size

    # Load font
    try:
        if font_path:
            title_font = ImageFont.truetype(font_path, size=int(h * 0.1))
            sub_font = ImageFont.truetype(font_path, size=int(h * 0.06))
        else:
            title_font = ImageFont.truetype("arial.ttf", size=int(h * 0.1))
            sub_font = ImageFont.truetype("arial.ttf", size=int(h * 0.06))
    except OSError:
        title_font = ImageFont.load_default()
        sub_font = title_font

    # Draw title with stroke
    title_upper = title.upper()
    # Word-wrap long titles
    words = title_upper.split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=title_font)
        if bbox[2] > w * 0.85 and current_line:
            lines.append(" ".join(current_line))
            current_line = [word]
        else:
            current_line.append(word)
    if current_line:
        lines.append(" ".join(current_line))

    # Draw centered title lines
    y_start = h * 0.35
    line_height = int(h * 0.13)

    for i, line in enumerate(lines[:3]):  # Max 3 lines
        bbox = draw.textbbox((0, 0), line, font=title_font)
        text_w = bbox[2] - bbox[0]
        x = (w - text_w) // 2
        y = int(y_start + i * line_height)

        # Draw stroke
        for dx in range(-4, 5):
            for dy in range(-4, 5):
                draw.text((x + dx, y + dy), line, font=title_font, fill="black")
        # Draw text
        draw.text((x, y), line, font=title_font, fill="yellow")

    # Draw subtitle
    if subtitle:
        bbox = draw.textbbox((0, 0), subtitle, font=sub_font)
        text_w = bbox[2] - bbox[0]
        x = (w - text_w) // 2
        y = int(h * 0.82)
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                draw.text((x + dx, y + dy), subtitle, font=sub_font, fill="black")
        draw.text((x, y), subtitle, font=sub_font, fill="white")

    img.save(output_path, quality=95)
    return ThumbnailResult(file_path=output_path, width=w, height=h)


def generate_thumbnail(title: str, prompt: str,
                        output_dir: str | Path,
                        subtitle: str = "") -> ThumbnailResult:
    """Full thumbnail pipeline: generate AI background + add text overlay."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    bg_path = output_dir / "thumbnail_bg.png"
    final_path = output_dir / "thumbnail.png"

    # Generate background using configured image provider
    full_prompt = (f"YouTube thumbnail background: {prompt}. "
                   "Vibrant colors, high contrast, eye-catching, no text.")
    generate_image(full_prompt, bg_path, width=1792, height=1024)

    # Add text overlay
    return add_text_overlay(bg_path, final_path, title, subtitle)
