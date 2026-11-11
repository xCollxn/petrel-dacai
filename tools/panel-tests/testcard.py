"""DACAI test card: every Petrel opcode not yet verified, each in a labelled box."""
import serial, struct, time, sys
s = serial.Serial("/dev/ttyAMA0", 115200, timeout=0.3)
def send(cmd, p=b""):
    s.write(b"\xAA" + bytes((cmd,)) + p + b"\xCC\x33\xC3\x3C"); time.sleep(0.03)
def W(*v): return struct.pack(">" + "H"*len(v), *v)
WHITE, RED, GREEN, BLUE, YELLOW, GREY, BLACK = 0xFFFF, 0xF800, 0x07E0, 0x001F, 0xFFE0, 0x8410, 0x0000
def text(x, y, t, col=WHITE): send(0x11, bytes((0x40 | 0x01,)) + W(col, BLACK, x, y) + t.encode())
def rect(mode, c, x0, y0, x1, y1): send(0x05, bytes((mode,)) + W(c, x0, y0, x1, y1))
step = sys.argv[1] if len(sys.argv) > 1 else "card"
s.reset_input_buffer(); send(0x00); time.sleep(0.2); print("handshake:", s.read(64).hex(" "))
send(0x30, b"\xFF")
if step == "card":
    send(0x29, W(0)); send(0x01, W(BLACK))
    # 1: 0x02 points
    text(4, 2, "1 PUNKTE 0x02"); send(0x02, W(RED) + bytes((4, 4)) + W(150, 8, 170, 8, 190, 8, 210, 8, 230, 8))
    # 2: 0x03 polyline
    text(4, 34, "2 LINIE 0x03"); send(0x03, W(GREEN, 140, 50, 170, 34, 200, 50, 230, 34, 260, 50))
    # 3: 0x08 bitmap (32x16 checkerboard)
    text(4, 66, "3 BITMAP 0x08")
    rows = b"".join((b"\xF0\xF0\xF0\xF0" if (r // 4) % 2 == 0 else b"\x0F\x0F\x0F\x0F") for r in range(16))
    send(0x08, W(150, 66, 32, YELLOW, BLUE) + rows)
    # 4: 0x09 move area: stripes R/G/B, then move up 10 px, fill white
    text(4, 100, "4 SCROLL 0x09"); text(4, 118, " soll: G-B-weiss", GREY)
    rect(1, RED, 150, 100, 230, 109); rect(1, GREEN, 150, 110, 230, 119); rect(1, BLUE, 150, 120, 230, 129)
    send(0x3D); time.sleep(0.2)
    send(0x09, bytes((0x80 | 2,)) + W(10, WHITE, 150, 100, 230, 129))
    # 5: 0x14 native number
    text(4, 146, "5 ZAHL 0x14"); text(4, 164, " soll: 12345", GREY)
    send(0x14, bytes((0x80 | 0x01,)) + W(WHITE, BLACK) + bytes((5, 0)) + W(160, 150) + (12345).to_bytes(4, "big"))
    # 6: 0x21 QR
    text(4, 196, "6 QR 0x21"); send(0x21, W(150, 190) + bytes((2,)) + b"PETREL DACAI")
    # 7: 0x2A EAN-13
    text(4, 300, "7 EAN13 0x2A"); send(0x2A, W(130, 296) + bytes((4, 0, 0, 6, 3, 8, 1, 3, 3, 3, 9, 3)))
    # 8: rect outline modes (0x05 mode 0 / 2)
    text(4, 400, "8 RAHMEN 0x05"); rect(0, YELLOW, 150, 396, 200, 430); rect(2, RED, 210, 396, 260, 430)
    text(4, 450, "Foto machen :)", YELLOW)
    send(0x3D)
elif step == "bright":
    send(0x01, W(WHITE)); send(0x3D)
    for v in (0xFF, 0x80, 0x30, 0x10, 0xFF):
        send(0x30, bytes((v,))); print("backlight", hex(v)); time.sleep(3)
elif step in ("rot0", "rot1", "rot2", "rot3"):
    send(0x34, b"\x5A\xA5" + bytes((int(step[3]),))); time.sleep(0.3); print("0x34 reply:", s.read(64).hex(" ") or "-")
    send(0x01, W(BLACK)); text(10, 10, "OBEN LINKS " + step, YELLOW); rect(1, RED, 0, 0, 30, 30); send(0x3D)
print("rx:", s.read(128).hex(" ") or "-")
