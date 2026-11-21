#!/usr/bin/env python3
"""Build-time font atlas generator (fresh code, written for this entry).

Renders printable ASCII glyphs with PIL + system DejaVu fonts into a single
grayscale bitmap (atlas.bin) plus metrics (atlas.json). The runtime entry
(main.py) uses only the Python standard library and reads these two files;
no font files or PIL are needed at run time.
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = "/usr/share/fonts/truetype/dejavu"

SIZES = {
    "mast": (f"{FONT_DIR}/DejaVuSerif-Bold.ttf", 54),
    "head": (f"{FONT_DIR}/DejaVuSans-Bold.ttf", 25),
    "sub": (f"{FONT_DIR}/DejaVuSans-Bold.ttf", 17),
    "body": (f"{FONT_DIR}/DejaVuSans.ttf", 13),
    "small": (f"{FONT_DIR}/DejaVuSans.ttf", 11),
    "label": (f"{FONT_DIR}/DejaVuSans-Bold.ttf", 12),
}

CHARS = "".join(chr(c) for c in range(32, 127))


def main():
    # Measure every glyph at every size first.
    glyphs = {}  # size -> char -> dict
    row_heights = {}
    for name, (path, px) in SIZES.items():
        font = ImageFont.truetype(path, px)
        row = {}
        max_h = 0
        for ch in CHARS:
            # Render on a scratch tile to get exact ink box.
            tmp = Image.new("L", (px * 2 + 8, px * 3), 0)
            d = ImageDraw.Draw(tmp)
            d.text((4, 4), ch, font=font, fill=255)
            bbox = tmp.getbbox()
            if bbox is None:  # space or blank
                adv = int(font.getlength(ch))
                row[ch] = {"x": 0, "y": 0, "w": 0, "h": 0, "adv": adv, "bx": 0, "by": 0}
                continue
            x0, y0, x1, y1 = bbox
            w, h = x1 - x0, y1 - y0
            adv = int(round(font.getlength(ch)))
            # bearing relative to a common baseline: store top offset from row top
            row[ch] = {"x": 0, "y": 0, "w": w, "h": h, "adv": adv, "bx": x0 - 4, "by": y0 - 4}
            max_h = max(max_h, h)
        glyphs[name] = row
        row_heights[name] = max_h + 4

    # Lay out: one horizontal strip per size.
    widths = {}
    for name in SIZES:
        widths[name] = sum(g["w"] + 2 for g in glyphs[name].values())
    atlas_w = max(widths.values()) + 4
    atlas_h = sum(row_heights.values()) + 4 * len(SIZES)
    atlas = Image.new("L", (atlas_w, atlas_h), 0)
    draw = ImageDraw.Draw(atlas)

    meta = {"width": atlas_w, "height": atlas_h, "sizes": {}}
    y = 0
    for name, (path, px) in SIZES.items():
        font = ImageFont.truetype(path, px)
        x = 2
        entry = {"ascent": int(font.getmetrics()[0]), "glyphs": {}}
        for ch in CHARS:
            g = glyphs[name][ch]
            if g["w"] > 0:
                tmp = Image.new("L", (px * 2 + 8, px * 3), 0)
                d = ImageDraw.Draw(tmp)
                d.text((4, 4), ch, font=font, fill=255)
                tile = tmp.crop((g["bx"] + 4, g["by"] + 4,
                                 g["bx"] + 4 + g["w"], g["by"] + 4 + g["h"]))
                atlas.paste(tile, (x, y))
            entry["glyphs"][ch] = {"x": x, "y": y, "w": g["w"], "h": g["h"],
                                   "adv": g["adv"], "bx": g["bx"], "by": g["by"]}
            x += g["w"] + 2
        meta["sizes"][name] = entry
        y += row_heights[name] + 4

    with open(os.path.join(BASE, "atlas.bin"), "wb") as f:
        f.write(atlas.tobytes())
    with open(os.path.join(BASE, "atlas.json"), "w") as f:
        json.dump(meta, f, separators=(",", ":"))
    print("atlas", atlas_w, "x", atlas_h, "bytes", os.path.getsize(os.path.join(BASE, "atlas.bin")))


if __name__ == "__main__":
    main()
