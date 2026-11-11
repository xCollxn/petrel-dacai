import serial, time
s = serial.Serial("/dev/ttyAMA0", 115200, timeout=0.5)
def tx(b, label):
    s.reset_input_buffer(); s.write(b); time.sleep(0.4)
    print(f"{label:28s} -> {s.read(128).hex(' ') or '-'}")
tx(bytes.fromhex("AA00CC33C33C"), "DWIN handshake (before)")
tx(bytes.fromhex("EE04FFFCFFFF"), "Dacai handshake EE 04")
tx(bytes.fromhex("EE04FFFCFFFF"), "Dacai handshake again")
tx(bytes.fromhex("AA00CC33C33C"), "DWIN handshake (after)")
