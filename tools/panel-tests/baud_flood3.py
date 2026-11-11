import serial, struct, time, os
CLK = 15667200
def W(*v): return struct.pack(">" + "H"*len(v), *v)
def frame(cmd, p=b""): return b"\xAA" + bytes((cmd,)) + p + b"\xCC\x33\xC3\x3C"
def hs(s, t=0.1):
    s.reset_input_buffer(); s.write(frame(0x00)); time.sleep(t); return s.read(64) == bytes.fromhex("aa004f4bcc33c33c")
def wait_ready(s, limit=15):
    t0 = time.time()
    while time.time() - t0 < limit:
        if hs(s): return round(time.time() - t0, 2)
def sram_ok(s):
    data = os.urandom(200); s.write(frame(0x31, b"\x5A" + W(0x7000) + data)); time.sleep(0.1)
    s.reset_input_buffer(); s.write(frame(0x32, b"\x5A" + W(0x7000) + bytes((200,)))); time.sleep(0.2)
    return s.read(300)[6:206] == data
s = serial.Serial("/dev/ttyAMA0", 115200, timeout=0.2); print("start", hs(s))
for div in (34, 17):
    s.write(frame(0x38, W(div))); s.flush(); time.sleep(0.2); s.baudrate = round(CLK / div); time.sleep(0.1)
    print("\n==", s.baudrate, "ready", wait_ready(s))
    for rounds in (1, 3):
        buf = b""
        for r in range(rounds):
            for i in range(24):
                buf += frame(0x05, b"\x01" + W(0x2967, 0, i * 20, 271, i * 20 + 19))
                buf += frame(0x11, bytes((0x40 | 1,)) + W(0xFFFF, 0x2967, 30, i * 20 + 2) + b"Menu line %02d  Temperature 215" % i)
                buf += frame(0x23, W(4, i * 20) + bytes((0x02, (i * 7 + r) % 180)))
        buf += frame(0x3D)
        t0 = time.time(); s.write(buf); s.flush(); sent = round(time.time() - t0, 2)
        print(f"{rounds} full menu screen(s): sent {sent}s, ready after {wait_ready(s)}s, sram {sram_ok(s)}")
    s.write(frame(0x38, W(136))); s.flush(); time.sleep(0.2); s.baudrate = 115200; time.sleep(0.1)
print("\nend 115200 ready", wait_ready(s))
