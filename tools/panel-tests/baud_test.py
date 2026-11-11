"""Raise the host UART speed with 0x38 (DACAI: sets UART2 = host link), verify with SRAM write/read-back."""
import serial, struct, time, os
PORT = "/dev/ttyAMA0"; CLK = 15667200
def W(*v): return struct.pack(">" + "H"*len(v), *v)
def frame(cmd, p=b""): return b"\xAA" + bytes((cmd,)) + p + b"\xCC\x33\xC3\x3C"
def hs(s):
    s.reset_input_buffer(); s.write(frame(0x00)); time.sleep(0.15); return s.read(64) == bytes.fromhex("aa004f4bcc33c33c")
def readback(s, addr, n):
    s.reset_input_buffer(); s.write(frame(0x32, b"\x5A" + W(addr) + bytes((n,))))
    want = 1 + 1 + 1 + 2 + 1 + n + 4; buf = b""; t = time.time()
    while len(buf) < want and time.time() - t < 1: buf += s.read(want - len(buf))
    return buf[6:6+n] if buf[:2] == b"\xAA\x32" else None
s = serial.Serial(PORT, 115200, timeout=0.2)
print("115200 handshake:", hs(s))
cur = 115200
for div in (68, 34, 17):
    s.write(frame(0x38, W(div))); s.flush(); time.sleep(0.2)
    new = round(CLK / div); s.baudrate = new; time.sleep(0.1)
    ok = hs(s); print(f"\n== {new} baud (div {div}) handshake: {ok}")
    if not ok:
        print("no handshake - stopping"); break
    cur = new
    data = os.urandom(8192)
    t0 = time.time()
    for off in range(0, len(data), 240):
        s.write(frame(0x31, b"\x5A" + W(off) + data[off:off+240]))
    s.flush(); t1 = time.time(); time.sleep(0.3); acks = s.read(s.in_waiting or 0).count(b"\x5aOK")
    bad = 0
    for off in range(0, len(data), 240):
        n = min(240, len(data) - off); r = readback(s, off, n)
        if r != data[off:off+n]: bad += 1
    print(f"8 KB write {t1-t0:.2f}s, acks {acks}/{-(-len(data)//240)}, read-back blocks bad: {bad}")
# back to 115200
s.write(frame(0x38, W(136))); s.flush(); time.sleep(0.2); s.baudrate = 115200; time.sleep(0.1)
print("\nback at 115200, handshake:", hs(s))
