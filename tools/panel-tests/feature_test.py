"""DACAI feature tests for Petrel upstream: 0x28 animation, 0x27 area 0, 0x25/0x26 area 1."""
import serial, struct, sys, time

s = serial.Serial("/dev/ttyAMA0", 115200, timeout=0.3)

def send(cmd, payload=b""):
    s.write(b"\xAA" + bytes((cmd,)) + payload + b"\xCC\x33\xC3\x3C")
    time.sleep(0.03)
    r = s.read(64)
    return r

def W(*v): return struct.pack(">" + "H" * len(v), *v)
def upd(): send(0x3D)
def clear(c): send(0x01, W(c))
def rect(c, x0, y0, x1, y1): send(0x05, b"\x01" + W(c, x0, y0, x1, y1))

print("handshake:", send(0x00).hex(" "))
send(0x30, b"\xFF")
t = sys.argv[1]

if t == "anim":
    clear(0x0000)
    # channel 0: boot spinner 181-185, channel 1: fan 166-173
    send(0x28, W(110, 150) + bytes((0xC0, 2, 181, 185, 20)))
    send(0x28, W(110, 300) + bytes((0xC1, 2, 166, 173, 10)))
    upd()
elif t == "anim_upd":       # same, but keep sending 0x3D (does the panel need refreshes?)
    clear(0x0000)
    send(0x28, W(110, 150) + bytes((0xC0, 2, 181, 185, 20)))
    send(0x28, W(110, 300) + bytes((0xC1, 2, 166, 173, 10)))
    for _ in range(100):
        upd(); time.sleep(0.1)
elif t == "anim_off":
    send(0x29, W(0)); upd()
elif t == "area0":
    send(0x29, W(0))
    send(0x22, b"\x00\x00"); upd(); print("picture 0 shown"); time.sleep(4)
    rect(0xF800, 40, 120, 230, 360); upd(); print("red box"); time.sleep(4)
    # restore from area 0 (mode: background, index 0) = what Petrel does on the boot screen
    send(0x27, b"\x80" + W(40, 120, 230, 360, 40, 120)); upd(); print("restored")
elif t == "area1":
    send(0x29, W(0))
    clear(0x001F); upd(); print("blue screen"); time.sleep(1)
    send(0x25, b"\x01\x00"); upd(); print("picture 0 cached in area 1 (should stay blue)")
    time.sleep(4)
    send(0x26, W(0, 0, 271, 239, 0, 0)); upd(); print("copied top half from area 1")
print("rx:", s.read(64).hex(" "))

if t == "area0b":
    send(0x22, b"\x00\x00"); upd(); time.sleep(2)
    rect(0xF800, 40, 120, 230, 359); upd(); print("red box"); time.sleep(3)
    strips = [(120, 179, b"\x00"), (180, 239, b"\x20"), (240, 299, b"\xC0")]
    for i, (y0, y1, m) in enumerate(strips, 1):
        r = send(0x27, m + W(40, y0, 230, y1, 40, y0)); upd(); print("strip", i, m.hex(), r.hex(" ")); time.sleep(2)
    r = send(0x25, b"\x01\x00"); print("0x25:", r.hex(" "))
    r = send(0x27, b"\x81" + W(40, 300, 230, 359, 40, 300)); upd(); print("strip 4 via area 1", r.hex(" "))

if t == "one":
    mode = bytes.fromhex(sys.argv[2])
    send(0x22, b"\x00\x00"); upd(); time.sleep(1.5)
    if len(sys.argv) > 3: send(0x25, b"\x01\x00")
    rect(0xF800, 40, 120, 230, 359); upd(); print("red box"); time.sleep(3)
    send(0x27, mode + W(40, 120, 230, 359, 40, 120)); upd(); print("copy", mode.hex())
