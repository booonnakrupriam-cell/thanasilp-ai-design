"""Smoke checks for Print Studio and OCR utilities."""
from io import BytesIO
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image, ImageDraw

import print_studio as p
from interactive_sign_editor import _detect_thai_text


def run():
    assert p._parse_thai_date("02/07/2474").year == 1931
    assert p._parse_thai_date("99/99/2569") is None
    assert p._thai_digits("15 2569") == "๑๕ ๒๕๖๙"
    w, h, dpi = p._target_pixels(300, 150, 150)
    assert w * h <= p.MAX_OUTPUT_PIXELS and dpi <= 150
    assert w > 1000 and h > 1000
    blank = Image.new("RGBA", (360, 180), (250, 250, 255, 255))
    data = p._image_bytes(blank, "PNG", 150)
    with Image.open(BytesIO(data)) as image:
        assert image.size == (360, 180)
    font = p._font(30)
    assert font is not None, "Thai font package was not installed"
    d = ImageDraw.Draw(blank)
    d.text((30, 35), "Hello 2026", font=font, fill="#000000")
    buf = BytesIO()
    blank.save(buf, format="PNG")
    boxes = _detect_thai_text(buf.getvalue())
    assert isinstance(boxes, list) and len(boxes) <= 100
    print("PASS: Print Studio math, Thai fonts, export PNG, and OCR runtime")


if __name__ == "__main__":
    run()
