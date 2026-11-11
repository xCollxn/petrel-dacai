import serial, struct, time, os
CLK = 15667200
def W(*v): return struct.pack(">" + "H"*len(v), *v)
def frame(cmd, p=b""): return b"\xAA" + bytes((cmd,)) + p + b"\xCC\x33\xC3\x3C"
def hs(s, t=0.15):
    s.reset_input_buffer(); s.write(frame(0x00)); time.sleep(t); return s.read(64) == bytes.fromhex("aa004f4bcc33c33c")
def wait_ready(s, limit=15):
    t0 = time.time()
    while time.time() - t0 < limit:
        if hs(s, 0.1): return time.time() - t0
    return None
def sram_ok(s):
    data = os.urandom(200); s.write(frame(0x31, b"\x5A" + W(0x7000) + data)); time.sleep(0.1)
    s.reset_input_buffer(); s.write(frame(0x32, b"\x5A" + W(0x7000) + bytes((200,)))); time.sleep(0.2)
    r = s.read(300); return r[6:206] == data
s = serial.Serial("/dev/ttyAMA0", 115200, timeout=0.2); print("start", hs(s))
for baud_div in (136, 34):
    if baud_div != 136:
        s.write(frame(0x38, W(baud_div))); s.flush(); time.sleep(0.2); s.baudrate = round(CLK / baud_div); time.sleep(0.1)
    print("\n==", s.baudrate, "hs", hs(s))
    for n in (300, 1000, 3000):
        buf = b"".join(frame(0x05, b"\x01" + W((i * 2111) & 0xFFFF, 0, i % 480, 271, i % 480)) for i in range(n)) + frame(0x3D)
        t0 = time.time(); s.write(buf); s.flush(); sent = time.time() - t0
        ready = wait_ready(s)
        print(f"{n:5d} rects: sent {sent:.2f}s, panel ready after {ready if ready is None else round(ready, 2)}s more, sram check {sram_ok(s)}")
    if baud_div != 136:
        s.write(frame(0x38, W(136))); s.flush(); time.sleep(0.2); s.baudrate = 115200; time.sleep(0.1)
print("\nend 115200 hs", hs(s))
