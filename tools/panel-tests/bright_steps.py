import serial, struct, time
s = serial.Serial("/dev/ttyAMA0", 115200, timeout=0.3)
def send(cmd, p=b""): s.write(b"\xAA" + bytes((cmd,)) + p + b"\xCC\x33\xC3\x3C"); time.sleep(0.02)
def W(*v): return struct.pack(">" + "H"*len(v), *v)
send(0x00); time.sleep(0.2); s.read(64)
for v in (63, 32, 16, 8, 4, 2, 1, 63):
    send(0x01, W(0xFFFF)); send(0x05, b"\x01" + W(0x2967, 0, 160, 271, 330))
    send(0x11, bytes((0x40 | 0x09,)) + W(0xFFFF, 0x2967, 100, 210) + str(v).rjust(2).encode())   # 32x64 font
    send(0x3D); send(0x30, bytes((v,))); print("level", v); time.sleep(3)
