#!/usr/bin/env python3
"""Check and adjust a DACAI icon library (ZICO) for native use with Petrel.

    zico_tool.py compare 2.zico ~/Petrel/assets/icons
        Which Petrel icon IDs are missing, have another size or look different
        (redrawn icons). Run it after every Petrel update before relying on
        PETREL_DACAI_PANEL_ICONS.

    zico_tool.py backing 2.zico out.zico 0x18C4 166-173
        Native 0x28 animations are drawn opaque. Give the listed icons an opaque
        backing colour instead of black (black = transparent only for normal icon
        drawing). 166-173 are Petrel's fan frames on the 0x18C4 dashboard.

ZICO: b'ZICO' + u32 directory length, 16-byte entries (u16 id, u16 1, u16 w, u16 h,
u32 offset, u32 length), payload zlib(RGB565 little endian). See tools/build_zico.py.
"""
import argparse
import struct
import sys
import zlib
from pathlib import Path


def read_zico(path):
    z = Path(path).read_bytes()
    if z[:4] != b'ZICO':
        raise SystemExit('not a ZICO file: ' + str(path))
    count = struct.unpack_from('<I', z, 4)[0] // 16
    base = 8 + count * 16
    icons = []
    for i in range(count):
        icon, one, w, h, off, length = struct.unpack_from('<HHHHII', z, 8 + i * 16)
        icons.append([icon, one, w, h, z[base + off:base + off + length]])
    return icons


def write_zico(path, icons):
    directory, blob = bytearray(), bytearray()
    for icon, one, w, h, data in icons:
        directory += struct.pack('<HHHHII', icon, one, w, h, len(blob), len(data))
        blob += data
    data = b'ZICO' + struct.pack('<I', len(directory)) + directory + blob
    Path(path).write_bytes(data)
    return len(data)


def cmd_compare(args):
    from PIL import Image
    lib = {icon: (w, h, zlib.decompress(data)) for icon, _one, w, h, data in read_zico(args.zico)}
    assets = {int(f.stem[:3]): f for f in Path(args.icons).glob('*.jpg') if f.stem[:3].isdigit()}
    missing = sorted(set(assets) - set(lib))
    size_diff, looks = [], []
    for icon in sorted(set(assets) & set(lib)):
        w, h, raw = lib[icon]
        with Image.open(assets[icon]) as im:
            im = im.convert('RGB')
            if im.size != (w, h):
                size_diff.append(f'{icon} (Petrel {im.size[0]}x{im.size[1]}, zico {w}x{h})')
                continue
            total = 0
            pixels = im.get_flattened_data() if hasattr(im, 'get_flattened_data') else im.getdata()
            for i, (r, g, b) in enumerate(pixels):
                v = raw[2 * i] | raw[2 * i + 1] << 8
                total += abs(r - ((v >> 11) << 3)) + abs(g - (((v >> 5) & 63) << 2)) + abs(b - ((v & 31) << 3))
            if total / (3 * w * h) > 12:
                looks.append(icon)
    print(f'zico: {len(lib)} icons, Petrel: {len(assets)} icons')
    print('MISSING in zico (would not be drawn):', missing or 'none')
    print('different size (would be drawn wrong):', size_diff or 'none')
    print('only in zico:', sorted(set(lib) - set(assets)) or 'none')
    print('same size but different look (your redrawn icons?):', looks or 'none')
    return 1 if missing or size_diff else 0


def cmd_backing(args):
    colour = int(args.colour, 0)
    low, high = (int(v) for v in args.ids.split('-'))
    icons = read_zico(args.zico)
    for entry in icons:
        if low <= entry[0] <= high:
            raw = bytearray(zlib.decompress(entry[4]))
            changed = 0
            for j in range(0, len(raw), 2):
                if raw[j] == 0 and raw[j + 1] == 0:
                    struct.pack_into('<H', raw, j, colour)
                    changed += 1
            entry[4] = zlib.compress(bytes(raw), 9)
            print(f'icon {entry[0]}: {changed} black pixels -> {colour:#06x}')
    size = write_zico(args.output, icons)
    print(f'wrote {args.output} ({size} bytes)')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('compare'); p.add_argument('zico'); p.add_argument('icons'); p.set_defaults(run=cmd_compare)
    p = sub.add_parser('backing'); p.add_argument('zico'); p.add_argument('output'); p.add_argument('colour')
    p.add_argument('ids'); p.set_defaults(run=cmd_backing)
    args = parser.parse_args(argv)
    return args.run(args)


if __name__ == '__main__':
    sys.exit(main())
