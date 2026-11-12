#!/usr/bin/env python3
"""Which rows/columns do 0x27 (copy) and 0x09 (move) really touch on a DACAI panel?

    rect_extent_test.py up|left|down|right   0x09 with the exact end (A) and end + 1 (B)
    rect_extent_test.py copy [PETREL_DIR]    0x27 with end - 1, end, end + 1 (1, 2, 3)

up/left/down/right: a white area is moved four times by 24 px (fill black) and the
exposed band is painted white again, like a scrolling list. A line of black in A
means the panel treats that end as exclusive; a red marker row/column after the
area shows whether end + 1 (B) leaves the outside alone.
copy: copies a dark rectangle from a Petrel sprite sheet whose next row is bright
and starts a new JPEG block. A bright line under 2 means one extra row is copied.
Results: docs/dacai-protocol.md ("Different", items 6 and 7).
"""
import struct
import sys
import time
from io import BytesIO
from pathlib import Path

import serial

TAIL = b'\xCC\x33\xC3\x3C'
WHITE, BLACK, RED = 0xFFFF, 0x0000, 0xF800
s = serial.Serial('/dev/ttyAMA0', 115200, timeout=0.3)


def send(cmd, payload=b'', wait=0.0):
    s.write(b'\xAA' + bytes((cmd,)) + payload + TAIL)
    s.flush()
    time.sleep(wait)


def words(*values):
    return struct.pack('>' + 'H' * len(values), *values)


def rect(color, x0, y0, x1, y1):
    send(0x05, b'\x01' + words(color, x0, y0, x1, y1))


def text(x, y, label):
    send(0x11, b'\x41' + words(0xFFE0, BLACK, x, y) + label.encode())


def move(direction, x0, y0, x1, y1):
    send(0x09, bytes((0x80 | direction,)) + words(24, BLACK, x0, y0, x1, y1))


def start():
    s.reset_input_buffer()
    send(0x00, wait=0.2)
    send(0x30, b'\xff')
    send(0x01, words(BLACK))


def test_move(name):
    direction = {'left': 0, 'right': 1, 'up': 2, 'down': 3}[name]
    start()
    vertical = direction >= 2
    # two areas: A with the exact end, B with end + 1; marker after the area
    areas = (((20, 60, 120, 349), (150, 60, 250, 349)) if vertical else
             ((20, 60, 119, 200), (20, 260, 119, 400)))
    for x0, y0, x1, y1 in areas:
        rect(WHITE, x0, y0, x1, y1)
        if vertical:
            rect(RED, x0, y1 + 1, x1, y1 + 1)
        else:
            rect(RED, x1 + 1, y0, x1 + 1, y1)
    send(0x3D, wait=0.3)
    for _ in range(4):
        for extra, (x0, y0, x1, y1) in enumerate(areas):
            move(direction, x0, y0, x1 + extra * (not vertical), y1 + extra * vertical)
            band = {0: (x1 - 23, y0, x1, y1), 1: (x0, y0, x0 + 23, y1),
                    2: (x0, y1 - 23, x1, y1), 3: (x0, y0, x1, y0 + 23)}[direction]
            rect(WHITE, *band)
        send(0x3D, wait=0.3)
    text(8, 8, f'{name}: A=end B=end+1')
    send(0x3D)


def test_copy(petrel):
    sys.path.insert(0, str(petrel))
    from PIL import Image
    from petrel.artwork import sprites
    sheets = sprites.build().payloads
    for number, payload in enumerate(sheets):
        sheet = Image.open(BytesIO(payload)).convert('L').rotate(-90, expand=True)
        px = sheet.load()
        for y in range(31, sheet.height - 1, 16):  # bright row starts a JPEG block
            for x in range(sheet.width - 10):
                if all(px[x + i, y + 1] > 110 for i in range(10)) and \
                        all(px[x + i, y - j] < 45 for i in range(10) for j in range(4)):
                    break
            else:
                continue
            break
        else:
            continue
        break
    else:
        raise SystemExit('no suitable spot on the sprite sheets')
    start()
    send(0x25, bytes((1, sprites.FIRST_SLOT + number)))
    for k, end in enumerate((y - 1, y, y + 1)):
        for rep in range(4):
            send(0x27, b'\x01' + words(x, y - 3, x + 9, end, 20 + 90 * k + 10 * rep, 80))
    text(8, 8, '1=end-1  2=end  3=end+1')
    send(0x3D)


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'up'
    if mode == 'copy':
        test_copy(Path(sys.argv[2] if len(sys.argv) > 2 else Path.home() / 'Petrel'))
    else:
        test_move(mode)
    print('done - look at the panel')
