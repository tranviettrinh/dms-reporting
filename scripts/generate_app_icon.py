from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    assets_dir = root / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    size = 256
    image = Image.new("RGBA", (size, size), (15, 23, 42, 0))
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle((16, 16, 240, 240), radius=48, fill=(29, 78, 216, 255))
    draw.rounded_rectangle((28, 28, 228, 228), radius=40, outline=(125, 211, 252, 255), width=4)
    draw.ellipse((148, 40, 216, 108), fill=(16, 185, 129, 255))
    draw.ellipse((52, 156, 108, 212), fill=(251, 191, 36, 255))

    font = _load_font(92)
    text = "DMS"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (size - text_width) / 2
    text_y = (size - text_height) / 2 - 8

    shadow_offset = 4
    draw.text((text_x + shadow_offset, text_y + shadow_offset), text, font=font, fill=(15, 23, 42, 140))
    draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255, 255))

    png_path = assets_dir / "abipha-dms-reporter.png"
    ico_path = assets_dir / "abipha-dms-reporter.ico"
    image.save(png_path)
    image.save(ico_path, sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])


if __name__ == "__main__":
    main()
