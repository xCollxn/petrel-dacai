"""DACAI: unbekannter Befehl 0x20 im Vergleich zu 0x23 (Icon-Reihe)."""
import serial, struct, time
s = serial.Serial("/dev/ttyAMA0", 115200, timeout=0.3)
def send(cmd, p=b""):
    s.write(b"\xAA" + bytes((cmd,)) + p + b"\xCC\x33\xC3\x3C"); time.sleep(0.05)
def W(*v): return struct.pack(">" + "H"*len(v), *v)
WHITE, YELLOW, BLACK, GREY = 0xFFFF, 0xFFE0, 0x0000, 0x8410
def text(x, y, t, col=WHITE): send(0x11, bytes((0x40 | 0x01,)) + W(col, BLACK, x, y) + t.encode())
s.reset_input_buffer(); send(0x00); time.sleep(0.2); print("handshake:", s.read(64).hex(" "))
send(0x30, b"\xFF"); send(0x29, W(0)); send(0x01, W(BLACK))
IDS = bytes((20, 21, 22))
text(4, 4, "0 REFERENZ 0x23", YELLOW)
send(0x23, W(120, 24) + bytes((0x89,)) + IDS)
tests = [("1 0x20 m89 p00", 0x89, 0x00), ("2 0x20 m09 p00", 0x09, 0x00),
         ("3 0x20 m89 p09", 0x89, 0x09), ("4 0x20 m09 p09", 0x09, 0x09),
         ("5 0x20 m89 p20", 0x89, 0x20)]
y = 80
for label, m, p in tests:
    text(4, y, label)
    send(0x20, W(120, y + 20) + bytes((m, p)) + IDS)
    r = s.read(64)
    print(label, "rx:", r.hex(" ") or "-")
    y += 76
text(4, 462, "Foto machen :)", YELLOW)
send(0x3D); time.sleep(0.3)
print("rx end:", s.read(128).hex(" ") or "-")
