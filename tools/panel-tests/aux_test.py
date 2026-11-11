import serial, struct, time, sys
s = serial.Serial("/dev/ttyAMA0", 115200, timeout=0.05)
def send(cmd, p=b""):
    s.write(b"\xAA" + bytes((cmd,)) + p + b"\xCC\x33\xC3\x3C")
s.reset_input_buffer()
send(0x00); time.sleep(0.2); print("handshake:", s.read(64).hex(" "))
send(0x38, struct.pack(">H", 136)); time.sleep(0.3); print("0x38 reply:", s.read(64).hex(" ") or "-")
send(0x39, b"U" * 8); time.sleep(0.3); print("0x39 reply:", s.read(64).hex(" ") or "-")
rx = bytearray(); end = time.time() + 20
while time.time() < end:
    send(0x39, b"\x00" * 200)   # long low periods -> visible voltage change
    time.sleep(0.02)
    rx += s.read(256)
print("rx during 20 s:", len(rx), rx[:64].hex(" "))
