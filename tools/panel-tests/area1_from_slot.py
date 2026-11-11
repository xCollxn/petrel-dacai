import serial, struct, time, sys
s = serial.Serial("/dev/ttyAMA0", 115200, timeout=0.5)
def send(cmd, p=b""): s.write(b"\xAA" + bytes((cmd,)) + p + b"\xCC\x33\xC3\x3C")
def W(*v): return struct.pack(">" + "H"*len(v), *v)
SLOT = int(sys.argv[1])
s.reset_input_buffer(); send(0x00); time.sleep(0.2); print("handshake:", s.read(64).hex(" "))
send(0x30, b"\xFF"); send(0x01, W(0x07E0)); send(0x3D); time.sleep(1.5)
send(0x25, bytes((1, SLOT))); time.sleep(0.3)
t0 = time.time(); send(0x26, W(0, 0, 271, 239, 0, 0)); send(0x3D); print("copied top half")
