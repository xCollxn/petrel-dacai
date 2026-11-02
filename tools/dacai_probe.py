#!/usr/bin/env python3
"""Probe the stock Creality screen on the Pi UART: DWIN or DACAI?

Stop Petrel (or any other display service) first - only one program may own the UART.

    python3 dacai_probe.py [--port /dev/ttyAMA0] [--draw-test]

Checks (all non-destructive):
  1. Handshake  AA 00 ... -> expect AA 00 4F 4B CC 33 C3 3C ("OK") at 115200 baud
  2. SRAM write of 4 bytes at 0x7FF0 -> DACAI answers with an unframed "5A 4F 4B",
     a real DWIN T5UIC1 sends no acknowledgement for SRAM writes
  3. --draw-test: draws four coloured rectangles and sends 0x3D (update). DACAI only
     shows drawing commands after 0x3D.
"""
import argparse
import os
import select
import struct
import termios
import time

TAIL = bytes.fromhex("CC33C33C")


def open_port(path):
    fd = os.open(path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    a = termios.tcgetattr(fd)
    a[0] = a[1] = a[3] = 0
    a[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
    a[4] = a[5] = termios.B115200
    termios.tcsetattr(fd, termios.TCSANOW, a)
    termios.tcflush(fd, termios.TCIOFLUSH)
    return fd


def send(fd, cmd, payload=b""):
    os.write(fd, b"\xAA" + bytes((cmd,)) + payload + TAIL)
    termios.tcdrain(fd)


def read(fd, t=0.4):
    out, end = b"", time.time() + t
    while time.time() < end:
        if select.select([fd], [], [], 0.05)[0]:
            out += os.read(fd, 512)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="/dev/ttyAMA0")
    ap.add_argument("--draw-test", action="store_true")
    a = ap.parse_args()
    fd = open_port(a.port)

    send(fd, 0x00)
    hs = read(fd)
    print("1. handshake:", hs.hex(" ") or "no answer")
    if hs != bytes.fromhex("AA004F4BCC33C33C"):
        print("   -> no T5UIC1 answer. Check wiring (display TX -> Pi RX GPIO15, display RX -> Pi TX GPIO14;"
              " labels like DIN/DOUT may be from the mainboard's point of view), 5 V/GND, and that the"
              " UART is enabled (dtparam=uart0=on on a Pi 5).")
        return
    send(fd, 0x31, b"\x5A" + struct.pack(">H", 0x7FF0) + b"\x00\x00\x00\x00")
    ack = read(fd)
    print("2. SRAM write ack:", ack.hex(" ") or "none")
    if ack.startswith(b"\x5AOK"):
        print("   -> DACAI panel (unframed acknowledgements). This project applies.")
    elif not ack:
        print("   -> behaves like a genuine DWIN T5UIC1. Use plain Petrel instead.")
    else:
        print("   -> unknown answer, please report it.")
    if a.draw_test:
        for i, color in enumerate((0xF800, 0x07E0, 0x001F, 0xFFE0)):
            x = 36 + i * 52
            send(fd, 0x05, b"\x01" + struct.pack(">HHHHH", color, x, 200, x + 44, 244))
        send(fd, 0x3D)
        print("3. drew red/green/blue/yellow squares in the middle - visible?")
    os.close(fd)


if __name__ == "__main__":
    main()
