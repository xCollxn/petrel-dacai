"""0x33 upload with the JPEG padded to exactly 32768 bytes (COM segment), so it ends with FF D9."""
import serial, struct, time, io, sys
from PIL import Image, ImageDraw, ImageFont
s = serial.Serial("/dev/ttyAMA0", 115200, timeout=0.5)
def send(cmd, p=b""): s.write(b"\xAA" + bytes((cmd,)) + p + b"\xCC\x33\xC3\x3C")
def W(*v): return struct.pack(">" + "H"*len(v), *v)
SLOT = int(sys.argv[1])
p = Image.new("RGB", (272, 480))
for y in range(480):
    for x in range(272): p.putpixel((x, y), (x*255//272, 60, y*255//480))
d = ImageDraw.Draw(p); d.text((40, 200), "SLOT %d OK" % SLOT, font=ImageFont.load_default(size=40), fill="white")
d.rectangle((0, 0, 271, 479), outline="yellow", width=6)
b = io.BytesIO(); p.rotate(90, expand=True).save(b, "JPEG", quality=80, subsampling=2, progressive=False); jpg = b.getvalue()
pad = 32768 - len(jpg) - 4                      # COM marker (2) + length field (2)
assert 0 <= pad <= 65533, len(jpg)
jpg = jpg[:2] + b"\xFF\xFE" + struct.pack(">H", pad + 2) + b"\x00" * pad + jpg[2:]
assert len(jpg) == 32768 and jpg[-2:] == b"\xFF\xD9"
s.reset_input_buffer(); send(0x00); time.sleep(0.2); print("handshake:", s.read(64).hex(" "))
send(0x30, b"\xFF"); send(0x01, W(0x001F)); send(0x3D)
t0 = time.time()
for off in range(0, len(jpg), 240):
    send(0x31, b"\x5A" + W(off) + jpg[off:off+240]); time.sleep(0.022)
time.sleep(0.3); s.read(s.in_waiting or 0); print("upload %.1fs" % (time.time() - t0))
send(0x33, bytes((0x5A, 0xA5, SLOT))); time.sleep(3); print("0x33:", s.read(64).hex(" ") or "-")
send(0x22, bytes((0, SLOT))); send(0x3D); print("shown slot", SLOT)
