import serial, struct, time, sys
s = serial.Serial("/dev/ttyAMA0", 115200, timeout=0.5)
def send(cmd, p=b""): s.write(b"\xAA" + bytes((cmd,)) + p + b"\xCC\x33\xC3\x3C")
s.reset_input_buffer(); send(0x00); time.sleep(0.3); print("handshake:", s.read(64).hex(" "))
send(0x30, b"\xFF"); send(0x22, bytes((0, int(sys.argv[1])))); send(0x3D); time.sleep(0.5); print("rx:", s.read(64).hex(" ") or "-")
