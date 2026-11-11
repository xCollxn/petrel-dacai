"""SD-free icon idea: Petrel icons on a JPEG sprite sheet, uploaded with padded 0x33,
drawn by copying from virtual area 1 (0x26 opaque / 0x27 bit7 = black transparent on DACAI)."""
import serial, struct, time, io, glob, os, sys
from PIL import Image
SLOT = 10
s = serial.Serial("/dev/ttyAMA0", 115200, timeout=0.5)
def send(cmd, p=b""): s.write(b"\xAA" + bytes((cmd,)) + p + b"\xCC\x33\xC3\x3C"); time.sleep(0.004)
def W(*v): return struct.pack(">" + "H"*len(v), *v)
icons = {}
for f in sorted(glob.glob(os.path.expanduser("~/Petrel/assets/icons/*.jpg"))):
    icons[int(os.path.basename(f)[:3])] = Image.open(f).convert("RGB")
pick = [i for i, im in icons.items() if im.size == (110, 100)][:4] \
     + [i for i, im in icons.items() if im.size == (78, 36)][:4] \
     + [i for i, im in icons.items() if im.size == (20, 20)][:24]
# shelf packing on a portrait 272x480 sheet
sheet = Image.new("RGB", (272, 480)); x = y = shelf = 0; pos = {}
for i in pick:
    im = icons[i]; w, h = im.size
    if x + w > 272: x, y, shelf = 0, y + shelf, 0
    sheet.paste(im, (x, y)); pos[i] = (x, y, w, h); x += w; shelf = max(shelf, h)
b = io.BytesIO(); sheet.rotate(90, expand=True).save(b, "JPEG", quality=92, subsampling=2); jpg = b.getvalue()
print("sheet jpeg", len(jpg), "bytes,", len(pick), "icons")
pad = 32768 - len(jpg) - 4; assert pad >= 0
jpg = jpg[:2] + b"\xFF\xFE" + struct.pack(">H", pad + 2) + b"\x00" * pad + jpg[2:]
s.reset_input_buffer(); send(0x00); time.sleep(0.2); print("handshake:", s.read(64).hex(" "))
send(0x30, b"\xFF")
if "noupload" not in sys.argv:
    for off in range(0, len(jpg), 240):
        send(0x31, b"\x5A" + W(off) + jpg[off:off+240]); time.sleep(0.02)
    time.sleep(0.3); s.read(s.in_waiting or 0)
    send(0x33, bytes((0x5A, 0xA5, SLOT))); time.sleep(3); print("0x33:", s.read(64).hex(" ") or "-")
# compose a Petrel-like screen
t0 = time.time()
send(0x01, W(0x2967))                                   # window background
send(0x05, b"\x01" + W(0x19E9, 0, 0, 271, 29))          # title bar
send(0x25, bytes((1, SLOT))); time.sleep(0.6)
tiles = pick[:4]
for n, i in enumerate(tiles):                           # 2x2 home tiles, opaque copy (0x26)
    x0, y0, w, h = pos[i]; dx, dy = 20 + (n % 2) * 122, 40 + (n // 2) * 110
    send(0x26, W(x0, y0, x0 + w - 1, y0 + h - 1, dx, dy))
small = pick[8:20]
for n, i in enumerate(small):                           # small icons: left opaque 0x27 m=0x01, right transparent m=0x81
    x0, y0, w, h = pos[i]; dy = 270 + (n % 6) * 30; base = 20 if n < 6 else 150
    send(0x05, b"\x01" + W(0xC618 if n % 2 else 0xFD20, base - 4, dy - 4, base + 90, dy + 24))   # coloured row
    send(0x27, b"\x01" + W(x0, y0, x0 + w - 1, y0 + h - 1, base, dy))
    send(0x27, b"\x81" + W(x0, y0, x0 + w - 1, y0 + h - 1, base + 50, dy))
send(0x3D); print("screen drawn in %.2fs" % (time.time() - t0))
