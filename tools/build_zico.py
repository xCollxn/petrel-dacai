#!/usr/bin/env python3
"""Build a DACAI icon library (N.zico) from a folder of icon images.

DACAI panels (the DWIN-T5UIC1 look-alike Creality fitted to many Ender-3 V2 Neo /
Max Neo / S1 printers) load icons from the microSD folder ``private/icon/N.zico``.

ZICO format (reverse-engineered from Creality's stock files):

    b'ZICO' + u32le directory_length (= count * 16)
    directory entry (16 bytes, little endian):
        u16 id, u16 1, u16 width, u16 height, u32 offset, u32 length
    payload per icon: zlib( RGB565 little-endian pixels, row by row )

Pure black (0x0000) is treated as transparent by Petrel's icon drawing, so near-black
JPEG noise is snapped to black.

Usage:
    build_zico.py <icon_dir> <out.zico>      # icon_dir holds NNN.jpg / NNN.png
    build_zico.py --verify <file.zico>
"""
import re
import struct
import sys
import zlib
from pathlib import Path

from PIL import Image


def rgb565(img, black_threshold):
    img = img.convert("RGB")
    out = bytearray()
    for r, g, b in img.getdata():
        if r < black_threshold and g < black_threshold and b < black_threshold:
            r = g = b = 0
        out += struct.pack("<H", ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3))
    return bytes(out)


def build(src_dir, dest, black_threshold=10):
    entries = []
    for f in sorted(Path(src_dir).iterdir()):
        m = re.fullmatch(r"(\d{3})\.(jpg|png)", f.name)
        if not m:
            continue
        img = Image.open(f)
        w, h = img.size
        entries.append((int(m.group(1)), w, h, zlib.compress(rgb565(img, black_threshold), 9)))
    entries.sort()
    directory, blob = bytearray(), bytearray()
    for icon_id, w, h, data in entries:
        directory += struct.pack("<HHHHII", icon_id, 1, w, h, len(blob), len(data))
        blob += data
    Path(dest).write_bytes(b"ZICO" + struct.pack("<I", len(directory)) + directory + blob)
    print(f"{dest}: {len(entries)} icons, {8 + len(directory) + len(blob)} bytes")


def verify(path):
    d = Path(path).read_bytes()
    assert d[:4] == b"ZICO", "not a ZICO file"
    hl = struct.unpack("<I", d[4:8])[0]
    base = 8 + hl
    ids = []
    for i in range(hl // 16):
        icon_id, _, w, h, off, size = struct.unpack("<HHHHII", d[8 + i * 16:24 + i * 16])
        assert len(zlib.decompress(d[base + off:base + off + size])) == w * h * 2, icon_id
        ids.append(icon_id)
    print(f"{path}: OK, {len(ids)} icons, IDs {ids[0]}..{ids[-1]}")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--verify":
        verify(sys.argv[2])
    elif len(sys.argv) == 3:
        build(sys.argv[1], sys.argv[2])
    else:
        sys.exit(__doc__)
