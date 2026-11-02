#!/usr/bin/env python3
"""Render a boot image for the DACAI panel (``private/image/0.jpg``).

The panel is portrait 272x480, but the JPEG is stored rotated (480x272), like
Petrel's own splash. Keep y 280-350 calm: Petrel draws its progress bar and status
line there while starting.

Usage:
    make_boot.py out.jpg [--preview preview.png] [--title "3D Printer"]
                 [--subtitle "KLIPPER  ·  PETREL"] [--info ""] [--footer "DACAI EDITION"]
                 [--dejavu-dir fonts/dejavu]
"""
import argparse
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, S = 272, 480, 4
CYAN = (46, 196, 230)
TEAL = (57, 180, 147)
BLUE = (58, 120, 217)
AMBER = (242, 193, 78)
ORANGE = (240, 128, 52)


def lerp(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def fit_font(path, text, max_width, size):
    while size > 10:
        f = ImageFont.truetype(path, size * S)
        if f.getlength(text) <= max_width * S:
            return f
        size -= 1
    return ImageFont.truetype(path, size * S)


def build(title, subtitle, info, footer, fonts):
    im = Image.new("RGB", (W * S, H * S))
    px = im.load()
    for y in range(H * S):
        c = lerp((10, 16, 30), (6, 9, 16), y / (H * S))
        for x in range(W * S):
            px[x, y] = c
    d = ImageDraw.Draw(im, "RGBA")
    for j in range(0, 250, 17):                       # print-bed grid, fading out
        a = round(24 * max(0.0, 1 - j / 250))
        d.line([(0, j * S), (W * S, j * S)], fill=(60, 110, 160, a), width=S)
    for i in range(0, W * S, 17 * S):
        for y0 in range(0, 250, 10):
            a = round(24 * max(0.0, 1 - y0 / 250))
            d.line([(i, y0 * S), (i, (y0 + 10) * S)], fill=(60, 110, 160, a), width=S)

    glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([46 * S, 22 * S, 226 * S, 202 * S], fill=(46, 196, 230, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(28 * S))
    im.paste(glow, (0, 0), glow)
    d = ImageDraw.Draw(im, "RGBA")

    cx, base_y, r = 136, 174, 58                      # isometric cube built from layers
    layers, layer_h = 14, 5.2
    for k in range(layers):
        t = k / (layers - 1)
        y = base_y - k * layer_h
        left_c = lerp((24, 70, 120), (34, 120, 170), t)
        right_c = lerp((18, 52, 92), (28, 96, 140), t)
        L, R, B = (cx - r * 0.87, y), (cx + r * 0.87, y), (cx, y + r * 0.5)
        Bd, Ld, Rd = (cx, y + r * 0.5 + layer_h), (cx - r * 0.87, y + layer_h), (cx + r * 0.87, y + layer_h)
        d.polygon([(p[0] * S, p[1] * S) for p in (L, B, Bd, Ld)], fill=left_c)
        d.polygon([(p[0] * S, p[1] * S) for p in (B, R, Rd, Bd)], fill=right_c)
        d.line([(L[0] * S, L[1] * S), (B[0] * S, B[1] * S), (R[0] * S, R[1] * S)],
               fill=lerp(left_c, (255, 255, 255), 0.25), width=S)
    y = base_y - layers * layer_h
    T, L, R, B = (cx, y - r * 0.5), (cx - r * 0.87, y), (cx + r * 0.87, y), (cx, y + r * 0.5)
    d.polygon([(p[0] * S, p[1] * S) for p in (T, R, B, L)], fill=(120, 225, 245))
    path = [(cx - 30, y + 2), (cx + 10, y - 21), (cx + 38, y - 5), (cx - 2, y + 18)]
    d.line([(p[0] * S, p[1] * S) for p in path], fill=(255, 255, 255, 230), width=int(2.2 * S), joint="curve")

    nx, ny = cx - 2, y + 18                           # nozzle with glowing tip
    d.rounded_rectangle([(nx - 22) * S, (ny - 74) * S, (nx + 22) * S, (ny - 46) * S], radius=5 * S,
                        fill=(150, 165, 182))
    d.rounded_rectangle([(nx - 22) * S, (ny - 74) * S, (nx + 22) * S, (ny - 68) * S], radius=3 * S,
                        fill=(190, 202, 215))
    d.rectangle([(nx - 9) * S, (ny - 46) * S, (nx + 9) * S, (ny - 30) * S], fill=ORANGE)
    d.polygon([((nx - 9) * S, (ny - 30) * S), ((nx + 9) * S, (ny - 30) * S), (nx * S, (ny - 12) * S)], fill=ORANGE)
    hot = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(hot).ellipse([(nx - 12) * S, (ny - 22) * S, (nx + 12) * S, (ny + 2) * S], fill=(255, 170, 60, 200))
    hot = hot.filter(ImageFilter.GaussianBlur(6 * S))
    im.paste(hot, (0, 0), hot)
    d = ImageDraw.Draw(im, "RGBA")
    d.ellipse([(nx - 2.2) * S, (ny - 14) * S, (nx + 2.2) * S, (ny - 9.6) * S], fill=(255, 235, 170))
    d.line([(nx * S, (ny - 10) * S), (nx * S, ny * S)], fill=(255, 220, 150, 255), width=int(1.6 * S))

    bold = os.path.join(fonts, "DejaVuSans-Bold.ttf")
    mono = ImageFont.truetype(os.path.join(fonts, "DejaVuSansMono-Bold.ttf"), 11 * S)
    small = ImageFont.truetype(os.path.join(fonts, "DejaVuSans.ttf"), 10 * S)
    d.text((W / 2 * S, 238 * S), title, font=fit_font(bold, title, 250, 25), fill=(240, 244, 248), anchor="mm")
    if subtitle:
        d.text((W / 2 * S, 263 * S), subtitle, font=mono, fill=CYAN, anchor="mm")
    d.line([(96 * S, 392 * S), (176 * S, 392 * S)], fill=(46, 196, 230, 120), width=S)
    if info:
        d.text((W / 2 * S, 410 * S), info, font=small, fill=(150, 170, 190), anchor="mm")
    if footer:
        d.text((W / 2 * S, 430 * S), footer, font=mono, fill=AMBER, anchor="mm")
    for k in range(3):
        d.ellipse([(124 + k * 12 - 2) * S, 452 * S, (124 + k * 12 + 2) * S, 456 * S], fill=(CYAN, TEAL, BLUE)[k])
    return im.resize((W, H), Image.LANCZOS)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("--preview")
    ap.add_argument("--title", default="3D Printer")
    ap.add_argument("--subtitle", default="KLIPPER  ·  PETREL")
    ap.add_argument("--info", default="", help="small grey line, e.g. build volume")
    ap.add_argument("--footer", default="DACAI EDITION")
    ap.add_argument("--dejavu-dir", default=os.environ.get("DEJAVU_DIR", "fonts/dejavu"))
    a = ap.parse_args()
    portrait = build(a.title, a.subtitle, a.info, a.footer, a.dejavu_dir)
    if a.preview:
        portrait.save(a.preview)
    portrait.rotate(90, expand=True).save(a.out, "JPEG", quality=92, subsampling=2, progressive=False)
    print(a.out, "written (480x272, rotated)")
