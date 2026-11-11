import serial, struct, time, io
from PIL import Image, ImageDraw
s = serial.Serial("/dev/ttyAMA0", 115200, timeout=0.3)
def send(cmd, p=b""): s.write(b"\xAA" + bytes((cmd,)) + p + b"\xCC\x33\xC3\x3C")
def W(*v): return struct.pack(">" + "H"*len(v), *v)
def pic(n):
    im = Image.new("RGB", (n, n))
    for y in range(n):
        for x in range(n): im.putpixel((x, y), (x*255//n, y*255//n, 160))
    d = ImageDraw.Draw(im); d.line((0,0,n-1,n-1), fill="white", width=5); d.line((0,n-1,n-1,0), fill="white", width=5); d.rectangle((0,0,n-1,n-1), outline="yellow", width=4)
    return im
def upload(jpg):
    for off in range(0, len(jpg), 128):
        send(0x31, b"\x5A" + W(off) + jpg[off:off+128]); time.sleep(0.012)
    s.read(s.in_waiting or 0)
s.reset_input_buffer(); send(0x00); time.sleep(0.2); print("handshake:", s.read(64).hex(" "))
send(0x30, b"\xFF")                      # backlight on
send(0x01, W(0x001F)); send(0x3D); time.sleep(0.3)   # blue background
b = io.BytesIO(); pic(128).save(b, "JPEG", quality=85); jpg = b.getvalue(); upload(jpg)
send(0x24, W(72, 40) + b"\x80" + W(0)); send(0x3D); time.sleep(1)     # top: DWIN 0x24
send(0x70, W(72, 290, 0)); send(0x3D); time.sleep(1)                  # bottom: DACAI 0x70
print("done", s.read(64).hex(" ") or "-")
