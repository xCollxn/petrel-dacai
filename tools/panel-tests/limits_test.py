"""DACAI limits for SD-free sprites: picture slots >15, free space for 8 full sheets, 0x25 decode time."""
import serial, struct, time, io, random, sys
from PIL import Image, ImageDraw, ImageFont
s = serial.Serial("/dev/ttyAMA0", 115200, timeout=0.5)
def send(cmd, p=b"", wait=0.03): s.write(b"\xAA" + bytes((cmd,)) + p + b"\xCC\x33\xC3\x3C"); s.flush(); time.sleep(wait)
def W(*v): return struct.pack(">" + "H"*len(v), *v)
def text(x, y, t, col=0xFFE0): send(0x11, bytes((0x40 | 0x01,)) + W(col, 0x0000, x, y) + t.encode())
SLOTS = list(range(16, 24))
COLS = [(200, 40, 40), (40, 160, 40), (40, 60, 200), (200, 160, 0), (160, 40, 160), (0, 150, 150), (230, 110, 0), (120, 120, 120)]
font = ImageFont.load_default(size=44)
def sheet(n, col):
    rnd = random.Random(n)
    p = Image.new("RGB", (272, 480)); px = p.load()
    for y in range(480):
        for x in range(272): px[x, y] = (rnd.randrange(256), rnd.randrange(256), rnd.randrange(256))
    d = ImageDraw.Draw(p); d.rectangle((0, 0, 127, 59), fill=col); d.text((10, 6), "%d" % n, font=font, fill="white")
    for q in range(95, 5, -5):
        b = io.BytesIO(); p.rotate(90, expand=True).save(b, "JPEG", quality=q, subsampling=2, progressive=False); j = b.getvalue()
        if len(j) <= 30000: break
    pad = 32768 - len(j) - 4
    j = j[:2] + b"\xFF\xFE" + struct.pack(">H", pad + 2) + b"\x00" * pad + j[2:]
    assert len(j) == 32768 and j[-2:] == b"\xFF\xD9"
    return j, q
s.reset_input_buffer(); send(0x00, wait=0.2); print("handshake:", s.read(64).hex(" "))
send(0x30, b"\xFF"); send(0x29, W(0)); send(0x01, W(0x0000))
if "noupload" not in sys.argv:
    for n, slot in enumerate(SLOTS):
        jpg, q = sheet(slot, COLS[n])
        text(4, 4 + n * 22, "lade Platz %d (q%d) ..." % (slot, q), 0xFFFF); send(0x3D)
        t0 = time.time()
        for off in range(0, len(jpg), 240):
            send(0x31, b"\x5A" + W(off) + jpg[off:off + 240], wait=0.022)
        time.sleep(0.3); s.read(s.in_waiting or 0)
        send(0x33, bytes((0x5A, 0xA5, slot)), wait=3)
        print("slot", slot, "q", q, "0x33:", s.read(64).hex(" ") or "-", "%.1fs" % (time.time() - t0))
send(0x01, W(0x0000))
for n, slot in enumerate(SLOTS):
    x, y = 4 + (n % 2) * 136, 2 + (n // 2) * 64
    send(0x25, bytes((1, slot)), wait=0.8)
    send(0x26, W(0, 0, 127, 59, x, y))
# timing row: switch between 16 and 17 with shrinking waits; expected label below each cell
for n, (slot, wait) in enumerate([(17, 0.3), (16, 0.15), (17, 0.08), (16, 0.03), (17, 0.0), (16, 0.0)]):
    x, y = 4 + (n % 2) * 136, 262 + (n // 2) * 70
    t0 = time.time(); send(0x25, bytes((1, slot)), wait=wait); send(0x26, W(0, 0, 127, 59, x, y))
    text(x, y + 61, "soll %d, %dms" % (slot, wait * 1000))
send(0x3D); time.sleep(0.3); print("fertig rx:", s.read(64).hex(" ") or "-")
